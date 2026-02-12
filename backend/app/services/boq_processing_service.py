"""
BOQ Processing Service - Implement new processing flow:

Upload BOQ mới
    ↓
Extract tất cả công tác (1000 items)
    ↓
Lọc trùng tên gốc GIỐNG HỆT (tối ưu)
    ↓
Chuẩn hóa toàn bộ
    ↓
So khớp với Master
    ├─ Exact match (≥95%) → Gán mã có sẵn
    ├─ Fuzzy match (80-95%) → Review
    └─ No match (<80%) → Công tác mới
    ↓
Lọc trùng trong công tác mới
    ↓
Thêm vào Master với mã mới
"""
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from difflib import SequenceMatcher

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.line_item import LineItem
from app.models.master_work_item import MasterWorkItem
from app.models.pending_master_item import PendingMasterItem
from app.models.project_work_item import ProjectWorkItem
from app.models.quarantine_log import QuarantineLog
from app.services.normalization_orchestrator import get_normalization_orchestrator
from app.services.work_code_generator import WorkCodeGenerator
from app.services.master_data_gatekeeper import MasterDataGatekeeper, get_gatekeeper
from app.services.spec_extractor import get_spec_extractor
from app.core.config import settings

logger = logging.getLogger(__name__)


# Threshold constants
EXACT_MATCH_THRESHOLD = 0.95  # ≥95% → Tự động gán mã
FUZZY_MATCH_THRESHOLD = 0.80  # 80-95% → Review
# <80% → Công tác mới


@dataclass
class MatchResult:
    """Result of matching a work item against master database"""
    original_description: str
    normalized_description: str
    match_type: str  # 'exact', 'fuzzy', 'new'
    similarity_score: float
    master_item: Optional[MasterWorkItem] = None
    master_work_code: Optional[str] = None
    needs_review: bool = False
    suggested_matches: List[Dict] = field(default_factory=list)


@dataclass
class ProcessingResult:
    """Result of processing a BOQ file"""
    total_extracted: int
    unique_raw: int  # After raw dedup
    unique_normalized: int  # After normalization dedup
    exact_matches: int
    fuzzy_matches: int
    new_items: int
    items: List[MatchResult] = field(default_factory=list)
    new_items_deduped: int = 0  # New items after internal dedup
    # Gatekeeper validation results
    gatekeeper_approved: int = 0
    gatekeeper_pending: int = 0
    gatekeeper_rejected: int = 0


