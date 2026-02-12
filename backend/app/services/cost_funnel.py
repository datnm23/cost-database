"""
Cost Funnel Pipeline — 5-Stage Cascade Matching

Each stage short-circuits on hit:
1. Synonym lookup (O(1) in-memory cache from master_synonyms)
2. Exact match (Redis hash or in-memory dict)
3. Semantic match (FAISS top-K, threshold >= 0.90)
4. LLM Structured Output (only for misses — batch of 10)
5. Code generation + Gatekeeper validation → route GREEN/YELLOW/RED
"""
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.master_work_item import MasterWorkItem
from app.models.master_synonym import MasterSynonym
from app.models.project_work_item import ProjectWorkItem
from app.services.master_data_gatekeeper import get_gatekeeper

logger = logging.getLogger(__name__)


@dataclass
class FunnelStageResult:
    """Metrics for a single funnel stage."""
    stage_name: str
    items_in: int
    items_resolved: int = 0
    hit_rate: float = 0.0
    duration_ms: float = 0.0


@dataclass
class FunnelItemResult:
    """Result for a single item through the funnel."""
    original_description: str
    normalized_description: Optional[str] = None
    resolved_stage: Optional[str] = None  # Which stage resolved it
    master_id: Optional[int] = None
    master_work_code: Optional[str] = None
    similarity_score: float = 0.0
    gate_status: Optional[str] = None  # GREEN/YELLOW/RED
    quality_score: float = 0.0
    structured_output: Optional[Dict] = None
    temp_code: Optional[str] = None


@dataclass
class FunnelResult:
    """Overall result from the cost funnel pipeline."""
    total_items: int = 0
    stage_results: List[FunnelStageResult] = field(default_factory=list)
    item_results: List[FunnelItemResult] = field(default_factory=list)
    total_resolved: int = 0
    total_unresolved: int = 0
    total_duration_ms: float = 0.0


