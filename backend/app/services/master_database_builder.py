"""
Master Database Builder — 3-Step Pipeline

Builds/rebuilds the master work items database from multiple BOQ files:

Step 1 — AGGREGATION:
    Scan line_items grouped by (description, unit), count frequency across files.

Step 2 — STANDARDIZATION:
    Normalize all descriptions, cluster similar items (fuzzy ≥0.85),
    elect canonical name per cluster (highest frequency), apply 80/20 Pareto.

Step 3 — CODING & TAGGING:
    Classify SEC codes, extract specs, generate work codes,
    validate via Gatekeeper, persist to master / pending / quarantine.
"""
import json
import logging
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.line_item import LineItem
from app.models.master_synonym import MasterSynonym
from app.models.master_work_item import MasterWorkItem
from app.models.pending_master_item import PendingMasterItem
from app.models.quarantine_log import QuarantineLog
from app.services.master_data_gatekeeper import get_gatekeeper
from app.services.normalization_orchestrator import get_normalization_orchestrator
from app.services.normalization_result import NormalizationResult, WorkCategory
from app.services.spec_extractor import get_spec_extractor
from app.services.work_code_generator import WorkCodeGenerator
from app.services.v4_code_generator import V4CodeGenerator

logger = logging.getLogger(__name__)

# SEC code mapping from WorkCategory
WORK_CATEGORY_TO_SEC = {
    WorkCategory.EARTHWORKS_PILING: 'SEC-01',
    WorkCategory.CONCRETE_REBAR: 'SEC-02',
    WorkCategory.FINISHING: 'SEC-03',
    WorkCategory.STEEL_MEP: 'SEC-04',
    WorkCategory.ROAD_INFRASTRUCTURE: 'SEC-05',
    WorkCategory.LANDSCAPING: 'SEC-05',
    WorkCategory.GENERAL: 'SEC-00',
}


@dataclass
class BuildConfig:
    """Configuration for the master database build process."""
    pareto_threshold: float = 0.80
    clustering_threshold: float = 0.85
    min_frequency: int = 1
    auto_approve: bool = False
    clear_existing: bool = False
    batch_size: int = 500
    include_only_pareto: bool = False


@dataclass
class AggregatedItem:
    """Step 1 output — a unique (description, unit) pair with frequency."""
    raw_descriptions: List[str]
    unit: Optional[str]
    frequency: int
    source_file_ids: List[int]
    representative_description: str


@dataclass
class StandardizedItem:
    """Step 2 output — a canonical item with synonyms and normalization result."""
    canonical_description: str
    canonical_unit: Optional[str]
    total_frequency: int
    synonym_variants: List[str]
    normalization_result: Optional[NormalizationResult] = None
    is_pareto_top: bool = False
    cluster_id: int = 0
    source_file_ids: List[int] = field(default_factory=list)


@dataclass
class StepStats:
    """Statistics for a single step."""
    input_count: int = 0
    output_count: int = 0
    duration_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MasterBuildResult:
    """Overall result from the 3-step build process."""
    step1_stats: StepStats = field(default_factory=StepStats)
    step2_stats: StepStats = field(default_factory=StepStats)
    step3_stats: StepStats = field(default_factory=StepStats)
    total_master_added: int = 0
    total_pending: int = 0
    total_quarantined: int = 0
    total_updated: int = 0
    total_synonyms_added: int = 0