class BOQProcessingService:
    """
    Service xử lý BOQ theo flow mới với fuzzy matching
    """

    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = get_normalization_orchestrator()
        self.code_generator = WorkCodeGenerator(db)
        self.gatekeeper = get_gatekeeper()
        self.spec_extractor = get_spec_extractor()

        # Initialize hybrid matcher if enabled
        self._hybrid_matcher = None
        if settings.HYBRID_MATCHER_ENABLED:
            try:
                from app.services.hybrid_matcher import get_hybrid_matcher
                self._hybrid_matcher = get_hybrid_matcher(db)
            except Exception as e:
                logger.warning(f"Failed to initialize hybrid matcher: {e}. Falling back to legacy matching.")

    def process_boq_items(
        self,
        file_id: int,
        items: List[Dict],
        auto_add_to_master: bool = False,
        processing_method: str = "3_tier"
    ) -> ProcessingResult:
        """
        Xử lý danh sách công tác từ BOQ file

        Args:
            file_id: ID của BOQ file
            items: List of dicts with 'description', 'unit', 'quantity', 'unit_price'
            auto_add_to_master: Tự động thêm công tác mới vào master
            processing_method: "3_tier" (hybrid), "ai_only" (100% AI semantic), or "cost_funnel" (5-stage cascade)

        Returns:
            ProcessingResult với thống kê và chi tiết
        """
        logger.info(f"Processing {len(items)} items from file {file_id} (method={processing_method})")

        # Cost funnel pipeline — separate flow
        if processing_method == "cost_funnel":
            return self._process_with_cost_funnel(file_id, items)

        # Step 1: Extract descriptions
        descriptions = [item.get('description', '') for item in items if item.get('description')]
        total_extracted = len(descriptions)
        logger.info(f"Step 1: Extracted {total_extracted} descriptions")

        # Step 2: Dedupe raw (tên gốc giống hệt)
        unique_raw = self._dedupe_raw(descriptions)
        logger.info(f"Step 2: Deduped raw: {total_extracted} → {len(unique_raw)} unique")

        # Step 3: Normalize all
        normalized_items = self._normalize_all(unique_raw)
        logger.info(f"Step 3: Normalized {len(normalized_items)} items")

        # Step 4: Match against master
        match_results = self._match_with_master(normalized_items, processing_method)

        # Count results
        exact_matches = [r for r in match_results if r.match_type == 'exact']
        fuzzy_matches = [r for r in match_results if r.match_type == 'fuzzy']
        new_items = [r for r in match_results if r.match_type == 'new']

        logger.info(f"Step 4: Matching results - Exact: {len(exact_matches)}, Fuzzy: {len(fuzzy_matches)}, New: {len(new_items)}")

        # Step 4b: Persist match results to line_items table
        self._persist_match_results(file_id, match_results)

        # Step 5: Dedupe new items (by normalized name)
        unique_new_items = self._dedupe_new_items(new_items)
        new_items_deduped = len(unique_new_items)
        logger.info(f"Step 5: Deduped new items: {len(new_items)} → {new_items_deduped}")

        # Step 6: Add to master if requested (with gatekeeper validation)
        gatekeeper_approved = 0
        gatekeeper_pending = 0
        gatekeeper_rejected = 0

        if auto_add_to_master and unique_new_items:
            gk_results = self._add_to_master_with_validation(file_id, unique_new_items)
            gatekeeper_approved = gk_results['approved']
            gatekeeper_pending = gk_results['pending']
            gatekeeper_rejected = gk_results['rejected']
            logger.info(
                f"Step 6: Gatekeeper validation - "
                f"Approved: {gatekeeper_approved}, Pending: {gatekeeper_pending}, Rejected: {gatekeeper_rejected}"
            )

        return ProcessingResult(
            total_extracted=total_extracted,
            unique_raw=len(unique_raw),
            unique_normalized=len(normalized_items),
            exact_matches=len(exact_matches),
            fuzzy_matches=len(fuzzy_matches),
            new_items=len(new_items),
            new_items_deduped=new_items_deduped,
            items=match_results,
            gatekeeper_approved=gatekeeper_approved,
            gatekeeper_pending=gatekeeper_pending,
            gatekeeper_rejected=gatekeeper_rejected
        )

    def _dedupe_raw(self, descriptions: List[str]) -> List[str]:
        """
        Lọc trùng tên gốc GIỐNG HỆT
        Giữ nguyên thứ tự xuất hiện đầu tiên
        """
        seen = set()
        unique = []
        for desc in descriptions:
            desc_stripped = desc.strip()
            if desc_stripped and desc_stripped not in seen:
                seen.add(desc_stripped)
                unique.append(desc_stripped)
        return unique

    def _normalize_all(self, descriptions: List[str]) -> List[Tuple[str, str]]:
        """
        Chuẩn hóa toàn bộ descriptions using NormalizationOrchestrator.

        The orchestrator handles:
        - Abbreviation expansion (BT -> Bê tông)
        - Priority-based normalizer selection (Traffic > MEP > Description)
        - Hybrid detection (earthwork + MEP specs)

        Returns:
            List of (original, normalized) tuples
        """
        normalized = []
        seen_normalized = set()

        for desc in descriptions:
            try:
                # Use orchestrator which handles expansion + normalization
                result = self.orchestrator.normalize(desc)
                norm = result.normalized
                norm_lower = norm.lower().strip()

                # Dedupe by normalized form
                if norm_lower not in seen_normalized:
                    seen_normalized.add(norm_lower)
                    normalized.append((desc, norm))
            except Exception as e:
                logger.warning(f"Failed to normalize '{desc[:50]}...': {e}")
                # Keep original
                desc_lower = desc.lower().strip()
                if desc_lower not in seen_normalized:
                    seen_normalized.add(desc_lower)
                    normalized.append((desc, desc))

        return normalized

    def _match_with_master(self, items: List[Tuple[str, str]], processing_method: str = "3_tier") -> List[MatchResult]:
        """
        So khớp với Master database

        Uses hybrid 3-tier matching or AI-only semantic matching based on processing_method.

        Args:
            items: List of (original, normalized) tuples
            processing_method: "3_tier" (hybrid) or "ai_only" (100% AI semantic)

        Returns:
            List of MatchResult
        """
        # AI-only uses only semantic matching (Tier 2 only from hybrid matcher)
        if processing_method == "ai_only":
            if self._hybrid_matcher is not None:
                return self._match_with_ai_only(items)
            else:
                logger.warning("AI-only matching requested but hybrid matcher not available. Falling back to legacy.")
                return self._match_with_legacy_matcher(items)

        # 3-tier uses hybrid matcher if available (Tier 1 + Tier 2 + Tier 3)
        if self._hybrid_matcher is not None:
            return self._match_with_hybrid_matcher(items)

        # Legacy O(N*M) matching
        return self._match_with_legacy_matcher(items)

    def _match_with_hybrid_matcher(self, items: List[Tuple[str, str]]) -> List[MatchResult]:
        """
        Match using hybrid 3-tier matcher (O(N*log M)).

        Args:
            items: List of (original, normalized) tuples

        Returns:
            List of MatchResult
        """
        results = []

        # Extract normalized descriptions for batch matching
        descriptions = [normalized for _, normalized in items]

        # Batch match with hybrid matcher
        hybrid_results = self._hybrid_matcher.match_batch(descriptions)

        # Convert HybridMatchResult to MatchResult
        for (original, normalized), hybrid_result in zip(items, hybrid_results):
            # Build suggested matches from candidates
            suggested_matches = hybrid_result.candidates if hybrid_result.candidates else []

            # Get master item if matched
            master_item = None
            if hybrid_result.master_id is not None:
                master_item = self.db.query(MasterWorkItem).filter(
                    MasterWorkItem.master_id == hybrid_result.master_id
                ).first()

            results.append(MatchResult(
                original_description=original,
                normalized_description=normalized,
                match_type=hybrid_result.match_type,
                similarity_score=hybrid_result.similarity_score,
                master_item=master_item,
                master_work_code=hybrid_result.work_code,
                needs_review=(hybrid_result.match_type == 'fuzzy'),
                suggested_matches=suggested_matches
            ))

        return results

    def _match_with_ai_only(self, items: List[Tuple[str, str]]) -> List[MatchResult]:
        """
        AI-only matching using semantic embeddings only (skips exact cache and fuzzy refinement).

        This uses 100% AI-based semantic matching via the embedding service and FAISS index.

        Args:
            items: List of (original, normalized) tuples

        Returns:
            List of MatchResult
        """
        results = []

        # Extract normalized descriptions for batch matching
        descriptions = [normalized for _, normalized in items]

        # Use semantic-only matching from hybrid matcher
        hybrid_results = self._hybrid_matcher.match_batch_semantic_only(descriptions)

        # Convert HybridMatchResult to MatchResult
        for (original, normalized), hybrid_result in zip(items, hybrid_results):
            # Build suggested matches from candidates
            suggested_matches = hybrid_result.candidates if hybrid_result.candidates else []

            # Get master item if matched
            master_item = None
            if hybrid_result.master_id is not None:
                master_item = self.db.query(MasterWorkItem).filter(
                    MasterWorkItem.master_id == hybrid_result.master_id
                ).first()

            results.append(MatchResult(
                original_description=original,
                normalized_description=normalized,
                match_type=hybrid_result.match_type,
                similarity_score=hybrid_result.similarity_score,
                master_item=master_item,
                master_work_code=hybrid_result.work_code,
                needs_review=(hybrid_result.match_type == 'fuzzy'),
                suggested_matches=suggested_matches
            ))

        return results

    def _match_with_legacy_matcher(self, items: List[Tuple[str, str]]) -> List[MatchResult]:
        """
        Legacy O(N*M) matching with SequenceMatcher.

        Args:
            items: List of (original, normalized) tuples

        Returns:
            List of MatchResult
        """
        results = []

        # Load all master items for matching
        master_items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).all()

        # Build lookup dict
        master_lookup = {
            m.description_normalized.lower(): m for m in master_items
            if m.description_normalized
        }
        master_descriptions = list(master_lookup.keys())

        for original, normalized in items:
            norm_lower = normalized.lower().strip()

            # Check exact match first
            if norm_lower in master_lookup:
                master = master_lookup[norm_lower]
                results.append(MatchResult(
                    original_description=original,
                    normalized_description=normalized,
                    match_type='exact',
                    similarity_score=1.0,
                    master_item=master,
                    master_work_code=master.work_code,
                    needs_review=False
                ))
                continue

            # Fuzzy match
            best_match, best_score, top_matches = self._find_best_match(
                norm_lower, master_descriptions, master_lookup
            )

            if best_score >= EXACT_MATCH_THRESHOLD:
                # High similarity - treat as exact
                results.append(MatchResult(
                    original_description=original,
                    normalized_description=normalized,
                    match_type='exact',
                    similarity_score=best_score,
                    master_item=best_match,
                    master_work_code=best_match.work_code if best_match else None,
                    needs_review=False
                ))
            elif best_score >= FUZZY_MATCH_THRESHOLD:
                # Fuzzy match - needs review
                results.append(MatchResult(
                    original_description=original,
                    normalized_description=normalized,
                    match_type='fuzzy',
                    similarity_score=best_score,
                    master_item=best_match,
                    master_work_code=best_match.work_code if best_match else None,
                    needs_review=True,
                    suggested_matches=top_matches
                ))
            else:
                # New item
                results.append(MatchResult(
                    original_description=original,
                    normalized_description=normalized,
                    match_type='new',
                    similarity_score=best_score,
                    needs_review=False,
                    suggested_matches=top_matches[:3] if top_matches else []
                ))

        return results

    def _find_best_match(
        self,
        description: str,
        master_descriptions: List[str],
        master_lookup: Dict[str, MasterWorkItem]
    ) -> Tuple[Optional[MasterWorkItem], float, List[Dict]]:
        """
        Tìm best match trong master database

        Returns:
            (best_master_item, best_score, top_3_matches)
        """
        if not master_descriptions:
            return None, 0.0, []

        # Calculate similarity scores
        scores = []
        for master_desc in master_descriptions:
            score = self._calculate_similarity(description, master_desc)
            if score > 0.3:  # Only consider if somewhat similar
                scores.append((master_desc, score))

        if not scores:
            return None, 0.0, []

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Get top matches
        top_matches = []
        for desc, score in scores[:5]:
            master = master_lookup.get(desc)
            if master:
                top_matches.append({
                    'work_code': master.work_code,
                    'description': master.description,
                    'similarity': round(score * 100, 1),
                    'sec_code': master.sec_code
                })

        best_desc, best_score = scores[0]
        best_master = master_lookup.get(best_desc)

        return best_master, best_score, top_matches

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings
        Uses SequenceMatcher with token-based matching
        """
        if not s1 or not s2:
            return 0.0

        # Exact match
        if s1 == s2:
            return 1.0

        # SequenceMatcher ratio
        ratio = SequenceMatcher(None, s1, s2).ratio()

        # Token-based bonus for construction terms
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())

        if tokens1 and tokens2:
            common = tokens1 & tokens2
            token_ratio = len(common) / max(len(tokens1), len(tokens2))
            # Weighted average
            ratio = 0.6 * ratio + 0.4 * token_ratio

        return ratio

    def _dedupe_new_items(self, new_items: List[MatchResult]) -> List[MatchResult]:
        """
        Lọc trùng trong công tác mới (by normalized description)
        """
        seen = set()
        unique = []

        for item in new_items:
            key = item.normalized_description.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique

    def _persist_match_results(self, file_id: int, match_results: List[MatchResult]):
        """
        Persist match results back to line_items table.

        For each match result, find matching line_items by description and update:
        - exact (≥95%): matched_master_id, match_type='exact', similarity, needs_review=False
        - fuzzy (80-95%): matched_master_id, match_type='fuzzy', similarity, needs_review=True
        - none (<80%): match_type='none', needs_review=False
        """
        if not match_results:
            return

        # Build a lookup from original_description to match result
        desc_to_result = {}
        for mr in match_results:
            desc_to_result[mr.original_description.strip()] = mr

        # Load all line items for this file
        line_items = self.db.query(LineItem).filter(
            LineItem.file_id == file_id,
            LineItem.description.isnot(None),
            LineItem.description != '',
        ).all()

        # Classify SEC codes for items that have a match
        sec_codes = {}
        try:
            from app.services.classifier_service import get_classifier
            classifier = get_classifier()
            for mr in match_results:
                desc = mr.normalized_description or mr.original_description
                results = classifier.classify(desc, top_k=1)
                if results and results[0][1] >= 70.0:
                    sec_codes[mr.original_description.strip()] = results[0][0]
        except Exception as e:
            logger.warning(f"ClassifierService unavailable for SEC classification: {e}")

        updated = 0
        for li in line_items:
            desc_key = li.description.strip() if li.description else ''
            mr = desc_to_result.get(desc_key)
            if mr is None:
                continue

            if mr.match_type == 'exact' and mr.similarity_score >= EXACT_MATCH_THRESHOLD:
                li.matched_master_id = mr.master_item.master_id if mr.master_item else None
                li.match_type = 'exact'
                li.match_similarity = round(mr.similarity_score * 100, 2)
                li.needs_review = False
            elif mr.match_type == 'fuzzy' and mr.similarity_score >= FUZZY_MATCH_THRESHOLD:
                li.matched_master_id = mr.master_item.master_id if mr.master_item else None
                li.match_type = 'fuzzy'
                li.match_similarity = round(mr.similarity_score * 100, 2)
                li.needs_review = True
            else:
                li.match_type = 'none'
                li.matched_master_id = None
                li.needs_review = False

            # Set normalized description
            if mr.normalized_description:
                li.normalized_description = mr.normalized_description

            # Set SEC code from classifier
            sec = sec_codes.get(desc_key)
            if sec:
                li.sec_code = sec

            updated += 1

        if updated > 0:
            self.db.flush()
            logger.info(f"Persisted match results for {updated} line items (file_id={file_id})")

    def _add_to_master(self, file_id: int, items: List[MatchResult]):
        """
        Thêm công tác mới vào Master database với mã mới
        (Legacy method - use _add_to_master_with_validation instead)
        """
        for item in items:
            try:
                # Generate work code
                work_code = self.code_generator.generate_work_code(
                    description=item.normalized_description,
                    sec_code=None,  # Will be classified later
                    unit=None
                )

                master_item = MasterWorkItem(
                    work_code=work_code,
                    description=item.normalized_description,
                    description_normalized=item.normalized_description.lower().strip(),
                    sec_code='UNCLASSIFIED',
                    unit_standard='',
                    occurrence_count=1,
                    source_files=json.dumps([file_id]),
                    is_verified=False
                )
                self.db.add(master_item)

            except Exception as e:
                logger.error(f"Failed to add master item '{item.normalized_description[:50]}...': {e}")

        self.db.commit()

    def _add_to_master_with_validation(self, file_id: int, items: List[MatchResult]) -> Dict[str, int]:
        """
        Validate items with gatekeeper before adding to Master database.

        Returns:
            Dict with counts: approved, pending, rejected
        """
        # Validate all items
        validation_results = self.gatekeeper.validate_batch(items)

        counts = {
            'approved': 0,
            'pending': 0,
            'rejected': 0
        }

        # Process APPROVED items → Master DB
        for item, gk_result in validation_results['approved']:
            try:
                self._create_master_item(file_id, item)
                counts['approved'] += 1
            except Exception as e:
                logger.error(f"Failed to add approved item: {e}")

        # Process PENDING items → Staging table
        for item, gk_result in validation_results['pending']:
            try:
                self._create_pending_item(file_id, item, gk_result)
                counts['pending'] += 1
            except Exception as e:
                logger.error(f"Failed to add pending item: {e}")

        # Log REJECTED items → Quarantine
        for item, gk_result in validation_results['rejected']:
            try:
                self._log_quarantine(file_id, item, gk_result)
                counts['rejected'] += 1
            except Exception as e:
                logger.error(f"Failed to log quarantine item: {e}")

        self.db.commit()
        return counts

    def _create_master_item(self, file_id: int, item: MatchResult):
        """Create a new master item from approved MatchResult"""
        # Classify SEC code using ClassifierService
        sec_code = 'UNCLASSIFIED'
        try:
            from app.services.classifier_service import get_classifier
            classifier = get_classifier()
            results = classifier.classify(item.normalized_description, top_k=1)
            if results and results[0][1] >= 70.0:
                sec_code = results[0][0]
        except Exception as e:
            logger.warning(f"ClassifierService unavailable, using UNCLASSIFIED: {e}")

        work_code = self.code_generator.generate_work_code(
            description=item.normalized_description,
            sec_code=sec_code if sec_code != 'UNCLASSIFIED' else None,
            unit=None
        )

        # Extract specs for fast filtering
        desc_normalized = item.normalized_description.lower().strip()
        specs = self.spec_extractor.extract(desc_normalized)

        master_item = MasterWorkItem(
            work_code=work_code,
            description=item.normalized_description,
            description_normalized=desc_normalized,
            sec_code=sec_code,
            unit_standard='',
            occurrence_count=1,
            source_files=json.dumps([file_id]),
            is_verified=False,
            # Separated specs
            spec_category=specs.category,
            spec_material=specs.material,
            spec_grade=specs.grade,
            spec_dimension=specs.dimension,
            matching_key=specs.to_matching_key(),
        )
        self.db.add(master_item)

    def _create_pending_item(self, file_id: int, item: MatchResult, gk_result):
        """Create a pending item for human review"""
        pending_item = PendingMasterItem(
            description=item.normalized_description,
            description_normalized=item.normalized_description.lower().strip(),
            sec_code='UNCLASSIFIED',
            unit_standard='',
            source_file_id=file_id,
            original_description=item.original_description,
            quality_score=gk_result.score,
            quality_reasons=json.dumps(gk_result.reasons),
            quality_indicators=json.dumps(gk_result.indicators),
            status='PENDING'
        )
        self.db.add(pending_item)

    def _log_quarantine(self, file_id: int, item: MatchResult, gk_result):
        """Route rejected item to quarantine (garbage) or project work items (legitimate low-score)."""
        primary_reason = gk_result.reasons[0] if gk_result.reasons else 'Unknown'

        if gk_result.is_forbidden_pattern:
            # Garbage pattern → quarantine
            forbidden_pattern = None
            if 'Forbidden pattern' in primary_reason:
                forbidden_pattern = primary_reason.split(':')[-1].strip() if ':' in primary_reason else primary_reason

            quarantine_log = QuarantineLog(
                description=item.original_description,
                description_normalized=item.normalized_description,
                source_file_id=file_id,
                rejection_reason=primary_reason[:500],
                quality_score=gk_result.score,
                matched_forbidden_pattern=forbidden_pattern[:100] if forbidden_pattern else None,
                quality_indicators=json.dumps(gk_result.indicators) if gk_result.indicators else None
            )
            self.db.add(quarantine_log)
        else:
            # Legitimate low-score → project work item with RED gate
            from app.models.boq_file import BOQFile
            boq = self.db.query(BOQFile).filter(BOQFile.file_id == file_id).first()
            project_id = boq.project_id if boq else 0

            # Generate temp code
            from sqlalchemy import func as sqla_func
            max_seq = self.db.query(sqla_func.count(ProjectWorkItem.pwi_id)).filter(
                ProjectWorkItem.project_id == project_id,
            ).scalar() or 0
            temp_code = f"PRJ.{project_id}-TEMP-{max_seq + 1:03d}"

            pwi = ProjectWorkItem(
                project_id=project_id,
                file_id=file_id,
                original_description=item.original_description,
                normalized_description=item.normalized_description,
                temp_code=temp_code,
                quality_score=gk_result.score,
                gate_status='RED',
                resolution_status='UNRESOLVED',
            )
            self.db.add(pwi)

    def process_line_items(
        self,
        file_id: int,
        auto_add_to_master: bool = False,
        processing_method: str = "3_tier"
    ) -> ProcessingResult:
        """
        Process line items from database (already parsed BOQ file)

        Args:
            file_id: BOQ file ID
            auto_add_to_master: Auto add new items to master
            processing_method: "3_tier" (hybrid) or "ai_only" (100% AI semantic)

        Returns:
            ProcessingResult
        """
        # Get line items from DB
        line_items = self.db.query(LineItem).filter(
            LineItem.file_id == file_id,
            LineItem.description != '',
            LineItem.description.isnot(None)
        ).all()

        items = [
            {
                'description': item.description,
                'unit': item.unit,
                'quantity': item.quantity,
                'unit_price': item.unit_price
            }
            for item in line_items
        ]

        return self.process_boq_items(file_id, items, auto_add_to_master, processing_method)

    def _process_with_cost_funnel(self, file_id: int, items: List[Dict]) -> ProcessingResult:
        """Process items using the 5-stage cost funnel pipeline."""
        from app.services.cost_funnel import get_cost_funnel
        from app.models.boq_file import BOQFile

        # Get project_id from file
        boq = self.db.query(BOQFile).filter(BOQFile.file_id == file_id).first()
        project_id = boq.project_id if boq else 0

        funnel = get_cost_funnel(self.db)
        funnel_result = funnel.process(items, project_id, file_id)

        # Convert funnel results to ProcessingResult
        exact_matches = sum(1 for ir in funnel_result.item_results if ir.gate_status == 'GREEN' and ir.master_id)
        fuzzy_matches = sum(1 for ir in funnel_result.item_results if ir.gate_status == 'YELLOW')
        new_items = sum(1 for ir in funnel_result.item_results if ir.gate_status == 'RED')

        match_results = []
        for ir in funnel_result.item_results:
            match_type = 'new'
            if ir.master_id:
                match_type = 'exact' if ir.similarity_score >= 0.95 else 'fuzzy'

            match_results.append(MatchResult(
                original_description=ir.original_description,
                normalized_description=ir.normalized_description or ir.original_description,
                match_type=match_type,
                similarity_score=ir.similarity_score,
                master_work_code=ir.master_work_code,
                needs_review=(ir.gate_status == 'YELLOW'),
            ))

        self.db.commit()

        return ProcessingResult(
            total_extracted=funnel_result.total_items,
            unique_raw=funnel_result.total_items,
            unique_normalized=funnel_result.total_items,
            exact_matches=exact_matches,
            fuzzy_matches=fuzzy_matches,
            new_items=new_items,
            items=match_results,
            new_items_deduped=new_items,
            gatekeeper_approved=exact_matches,
            gatekeeper_pending=fuzzy_matches,
            gatekeeper_rejected=new_items,
        )

    def get_match_summary(self, result: ProcessingResult) -> Dict:
        """
        Get summary statistics from processing result
        """
        return {
            'total_extracted': result.total_extracted,
            'after_raw_dedup': result.unique_raw,
            'after_normalize_dedup': result.unique_normalized,
            'matches': {
                'exact': result.exact_matches,
                'fuzzy': result.fuzzy_matches,
                'new': result.new_items
            },
            'new_items_deduped': result.new_items_deduped,
            'needs_review': result.fuzzy_matches,
            'ready_to_add': result.new_items_deduped,
            'gatekeeper': {
                'approved': result.gatekeeper_approved,
                'pending': result.gatekeeper_pending,
                'rejected': result.gatekeeper_rejected
            }
        }


def get_boq_processing_service(db: Session) -> BOQProcessingService:
    """Factory function to get BOQ processing service"""
    return BOQProcessingService(db)