class CostFunnel:
    """
    5-stage cascade matching pipeline.

    Usage:
        funnel = CostFunnel(db)
        result = funnel.process(descriptions, project_id, file_id)
    """

    def __init__(self, db: Session):
        self.db = db
        self.gatekeeper = get_gatekeeper()
        self._synonym_cache: Optional[Dict[str, int]] = None
        self._exact_cache: Optional[Dict[str, int]] = None
        self._hybrid_matcher = None
        self._ai_normalizer = None

    def process(
        self,
        items: List[Dict],
        project_id: int,
        file_id: int,
        wbs_contexts: Optional[Dict[int, Dict]] = None,
    ) -> FunnelResult:
        """
        Run items through the 5-stage funnel.

        Args:
            items: List of dicts with 'description', optional 'unit', 'quantity', 'unit_price'
            project_id: Project ID for temp code generation
            file_id: File ID for source tracking
            wbs_contexts: Optional dict mapping index -> WBS context dict

        Returns:
            FunnelResult with per-stage metrics and per-item results
        """
        start = time.monotonic()
        descriptions = [item.get('description', '') for item in items]
        n = len(descriptions)

        result = FunnelResult(total_items=n)
        item_results = [
            FunnelItemResult(original_description=desc)
            for desc in descriptions
        ]

        # Track which indices are still unresolved
        unresolved = set(range(n))

        # Stage 1: Synonym lookup
        stage1 = self._stage_synonym_lookup(descriptions, item_results, unresolved)
        result.stage_results.append(stage1)

        # Stage 2: Exact match
        stage2 = self._stage_exact_match(descriptions, item_results, unresolved)
        result.stage_results.append(stage2)

        # Stage 3: Semantic match
        stage3 = self._stage_semantic_match(descriptions, item_results, unresolved)
        result.stage_results.append(stage3)

        # Stage 4: LLM Structured Output
        stage4 = self._stage_llm_structured(descriptions, item_results, unresolved, wbs_contexts)
        result.stage_results.append(stage4)

        # Stage 5: Gatekeeper validation + routing
        stage5 = self._stage_gatekeeper(
            descriptions, items, item_results, unresolved,
            project_id, file_id,
        )
        result.stage_results.append(stage5)

        result.item_results = item_results
        result.total_resolved = n - len(unresolved)
        result.total_unresolved = len(unresolved)
        result.total_duration_ms = (time.monotonic() - start) * 1000

        return result

    # ── Stage 1: Synonym Lookup ──

    def _stage_synonym_lookup(
        self,
        descriptions: List[str],
        item_results: List[FunnelItemResult],
        unresolved: set,
    ) -> FunnelStageResult:
        start = time.monotonic()
        items_in = len(unresolved)
        resolved = 0

        cache = self._get_synonym_cache()

        for i in list(unresolved):
            norm = descriptions[i].lower().strip()
            master_id = cache.get(norm)
            if master_id is not None:
                master = self.db.query(MasterWorkItem).filter(
                    MasterWorkItem.master_id == master_id,
                    MasterWorkItem.is_active == True,
                ).first()
                if master:
                    item_results[i].resolved_stage = 'synonym'
                    item_results[i].master_id = master.master_id
                    item_results[i].master_work_code = master.work_code
                    item_results[i].similarity_score = 1.0
                    item_results[i].gate_status = 'GREEN'
                    item_results[i].quality_score = 100.0
                    unresolved.discard(i)
                    resolved += 1

        duration = (time.monotonic() - start) * 1000
        return FunnelStageResult(
            stage_name='synonym_lookup',
            items_in=items_in,
            items_resolved=resolved,
            hit_rate=resolved / items_in if items_in > 0 else 0.0,
            duration_ms=duration,
        )

    # ── Stage 2: Exact Match ──

    def _stage_exact_match(
        self,
        descriptions: List[str],
        item_results: List[FunnelItemResult],
        unresolved: set,
    ) -> FunnelStageResult:
        start = time.monotonic()
        items_in = len(unresolved)
        resolved = 0

        cache = self._get_exact_cache()

        for i in list(unresolved):
            norm = descriptions[i].lower().strip()
            master_id = cache.get(norm)
            if master_id is not None:
                master = self.db.query(MasterWorkItem).filter(
                    MasterWorkItem.master_id == master_id,
                    MasterWorkItem.is_active == True,
                ).first()
                if master:
                    item_results[i].resolved_stage = 'exact_match'
                    item_results[i].master_id = master.master_id
                    item_results[i].master_work_code = master.work_code
                    item_results[i].similarity_score = 1.0
                    item_results[i].gate_status = 'GREEN'
                    item_results[i].quality_score = 100.0
                    unresolved.discard(i)
                    resolved += 1

        duration = (time.monotonic() - start) * 1000
        return FunnelStageResult(
            stage_name='exact_match',
            items_in=items_in,
            items_resolved=resolved,
            hit_rate=resolved / items_in if items_in > 0 else 0.0,
            duration_ms=duration,
        )

    # ── Stage 3: Semantic Match ──

    def _stage_semantic_match(
        self,
        descriptions: List[str],
        item_results: List[FunnelItemResult],
        unresolved: set,
    ) -> FunnelStageResult:
        start = time.monotonic()
        items_in = len(unresolved)
        resolved = 0

        matcher = self._get_hybrid_matcher()
        if matcher is None:
            duration = (time.monotonic() - start) * 1000
            return FunnelStageResult(
                stage_name='semantic_match',
                items_in=items_in,
                items_resolved=0,
                hit_rate=0.0,
                duration_ms=duration,
            )

        # Batch match unresolved items
        unresolved_descs = [(i, descriptions[i]) for i in sorted(unresolved)]
        if unresolved_descs:
            try:
                batch_results = matcher.match_batch([desc for _, desc in unresolved_descs])
                for (idx, _), hybrid_result in zip(unresolved_descs, batch_results):
                    if (hybrid_result.match_type in ('exact', 'fuzzy')
                            and hybrid_result.similarity_score >= 0.90
                            and hybrid_result.master_id is not None):
                        item_results[idx].resolved_stage = 'semantic_match'
                        item_results[idx].master_id = hybrid_result.master_id
                        item_results[idx].master_work_code = hybrid_result.work_code
                        item_results[idx].similarity_score = hybrid_result.similarity_score
                        item_results[idx].gate_status = 'GREEN'
                        item_results[idx].quality_score = hybrid_result.similarity_score * 100
                        unresolved.discard(idx)
                        resolved += 1
            except Exception as e:
                logger.warning(f"Semantic match failed: {e}")

        duration = (time.monotonic() - start) * 1000
        return FunnelStageResult(
            stage_name='semantic_match',
            items_in=items_in,
            items_resolved=resolved,
            hit_rate=resolved / items_in if items_in > 0 else 0.0,
            duration_ms=duration,
        )

    # ── Stage 4: LLM Structured Output ──

    def _stage_llm_structured(
        self,
        descriptions: List[str],
        item_results: List[FunnelItemResult],
        unresolved: set,
        wbs_contexts: Optional[Dict[int, Dict]] = None,
    ) -> FunnelStageResult:
        start = time.monotonic()
        items_in = len(unresolved)
        resolved = 0

        if not unresolved:
            return FunnelStageResult(
                stage_name='llm_structured',
                items_in=0,
                items_resolved=0,
                duration_ms=0.0,
            )

        normalizer = self._get_ai_normalizer()
        if normalizer is None:
            duration = (time.monotonic() - start) * 1000
            return FunnelStageResult(
                stage_name='llm_structured',
                items_in=items_in,
                items_resolved=0,
                duration_ms=duration,
            )

        # Get unresolved descriptions
        unresolved_indices = sorted(unresolved)
        unresolved_descs = [descriptions[i] for i in unresolved_indices]

        # Build WBS contexts for unresolved items
        wbs_for_batch = None
        if wbs_contexts:
            wbs_for_batch = {}
            for j, idx in enumerate(unresolved_indices):
                if idx in wbs_contexts:
                    wbs_for_batch[j] = wbs_contexts[idx]

        try:
            structured_results = normalizer.normalize_structured_batch(
                unresolved_descs,
                wbs_contexts=wbs_for_batch,
                batch_size=10,
            )

            for j, (idx, sr) in enumerate(zip(unresolved_indices, structured_results)):
                if sr is not None:
                    item_results[idx].structured_output = sr.model_dump()
                    item_results[idx].normalized_description = sr.normalized_description

                    # High confidence structured output can resolve via exact match
                    if sr.confidence >= 0.90:
                        norm_desc = sr.normalized_description.lower().strip()
                        exact_cache = self._get_exact_cache()
                        master_id = exact_cache.get(norm_desc)
                        if master_id is not None:
                            master = self.db.query(MasterWorkItem).filter(
                                MasterWorkItem.master_id == master_id,
                                MasterWorkItem.is_active == True,
                            ).first()
                            if master:
                                item_results[idx].resolved_stage = 'llm_structured'
                                item_results[idx].master_id = master.master_id
                                item_results[idx].master_work_code = master.work_code
                                item_results[idx].similarity_score = sr.confidence
                                item_results[idx].gate_status = 'GREEN'
                                item_results[idx].quality_score = sr.confidence * 100
                                unresolved.discard(idx)
                                resolved += 1

        except Exception as e:
            logger.warning(f"LLM structured output failed: {e}")

        duration = (time.monotonic() - start) * 1000
        return FunnelStageResult(
            stage_name='llm_structured',
            items_in=items_in,
            items_resolved=resolved,
            hit_rate=resolved / items_in if items_in > 0 else 0.0,
            duration_ms=duration,
        )

    # ── Stage 5: Gatekeeper Validation ──

    def _stage_gatekeeper(
        self,
        descriptions: List[str],
        original_items: List[Dict],
        item_results: List[FunnelItemResult],
        unresolved: set,
        project_id: int,
        file_id: int,
    ) -> FunnelStageResult:
        start = time.monotonic()
        items_in = len(unresolved)
        resolved = 0

        for i in list(unresolved):
            desc = descriptions[i]
            norm_desc = item_results[i].normalized_description or desc

            gk_result = self.gatekeeper.validate({
                'normalized_description': norm_desc,
                'description': desc,
            })

            item_results[i].quality_score = gk_result.score

            if gk_result.status == 'APPROVED':
                item_results[i].gate_status = 'GREEN'
            elif gk_result.status == 'PENDING_REVIEW':
                item_results[i].gate_status = 'YELLOW'
            else:
                if gk_result.is_forbidden_pattern:
                    item_results[i].gate_status = 'RED'
                else:
                    item_results[i].gate_status = 'RED'

            # Generate temp code for non-GREEN items
            if item_results[i].gate_status in ('YELLOW', 'RED'):
                from sqlalchemy import func as sqla_func
                max_seq = self.db.query(sqla_func.count(ProjectWorkItem.pwi_id)).filter(
                    ProjectWorkItem.project_id == project_id,
                ).scalar() or 0
                temp_code = f"PRJ.{project_id}-TEMP-{max_seq + 1:03d}"
                item_results[i].temp_code = temp_code

                # Create ProjectWorkItem
                pwi = ProjectWorkItem(
                    project_id=project_id,
                    file_id=file_id,
                    original_description=desc,
                    normalized_description=norm_desc,
                    temp_code=temp_code,
                    quality_score=gk_result.score,
                    gate_status=item_results[i].gate_status,
                    unit=original_items[i].get('unit') if i < len(original_items) else None,
                    quantity=original_items[i].get('quantity') if i < len(original_items) else None,
                    unit_price=original_items[i].get('unit_price') if i < len(original_items) else None,
                    resolution_status='UNRESOLVED',
                    ai_structured_output=json.dumps(
                        item_results[i].structured_output, ensure_ascii=False
                    ) if item_results[i].structured_output else None,
                )
                self.db.add(pwi)

            item_results[i].resolved_stage = 'gatekeeper'
            unresolved.discard(i)
            resolved += 1

        self.db.flush()

        duration = (time.monotonic() - start) * 1000
        return FunnelStageResult(
            stage_name='gatekeeper',
            items_in=items_in,
            items_resolved=resolved,
            hit_rate=resolved / items_in if items_in > 0 else 0.0,
            duration_ms=duration,
        )

    # ── Cache builders ──

    def _get_synonym_cache(self) -> Dict[str, int]:
        """Build in-memory synonym -> master_id cache."""
        if self._synonym_cache is not None:
            return self._synonym_cache

        self._synonym_cache = {}
        synonyms = self.db.query(
            MasterSynonym.synonym_normalized,
            MasterSynonym.master_id,
        ).filter(
            MasterSynonym.is_active == True,
        ).all()

        for syn_norm, master_id in synonyms:
            if syn_norm:
                self._synonym_cache[syn_norm.lower().strip()] = master_id

        logger.info(f"Synonym cache loaded: {len(self._synonym_cache)} entries")
        return self._synonym_cache

    def _get_exact_cache(self) -> Dict[str, int]:
        """Build in-memory normalized_description -> master_id cache."""
        if self._exact_cache is not None:
            return self._exact_cache

        self._exact_cache = {}
        masters = self.db.query(
            MasterWorkItem.description_normalized,
            MasterWorkItem.master_id,
        ).filter(
            MasterWorkItem.is_active == True,
        ).all()

        for desc_norm, master_id in masters:
            if desc_norm:
                self._exact_cache[desc_norm.lower().strip()] = master_id

        logger.info(f"Exact match cache loaded: {len(self._exact_cache)} entries")
        return self._exact_cache

    def _get_hybrid_matcher(self):
        """Lazy-load hybrid matcher."""
        if self._hybrid_matcher is not None:
            return self._hybrid_matcher

        if not settings.HYBRID_MATCHER_ENABLED:
            return None

        try:
            from app.services.hybrid_matcher import get_hybrid_matcher
            self._hybrid_matcher = get_hybrid_matcher(self.db)
        except Exception as e:
            logger.warning(f"Failed to initialize hybrid matcher for funnel: {e}")
            self._hybrid_matcher = None

        return self._hybrid_matcher

    def _get_ai_normalizer(self):
        """Lazy-load AI normalizer."""
        if self._ai_normalizer is not None:
            return self._ai_normalizer

        try:
            from app.services.ai_normalizer import get_ai_normalizer
            self._ai_normalizer = get_ai_normalizer()
        except Exception as e:
            logger.warning(f"Failed to initialize AI normalizer for funnel: {e}")
            self._ai_normalizer = None

        return self._ai_normalizer


def get_cost_funnel(db: Session) -> CostFunnel:
    """Factory function for CostFunnel."""
    return CostFunnel(db)