class MasterDatabaseBuilder:
    """
    Builds/rebuilds the master work items database from multiple BOQ files.

    Composes existing services:
    - NormalizationOrchestrator for description normalization
    - SpecExtractor for structured specification extraction
    - WorkCodeGenerator for work code generation
    - MasterDataGatekeeper for quality validation
    """

    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = get_normalization_orchestrator()
        self.spec_extractor = get_spec_extractor()
        self.gatekeeper = get_gatekeeper()
        self.code_generator = WorkCodeGenerator(db)
        self.v4_code_generator = V4CodeGenerator()
        self._classifier = None

    def _get_classifier(self):
        """Lazy-load ClassifierService."""
        if not hasattr(self, '_classifier'):
            self._classifier = None
        if self._classifier is None:
            try:
                from app.services.classifier_service import get_classifier
                self._classifier = get_classifier(self.db)
            except Exception as e:
                logger.warning(f"Failed to initialize ClassifierService: {e}")
        return self._classifier

    def build(
        self,
        file_ids: List[int],
        config: Optional[BuildConfig] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> MasterBuildResult:
        """
        Execute the full 3-step master database build pipeline.

        Args:
            file_ids: List of BOQ file IDs to process.
            config: Build configuration. Uses defaults if None.
            progress_callback: Optional callback(step_name, current, total).

        Returns:
            MasterBuildResult with per-step stats.
        """
        if config is None:
            config = BuildConfig()

        result = MasterBuildResult()

        if config.clear_existing:
            self._clear_existing_master()

        # Step 1: Aggregation
        if progress_callback:
            progress_callback("aggregation", 0, 3)

        aggregated = self.step1_aggregate(file_ids, config.min_frequency)
        result.step1_stats = StepStats(
            input_count=len(file_ids),
            output_count=len(aggregated),
            details={
                'total_line_items_scanned': sum(a.frequency for a in aggregated),
                'unique_descriptions': len(aggregated),
            }
        )

        if not aggregated:
            return result

        # Step 2: Standardization
        if progress_callback:
            progress_callback("standardization", 1, 3)

        standardized = self.step2_standardize(
            aggregated, config.pareto_threshold, config.clustering_threshold
        )
        pareto_count = sum(1 for s in standardized if s.is_pareto_top)
        result.step2_stats = StepStats(
            input_count=len(aggregated),
            output_count=len(standardized),
            details={
                'clusters_formed': len(set(s.cluster_id for s in standardized)),
                'pareto_top_count': pareto_count,
                'below_pareto_count': len(standardized) - pareto_count,
                'total_synonyms': sum(len(s.synonym_variants) for s in standardized),
            }
        )

        # Step 3: Coding & Tagging
        if progress_callback:
            progress_callback("coding_tagging", 2, 3)

        items_to_process = standardized
        if config.include_only_pareto:
            items_to_process = [s for s in standardized if s.is_pareto_top]

        step3_result = self.step3_code_and_tag(items_to_process, config)
        result.step3_stats = step3_result.step3_stats
        result.total_master_added = step3_result.total_master_added
        result.total_pending = step3_result.total_pending
        result.total_quarantined = step3_result.total_quarantined
        result.total_updated = step3_result.total_updated
        result.total_synonyms_added = step3_result.total_synonyms_added

        if progress_callback:
            progress_callback("done", 3, 3)

        return result

    # ------------------------------------------------------------------
    # Step 1: Aggregation
    # ------------------------------------------------------------------

    def step1_aggregate(
        self,
        file_ids: List[int],
        min_frequency: int = 1,
    ) -> List[AggregatedItem]:
        """
        Scan line_items table grouped by (description, unit), count frequency.

        Args:
            file_ids: File IDs to scan.
            min_frequency: Minimum frequency threshold.

        Returns:
            List of AggregatedItem sorted by frequency descending.
        """
        if not file_ids:
            return []

        rows = (
            self.db.query(
                LineItem.description,
                LineItem.unit,
                func.count(func.distinct(LineItem.file_id)).label('file_count'),
                func.count(LineItem.line_item_id).label('total_count'),
                func.group_concat(func.distinct(LineItem.file_id)).label('file_ids_str'),
            )
            .filter(
                LineItem.file_id.in_(file_ids),
                LineItem.description.isnot(None),
                LineItem.description != '',
            )
            .group_by(LineItem.description, LineItem.unit)
            .having(func.count(LineItem.line_item_id) >= min_frequency)
            .order_by(func.count(LineItem.line_item_id).desc())
            .all()
        )

        aggregated = []
        for row in rows:
            file_ids_list = self._parse_file_ids(row.file_ids_str)
            aggregated.append(AggregatedItem(
                raw_descriptions=[row.description],
                unit=row.unit,
                frequency=row.total_count,
                source_file_ids=file_ids_list,
                representative_description=row.description,
            ))

        return aggregated

    # ------------------------------------------------------------------
    # Step 2: Standardization
    # ------------------------------------------------------------------

    def step2_standardize(
        self,
        aggregated_items: List[AggregatedItem],
        pareto_threshold: float = 0.80,
        clustering_threshold: float = 0.85,
    ) -> List[StandardizedItem]:
        """
        Normalize, cluster, elect canonical, and apply Pareto filter.

        Args:
            aggregated_items: Output from step 1.
            pareto_threshold: Cumulative frequency threshold for Pareto (0-1).
            clustering_threshold: Fuzzy similarity threshold for clustering.

        Returns:
            List of StandardizedItem with canonical names and synonyms.
        """
        if not aggregated_items:
            return []

        # Normalize all descriptions
        descriptions = [item.representative_description for item in aggregated_items]
        norm_results = self.orchestrator.normalize_batch(descriptions)

        # Build items with normalized descriptions
        items_with_norm = list(zip(aggregated_items, norm_results))

        # Cluster similar normalized descriptions
        clusters = self._cluster_descriptions(items_with_norm, clustering_threshold)

        # Elect canonical per cluster and build StandardizedItems
        standardized = []
        for cluster_id, cluster_members in enumerate(clusters):
            item = self._elect_canonical(cluster_members, cluster_id)
            standardized.append(item)

        # Sort by frequency for Pareto
        standardized.sort(key=lambda s: s.total_frequency, reverse=True)

        # Apply Pareto filter
        self._apply_pareto(standardized, pareto_threshold)

        return standardized

    # ------------------------------------------------------------------
    # Step 3: Coding & Tagging
    # ------------------------------------------------------------------

    def step3_code_and_tag(
        self,
        standardized_items: List[StandardizedItem],
        config: Optional[BuildConfig] = None,
    ) -> MasterBuildResult:
        """
        Classify, extract specs, generate codes, validate, and persist.

        Args:
            standardized_items: Output from step 2.
            config: Build configuration.

        Returns:
            MasterBuildResult with step3 stats populated.
        """
        if config is None:
            config = BuildConfig()

        result = MasterBuildResult()
        stats = {
            'approved': 0,
            'pending': 0,
            'rejected': 0,
            'updated': 0,
            'synonyms_added': 0,
            'by_sec_code': defaultdict(int),
        }

        for item in standardized_items:
            try:
                nested = self.db.begin_nested()
                self._process_standardized_item(item, config, stats)
                nested.commit()
            except Exception as e:
                logger.error(
                    f"Error processing item '{item.canonical_description}': {e}"
                )
                try:
                    nested.rollback()
                except Exception:
                    pass
                continue

        self.db.commit()

        # Link master items back to source line_items
        self._link_master_to_line_items(standardized_items)

        result.step3_stats = StepStats(
            input_count=len(standardized_items),
            output_count=stats['approved'] + stats['pending'] + stats['rejected'],
            details={
                'approved': stats['approved'],
                'pending': stats['pending'],
                'rejected': stats['rejected'],
                'updated': stats['updated'],
                'by_sec_code': dict(stats['by_sec_code']),
            }
        )
        result.total_master_added = stats['approved']
        result.total_pending = stats['pending']
        result.total_quarantined = stats['rejected']
        result.total_updated = stats['updated']
        result.total_synonyms_added = stats['synonyms_added']

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_standardized_item(
        self,
        item: StandardizedItem,
        config: BuildConfig,
        stats: Dict[str, Any],
    ) -> None:
        """Process a single standardized item through coding, validation, and persistence."""
        norm_result = item.normalization_result
        if norm_result is None:
            norm_result = self.orchestrator.normalize(item.canonical_description)

        # Derive SEC code: prefer ClassifierService, then rule-based MEP, fallback to work category mapping
        sec_code = None
        classifier = self._get_classifier()
        if classifier:
            try:
                desc_for_classify = norm_result.normalized or item.canonical_description
                classify_results = classifier.classify(desc_for_classify, top_k=1)
                if classify_results and classify_results[0][1] >= 70.0:
                    sec_code = classify_results[0][0]
            except Exception as e:
                logger.warning(f"ClassifierService failed, falling back to mapping: {e}")

        # Rule-based MEP sub-classification (runs after ML, before WorkCategory fallback)
        if not sec_code or sec_code == 'SEC-00' or sec_code == 'SEC-04':
            desc_for_rules = norm_result.normalized or item.canonical_description
            rule_sec = self._classify_sec_by_rules(desc_for_rules)
            if rule_sec:
                sec_code = rule_sec

        if not sec_code:
            sec_code = WORK_CATEGORY_TO_SEC.get(
                norm_result.work_category, 'SEC-00'
            )

        # Normalize for indexing
        desc_normalized = self._normalize_for_index(item.canonical_description)
        desc_display = norm_result.normalized or item.canonical_description

        # Check if similar item already exists in master
        existing = self._find_existing_master(desc_normalized, sec_code, item.canonical_unit)
        if existing:
            self._update_existing_master(existing, item)
            stats['updated'] += 1
            # Still add synonyms for the existing item
            self._persist_synonyms(existing.master_id, item.synonym_variants)
            stats['synonyms_added'] += len(item.synonym_variants)
            return

        # Extract specs
        specs = self.spec_extractor.extract(desc_normalized)

        # Validate with gatekeeper
        gk_result = self.gatekeeper.validate({
            'normalized_description': desc_normalized,
            'description': desc_display,
        })

        stats['by_sec_code'][sec_code] += 1

        if gk_result.status == 'APPROVED' or (config.auto_approve and gk_result.status == 'PENDING_REVIEW'):
            # Generate work code
            work_code = self.code_generator.generate_work_code(
                description=desc_display,
                sec_code=sec_code,
                unit=item.canonical_unit,
            )

            # Detect item table type from description
            detected_type = self._detect_item_type(desc_display)

            # Generate v4.0 code
            spec_dict = {
                'category': specs.category,
                'material': specs.material,
                'grade': specs.grade,
                'dimension': specs.dimension,
            }
            v4_code, v4_discipline, v4_location = self.v4_code_generator.generate(
                description=desc_display,
                sec_code=sec_code,
                specs=spec_dict,
                table_type=detected_type,
            )

            # Generate unique instance code
            instance_code = self.v4_code_generator.generate_instance_code(
                ref_code=v4_code,
                db=self.db,
            )

            # Resolve type-specific attributes from specs
            v4_material_type = None
            v4_worker_grade = None
            v4_equip_type = None
            if detected_type == 'M':
                v4_material_type = spec_dict.get('material') or None
            elif detected_type == 'L':
                v4_worker_grade = spec_dict.get('grade') or None
            elif detected_type == 'E':
                v4_equip_type = spec_dict.get('category') or None

            master_item = MasterWorkItem(
                work_code=work_code,
                description=desc_display,
                description_normalized=desc_normalized,
                sec_code=sec_code,
                unit_standard=item.canonical_unit or 'N/A',
                occurrence_count=item.total_frequency,
                source_files=json.dumps(item.source_file_ids),
                is_verified=False,
                spec_category=specs.category,
                spec_material=specs.material,
                spec_grade=specs.grade,
                spec_dimension=specs.dimension,
                matching_key=specs.to_matching_key(),
                # Spec lifecycle fields
                spec_status=gk_result.suggested_spec_status,
                spec_source=gk_result.suggested_spec_source,
                spec_confidence=gk_result.suggested_spec_confidence,
                # v4.0 codes
                sec_code_v4=v4_code,
                instance_code=instance_code,
                item_table_type=detected_type,
                # v4.0 attributes (stored separately, not in the code)
                discipline=v4_discipline,
                location=v4_location,
                material_type=v4_material_type,
                worker_grade=v4_worker_grade,
                equip_type=v4_equip_type,
            )
            # Compute spec completeness
            master_item.spec_completeness = master_item.compute_spec_completeness()

            self.db.add(master_item)
            self.db.flush()  # Get master_id for synonyms

            # Persist synonyms
            self._persist_synonyms(master_item.master_id, item.synonym_variants)
            stats['synonyms_added'] += len(item.synonym_variants)
            stats['approved'] += 1

        elif gk_result.status == 'PENDING_REVIEW':
            pending = PendingMasterItem(
                description=desc_display,
                description_normalized=desc_normalized,
                sec_code=sec_code,
                unit_standard=item.canonical_unit or 'N/A',
                original_description=item.canonical_description,
                quality_score=gk_result.score,
                quality_reasons=json.dumps(gk_result.reasons),
                quality_indicators=json.dumps(gk_result.indicators),
                status='PENDING',
            )
            self.db.add(pending)
            stats['pending'] += 1

        else:
            # Rejected
            primary_reason = gk_result.reasons[0] if gk_result.reasons else 'Unknown'
            quarantine = QuarantineLog(
                description=item.canonical_description,
                description_normalized=desc_normalized,
                rejection_reason=primary_reason[:500],
                quality_score=gk_result.score,
                quality_indicators=json.dumps(gk_result.indicators) if gk_result.indicators else None,
            )
            self.db.add(quarantine)
            stats['rejected'] += 1

    def _link_master_to_line_items(
        self,
        standardized_items: List[StandardizedItem],
    ) -> None:
        """
        Back-link master items to their source line_items.

        After step3 creates master items, iterate through standardized_items,
        find the corresponding master item, and update all source line_items
        with matched_master_id, match_type='exact', match_similarity=1.0.

        Only updates line_items that don't already have a matched_master_id.
        """
        for item in standardized_items:
            # Find the master item by normalized description
            desc_normalized = self._normalize_for_index(item.canonical_description)
            master = self.db.query(MasterWorkItem).filter(
                MasterWorkItem.description_normalized == desc_normalized,
                MasterWorkItem.is_active == True,
            ).first()

            if not master:
                continue

            # All descriptions in the cluster (canonical + synonyms)
            all_descriptions = [item.canonical_description] + item.synonym_variants
            all_normalized = [self._normalize_for_index(d) for d in all_descriptions]

            # Update source line items that don't already have a match
            for file_id in item.source_file_ids:
                for norm_desc in all_normalized:
                    line_items = self.db.query(LineItem).filter(
                        LineItem.file_id == file_id,
                        LineItem.normalized_description == norm_desc,
                        LineItem.matched_master_id.is_(None),
                    ).all()

                    for li in line_items:
                        li.matched_master_id = master.master_id
                        li.match_type = 'exact'
                        li.match_similarity = 100.0
                        li.needs_review = False

        self.db.flush()

    # ── Item Type Detection ──

    # Keywords that indicate Material items (M)
    _MATERIAL_KEYWORDS = [
        r'\bvật\s*liệu\b', r'\bvật\s*tư\b',
        r'\bcung\s*cấp\b', r'\bmua\b',
        r'\bthép\s+hình\b', r'\bthép\s+tấm\b',
        r'\bcát\b', r'\bđá\b', r'\bxi\s*măng\b',
        r'\bsơn\b(?!\s+\w*tường)', r'\bgạch\s+ốp\b', r'\bgạch\s+lát\b',
        r'\bống\s+(hdpe|pvc|upvc|ppr|thép|gang|inox)\b',
        r'\bcáp\s+(cu|nhôm|điện)\b', r'\bdây\s+điện\b',
        r'\bvan\s+(cổng|bướm|bi|cầu|một\s+chiều)\b',
        r'\bbê\s*tông\s+thương\s+phẩm\b',
        r'\bvữa\s+(xây|trát|lót)\b',
    ]

    # Keywords that indicate Labour items (L)
    _LABOUR_KEYWORDS = [
        r'\bnhân\s*công\b', r'\bthợ\b', r'\bcông\s+nhân\b',
        r'\bbậc\s*\d\b', r'\blao\s+động\b',
        r'\bngày\s+công\b', r'\bca\s+thợ\b',
    ]

    # Keywords that indicate Equipment items (E)
    _EQUIPMENT_KEYWORDS = [
        r'\bmáy\s+(đào|xúc|trộn|bơm|khoan|ép|lu|cắt|hàn|cẩu|phát)\b',
        r'\bcần\s+trục\b', r'\bcẩu\b',
        r'\bxe\s+(tải|ben|bồn|cứu\s+hỏa)\b',
        r'\bca\s+máy\b',
        r'\bthiết\s+bị\s+thi\s+công\b',
        r'\bđầm\s+(dùi|bàn|cóc)\b',
    ]

    def _detect_item_type(self, description: str) -> str:
        """
        Detect item table type from description keywords.

        Returns: 'A' (Activity), 'M' (Material), 'L' (Labour), 'E' (Equipment)
        Default is 'A' if no specific pattern matches.
        """
        desc_lower = description.lower()

        for pattern in self._MATERIAL_KEYWORDS:
            if re.search(pattern, desc_lower):
                return 'M'

        for pattern in self._LABOUR_KEYWORDS:
            if re.search(pattern, desc_lower):
                return 'L'

        for pattern in self._EQUIPMENT_KEYWORDS:
            if re.search(pattern, desc_lower):
                return 'E'

        return 'A'

    def _cluster_descriptions(
        self,
        items_with_norm: List[Tuple[AggregatedItem, NormalizationResult]],
        threshold: float,
    ) -> List[List[Tuple[AggregatedItem, NormalizationResult]]]:
        """
        Group similar normalized descriptions using Union-Find with pairwise
        fuzzy matching (RapidFuzz).

        For datasets >5000, falls back to a simpler exact-normalized grouping
        to avoid O(n^2) explosion.
        """
        n = len(items_with_norm)
        if n == 0:
            return []

        # Get normalized descriptions for comparison
        norm_descs = [
            self._normalize_for_index(nr.normalized)
            for _, nr in items_with_norm
        ]

        # Union-Find parent array
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        if n <= 5000:
            # Pairwise fuzzy comparison with RapidFuzz
            try:
                from rapidfuzz import fuzz
                for i in range(n):
                    for j in range(i + 1, n):
                        # Items must have same unit to be clustered
                        if items_with_norm[i][0].unit != items_with_norm[j][0].unit:
                            continue
                        score = fuzz.ratio(norm_descs[i], norm_descs[j]) / 100.0
                        if score >= threshold:
                            union(i, j)
            except ImportError:
                # Fallback: use difflib SequenceMatcher
                from difflib import SequenceMatcher
                for i in range(n):
                    for j in range(i + 1, n):
                        if items_with_norm[i][0].unit != items_with_norm[j][0].unit:
                            continue
                        score = SequenceMatcher(None, norm_descs[i], norm_descs[j]).ratio()
                        if score >= threshold:
                            union(i, j)
        else:
            # Large dataset: group by exact normalized description + unit
            seen: Dict[Tuple[str, Optional[str]], int] = {}
            for i in range(n):
                key = (norm_descs[i], items_with_norm[i][0].unit)
                if key in seen:
                    union(i, seen[key])
                else:
                    seen[key] = i

        # Build clusters from Union-Find
        clusters_map: Dict[int, List[int]] = defaultdict(list)
        for i in range(n):
            clusters_map[find(i)].append(i)

        return [
            [items_with_norm[i] for i in indices]
            for indices in clusters_map.values()
        ]

    def _is_degenerate(self, text: str) -> bool:
        """
        Check if a normalized description is degenerate (unusable as canonical).

        Rejects:
        - Too short (< 5 characters)
        - Contains repeated words ("ống ống", "d60 d60")
        - Too generic (single common word)
        """
        if not text or len(text.strip()) < 5:
            return True

        words = text.lower().split()
        if not words:
            return True

        # Check for repeated consecutive words: "ống ống", "d60 d60"
        for i in range(len(words) - 1):
            if words[i] == words[i + 1] and len(words[i]) >= 2:
                return True

        # Check for too generic (single word that is a common filler)
        generic_words = {'đầu', 'ra', 'vào', 'cái', 'bộ', 'hệ', 'loại', 'kiểu'}
        if len(words) == 1 and words[0] in generic_words:
            return True

        # Check if entire description is just repeated tokens
        unique_words = set(words)
        if len(unique_words) == 1 and len(words) > 1:
            return True

        return False

    def _elect_canonical(
        self,
        cluster: List[Tuple[AggregatedItem, NormalizationResult]],
        cluster_id: int,
    ) -> StandardizedItem:
        """
        Pick the best NORMALIZED description as canonical.

        Strategy:
        1. Sort by frequency (desc), then description length (desc)
        2. Use normalized description from the winner
        3. If normalized is degenerate, try other cluster members
        4. If all normalized are degenerate, fall back to raw description
        5. ALL raw descriptions (including the one chosen) become synonyms
        """
        # Sort: highest frequency first, then longest description
        cluster.sort(
            key=lambda x: (x[0].frequency, len(x[0].representative_description)),
            reverse=True,
        )

        # Collect all file IDs and descriptions across cluster
        all_file_ids: Set[int] = set()
        all_raw_descriptions: Set[str] = set()
        total_freq = 0

        for agg, _ in cluster:
            all_file_ids.update(agg.source_file_ids)
            all_raw_descriptions.update(agg.raw_descriptions)
            total_freq += agg.frequency

        # Find best non-degenerate normalized description
        canonical_desc = None
        canonical_norm = cluster[0][1]  # default norm result

        for agg, norm in cluster:
            normalized = norm.normalized
            if normalized and not self._is_degenerate(normalized):
                canonical_desc = normalized
                canonical_norm = norm
                break

        # If all normalized are degenerate, fall back to raw (highest freq)
        if canonical_desc is None:
            canonical_desc = cluster[0][0].representative_description
            canonical_norm = cluster[0][1]
            logger.warning(
                f"All normalized descriptions degenerate in cluster {cluster_id}, "
                f"falling back to raw: '{canonical_desc}'"
            )

        # ALL raw descriptions become synonyms (including the original canonical raw)
        synonym_variants = [
            d for d in all_raw_descriptions if d != canonical_desc
        ]

        return StandardizedItem(
            canonical_description=canonical_desc,
            canonical_unit=cluster[0][0].unit,
            total_frequency=total_freq,
            synonym_variants=synonym_variants,
            normalization_result=canonical_norm,
            cluster_id=cluster_id,
            source_file_ids=sorted(all_file_ids),
        )

    # MEP sub-category rules for rule-based SEC classification
    _MEP_SEC_RULES = {
        'SEC-04-01': [  # Electrical
            r'\bmccb\b', r'\bmcb\b', r'\bcontactor\b', r'\baptomat\b',
            r'\bcầu\s+chì\b', r'\bđèn\s+báo\b', r'\btủ\s+điện\b',
            r'\bthanh\s+cái\b', r'\bcáp\s+cu\b', r'\bxlpe\b',
            r'\bcáp\s+điện\b', r'\bdây\s+điện\b', r'\btủ\s+điều\s+khiển\b',
            r'\bcầu\s+dao\b', r'\brơ\s*le\b', r'\bbiến\s+áp\b',
        ],
        'SEC-04-02': [  # Plumbing
            r'\bống\s+hdpe\b', r'\bống\s+pvc\b', r'\bống\s+upvc\b',
            r'\bống\s+ppr\b', r'\bống\s+thép\b', r'\bống\s+nhựa\b',
            r'\bvan\s+cổng\b', r'\bvan\s+bướm\b', r'\bvan\s+bi\b',
            r'\bvan\s+một\s+chiều\b', r'\bvan\s+cầu\b',
            r'\bcôn\s+thu\b', r'\bcút\b(?!\s+điện)', r'\btê\b(?!\s+bào)',
            r'\bbích\b', r'\bkhớp\s+nối\b',
            r'\bđồng\s+hồ\s+nước\b', r'\bđồng\s+hồ\s+đo\b',
            r'\bbơm\s+nước\b', r'\bbơm\s+chìm\b',
            r'\bống\s+gang\b', r'\bống\s+inox\b',
        ],
        'SEC-04-03': [  # HVAC
            r'\bđiều\s+hòa\b', r'\bthông\s+gió\b', r'\bahu\b', r'\bfcu\b',
            r'\bống\s+gió\b', r'\bdàn\s+lạnh\b', r'\bdàn\s+nóng\b',
            r'\bmáy\s+lạnh\b', r'\bchiller\b', r'\bcooling\b',
        ],
        'SEC-04-04': [  # PCCC (Fire Protection)
            r'\bpccc\b', r'\bbáo\s+cháy\b', r'\bsprinkler\b',
            r'\bbình\s+chữa\s+cháy\b', r'\bchữa\s+cháy\b',
            r'\bđầu\s+phun\b', r'\btủ\s+cứu\s+hỏa\b',
        ],
    }

    def _classify_sec_by_rules(self, description: str) -> Optional[str]:
        """
        Rule-based MEP sub-category classifier.

        Runs AFTER ML classifier, BEFORE WorkCategory fallback.
        Uses word boundary regex to avoid false matches
        (e.g., "van" should not match "ván khuôn").

        Returns:
            SEC sub-code (e.g., 'SEC-04-02') or None if no match.
        """
        desc_lower = description.lower()

        for sec_code, patterns in self._MEP_SEC_RULES.items():
            for pattern in patterns:
                if re.search(pattern, desc_lower):
                    logger.debug(
                        f"SEC rule match: pattern '{pattern}' → {sec_code} "
                        f"for '{description[:50]}'"
                    )
                    return sec_code

        return None

    def _apply_pareto(
        self,
        items: List[StandardizedItem],
        threshold: float,
    ) -> None:
        """
        Mark top items covering threshold% of cumulative frequency.
        Items must be pre-sorted by frequency descending.
        """
        grand_total = sum(s.total_frequency for s in items)
        if grand_total == 0:
            return

        cumulative = 0
        target = grand_total * threshold

        for item in items:
            cumulative += item.total_frequency
            item.is_pareto_top = True
            if cumulative >= target:
                break

    def _find_existing_master(
        self,
        desc_normalized: str,
        sec_code: str,
        unit: Optional[str],
    ) -> Optional[MasterWorkItem]:
        """Check if similar item already exists in master database."""
        query = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.description_normalized == desc_normalized,
            MasterWorkItem.is_active == True,
        )
        if sec_code:
            query = query.filter(MasterWorkItem.sec_code == sec_code)
        if unit:
            query = query.filter(MasterWorkItem.unit_standard == unit)

        return query.first()

    def _update_existing_master(
        self,
        master: MasterWorkItem,
        item: StandardizedItem,
    ) -> None:
        """Update existing master item with new frequency and source info."""
        master.occurrence_count = (master.occurrence_count or 0) + item.total_frequency

        existing_sources = json.loads(master.source_files) if master.source_files else []
        merged = sorted(set(existing_sources + item.source_file_ids))
        master.source_files = json.dumps(merged)

    def _persist_synonyms(
        self,
        master_id: int,
        variants: List[str],
    ) -> None:
        """Persist synonym variants for a master item."""
        for variant in variants:
            normalized = self._normalize_for_index(variant)
            # Check if synonym already exists
            exists = self.db.query(MasterSynonym).filter(
                MasterSynonym.master_id == master_id,
                MasterSynonym.synonym_normalized == normalized,
            ).first()
            if not exists:
                synonym = MasterSynonym(
                    master_id=master_id,
                    synonym_text=variant,
                    synonym_normalized=normalized,
                    synonym_type='alias',
                    is_active=True,
                )
                self.db.add(synonym)

    def _normalize_for_index(self, text: str) -> str:
        """Normalize text for indexing (lowercase, NFC, single spaces)."""
        if not text:
            return ''
        text = unicodedata.normalize('NFC', text)
        text = text.lower()
        text = ' '.join(text.split())
        return text.strip()

    def _clear_existing_master(self) -> None:
        """Clear all existing master data for full rebuild."""
        self.db.query(MasterSynonym).delete()
        self.db.query(PendingMasterItem).delete()
        self.db.query(QuarantineLog).delete()
        self.db.query(MasterWorkItem).delete()
        self.db.flush()

    def _parse_file_ids(self, file_ids_str: Optional[str]) -> List[int]:
        """Parse comma-separated file ID string into list of ints."""
        if not file_ids_str:
            return []
        try:
            return sorted(int(x) for x in str(file_ids_str).split(',') if x.strip())
        except (ValueError, TypeError):
            return []


def get_master_database_builder(db: Session) -> MasterDatabaseBuilder:
    """Factory function for MasterDatabaseBuilder."""
    return MasterDatabaseBuilder(db)
