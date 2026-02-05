"""
Hybrid Matcher Service - Main 4-Tier Orchestrator

Coordinates the four matching tiers:
1. Exact Match Cache (O(1)) - Redis hash lookup
1.5. Synonym Match (O(1)) - Synonym cache lookup
2. Semantic Embedding Match (O(log M)) - FAISS vector search
3. Fuzzy String Refinement (O(K)) - RapidFuzz on top-K candidates

Provides 50-100x performance improvement over brute force O(N*M) matching.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.master_work_item import MasterWorkItem

from app.services.hybrid_matcher.exact_match_cache import (
    ExactMatchCache,
    get_exact_match_cache,
)
from app.services.hybrid_matcher.embedding_service import (
    EmbeddingService,
    get_embedding_service,
)
from app.services.hybrid_matcher.faiss_index_service import (
    FAISSIndexService,
    get_faiss_index_service,
)
from app.services.hybrid_matcher.fuzzy_matcher import (
    FuzzyMatcher,
    get_fuzzy_matcher,
)
from app.services.synonym_service import SynonymService

logger = logging.getLogger(__name__)


@dataclass
class HybridMatchResult:
    """Result of hybrid matching for a single description."""
    query: str  # Input normalized description
    match_type: str  # 'exact', 'fuzzy', 'new'
    similarity_score: float  # 0-1 score
    matched_tier: int  # 1, 2, or 3 (0 if no match)
    master_id: Optional[int] = None
    work_code: Optional[str] = None
    master_description: Optional[str] = None
    candidates: List[Dict] = field(default_factory=list)  # Top candidates for review


class HybridMatcherService:
    """
    Hybrid 4-Tier Matcher Service.

    Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │ TIER 1: EXACT STRING MATCH (O(1))                               │
    │ - Hash-based lookup in Redis cache                              │
    │ - If hit → Return immediately, score=1.0                        │
    └─────────────────────────────────────────────────────────────────┘
         │ No match
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ TIER 1.5: SYNONYM MATCH (O(1))                                  │
    │ - Lookup in synonym cache                                       │
    │ - If hit → Return as exact match, score=1.0                     │
    └─────────────────────────────────────────────────────────────────┘
         │ No match
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ TIER 2: SEMANTIC EMBEDDING MATCH (O(log M) with FAISS)          │
    │ - Pre-computed SBERT embeddings for all master items            │
    │ - Return top K=20 candidates if similarity >= 0.75              │
    │ - If best >= 0.90 → Return as exact match (skip Tier 3)         │
    └─────────────────────────────────────────────────────────────────┘
         │ Candidates
         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ TIER 3: FUZZY STRING REFINEMENT (O(K) where K=20)               │
    │ - RapidFuzz (10x faster than SequenceMatcher)                   │
    │ - Token overlap bonus (existing logic preserved)                │
    │ - Final: exact >= 0.95, fuzzy >= 0.80                           │
    └─────────────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        db: Session,
        cache: ExactMatchCache = None,
        embedding_service: EmbeddingService = None,
        faiss_index: FAISSIndexService = None,
        fuzzy_matcher: FuzzyMatcher = None,
        synonym_service: SynonymService = None,
    ):
        """
        Initialize HybridMatcherService.

        Args:
            db: Database session
            cache: Redis exact match cache
            embedding_service: SBERT embedding service
            faiss_index: FAISS index service
            fuzzy_matcher: RapidFuzz matcher
            synonym_service: Synonym lookup service
        """
        self.db = db
        self.cache = cache or get_exact_match_cache()
        self.embedding_service = embedding_service or get_embedding_service()
        self.faiss_index = faiss_index or get_faiss_index_service()
        self.fuzzy_matcher = fuzzy_matcher or get_fuzzy_matcher()
        self.synonym_service = synonym_service or SynonymService(db)

        # Thresholds from settings
        self.semantic_threshold = settings.SEMANTIC_THRESHOLD
        self.semantic_exact_threshold = settings.SEMANTIC_EXACT_THRESHOLD
        self.faiss_top_k = settings.FAISS_TOP_K
        self.fuzzy_exact_threshold = settings.FUZZY_EXACT_THRESHOLD
        self.fuzzy_match_threshold = settings.FUZZY_MATCH_THRESHOLD

        # Master items lookup
        self._master_lookup: Dict[str, MasterWorkItem] = {}
        self._master_id_lookup: Dict[int, MasterWorkItem] = {}
        self._initialized = False

    def initialize(self, force_rebuild: bool = False):
        """
        Initialize the matcher by loading/building indices.

        Args:
            force_rebuild: Force rebuild of embeddings and index
        """
        if self._initialized and not force_rebuild:
            return

        logger.info("Initializing HybridMatcherService...")

        # Load master items
        master_items = self.db.query(MasterWorkItem).filter(
            MasterWorkItem.is_active == True
        ).all()

        logger.info(f"Loaded {len(master_items)} active master items")

        # Build lookup dictionaries
        self._master_lookup = {}
        self._master_id_lookup = {}
        descriptions = []
        master_ids = []

        for item in master_items:
            if item.description_normalized:
                desc_lower = item.description_normalized.lower().strip()
                self._master_lookup[desc_lower] = item
                self._master_id_lookup[item.master_id] = item
                descriptions.append(desc_lower)
                master_ids.append(item.master_id)

        # Try to load existing embeddings/index
        embeddings_loaded = False
        index_loaded = False

        if not force_rebuild:
            embeddings_loaded = self.embedding_service.load_embeddings()
            index_loaded = self.faiss_index.load_index()

        # Build if not loaded or force rebuild
        if not embeddings_loaded or force_rebuild:
            logger.info("Building master embeddings...")
            embeddings = self.embedding_service.build_master_embeddings(master_items)
            self.embedding_service.save_embeddings()
        else:
            embeddings = self.embedding_service.embeddings

        if not index_loaded or force_rebuild:
            logger.info("Building FAISS index...")
            self.faiss_index.build_index(
                embeddings=embeddings,
                descriptions=descriptions,
                master_ids=master_ids
            )
            self.faiss_index.save_index()

        # Warm the cache
        if self.cache.is_available():
            self.cache.warm_cache(master_items)

        # Build synonym cache
        synonym_count = self.synonym_service.build_synonym_cache()
        logger.info(f"Built synonym cache with {synonym_count} entries")

        self._initialized = True
        logger.info("HybridMatcherService initialized successfully")

    def match(self, description: str) -> HybridMatchResult:
        """
        Match a single description against master items.

        Args:
            description: Normalized description to match

        Returns:
            HybridMatchResult with match details
        """
        if not self._initialized:
            self.initialize()

        desc_lower = description.lower().strip()

        # === TIER 1: Exact Match Cache ===
        cached = self.cache.get(desc_lower)
        if cached:
            return HybridMatchResult(
                query=description,
                match_type='exact',
                similarity_score=1.0,
                matched_tier=1,
                master_id=cached['master_id'],
                work_code=cached['work_code'],
                master_description=cached.get('description'),
            )

        # Also check in-memory lookup for exact match
        if desc_lower in self._master_lookup:
            master = self._master_lookup[desc_lower]
            # Cache for future lookups
            self.cache.set(
                desc_lower,
                master.master_id,
                master.work_code,
                master.description
            )
            return HybridMatchResult(
                query=description,
                match_type='exact',
                similarity_score=1.0,
                matched_tier=1,
                master_id=master.master_id,
                work_code=master.work_code,
                master_description=master.description,
            )

        # === TIER 1.5: Synonym Match ===
        synonym_master = self.synonym_service.find_by_synonym(desc_lower)
        if synonym_master:
            # Cache for future lookups
            self.cache.set(
                desc_lower,
                synonym_master.master_id,
                synonym_master.work_code,
                synonym_master.description
            )
            return HybridMatchResult(
                query=description,
                match_type='exact',
                similarity_score=1.0,
                matched_tier=1,  # Treat as tier 1 since it's O(1) lookup
                master_id=synonym_master.master_id,
                work_code=synonym_master.work_code,
                master_description=synonym_master.description,
            )

        # === TIER 2: Semantic Embedding Match ===
        if self.faiss_index.is_ready():
            query_embedding = self.embedding_service.encode_single(desc_lower)
            faiss_results = self.faiss_index.search(
                query_embedding,
                top_k=self.faiss_top_k,
                threshold=self.semantic_threshold
            )

            if faiss_results:
                # Get the best semantic match
                best_idx, best_semantic_score = faiss_results[0]

                # If semantic score is very high, skip Tier 3
                if best_semantic_score >= self.semantic_exact_threshold:
                    master_id = self.faiss_index.index_to_master_id.get(best_idx)
                    if master_id and master_id in self._master_id_lookup:
                        master = self._master_id_lookup[master_id]

                        # Cache for future lookups
                        self.cache.set(
                            desc_lower,
                            master.master_id,
                            master.work_code,
                            master.description
                        )

                        return HybridMatchResult(
                            query=description,
                            match_type='exact',
                            similarity_score=best_semantic_score,
                            matched_tier=2,
                            master_id=master.master_id,
                            work_code=master.work_code,
                            master_description=master.description,
                        )

                # === TIER 3: Fuzzy String Refinement ===
                # Get candidate descriptions for fuzzy matching
                candidates_for_fuzzy = []
                for idx, semantic_score in faiss_results:
                    desc = self.faiss_index.index_to_description.get(idx)
                    if desc:
                        candidates_for_fuzzy.append((desc, semantic_score))

                # Re-score with fuzzy matching
                fuzzy_results = self.fuzzy_matcher.refine_candidates(
                    desc_lower,
                    candidates_for_fuzzy,
                    min_score=self.fuzzy_match_threshold * 0.8  # Slightly lower for candidates
                )

                if fuzzy_results:
                    best_desc, best_fuzzy_score = fuzzy_results[0]
                    master = self._master_lookup.get(best_desc)

                    if master:
                        # Build candidates list for review
                        candidates = []
                        for cand_desc, cand_score in fuzzy_results[:5]:
                            cand_master = self._master_lookup.get(cand_desc)
                            if cand_master:
                                candidates.append({
                                    'work_code': cand_master.work_code,
                                    'description': cand_master.description,
                                    'similarity': round(cand_score * 100, 1),
                                    'sec_code': cand_master.sec_code,
                                })

                        # Determine match type
                        if best_fuzzy_score >= self.fuzzy_exact_threshold:
                            match_type = 'exact'
                            # Cache exact matches
                            self.cache.set(
                                desc_lower,
                                master.master_id,
                                master.work_code,
                                master.description
                            )
                        elif best_fuzzy_score >= self.fuzzy_match_threshold:
                            match_type = 'fuzzy'
                        else:
                            match_type = 'new'

                        return HybridMatchResult(
                            query=description,
                            match_type=match_type,
                            similarity_score=best_fuzzy_score,
                            matched_tier=3,
                            master_id=master.master_id,
                            work_code=master.work_code,
                            master_description=master.description,
                            candidates=candidates,
                        )

        # No match found
        return HybridMatchResult(
            query=description,
            match_type='new',
            similarity_score=0.0,
            matched_tier=0,
        )

    def match_batch(self, descriptions: List[str]) -> List[HybridMatchResult]:
        """
        Match multiple descriptions in batch for better performance.

        Args:
            descriptions: List of normalized descriptions

        Returns:
            List of HybridMatchResult for each description
        """
        if not self._initialized:
            self.initialize()

        results = []

        # Separate into cache hits and misses
        cache_hits = []
        cache_misses = []
        miss_indices = []

        for i, desc in enumerate(descriptions):
            desc_lower = desc.lower().strip()

            # Check Tier 1 cache
            cached = self.cache.get(desc_lower)
            if cached:
                cache_hits.append((i, HybridMatchResult(
                    query=desc,
                    match_type='exact',
                    similarity_score=1.0,
                    matched_tier=1,
                    master_id=cached['master_id'],
                    work_code=cached['work_code'],
                    master_description=cached.get('description'),
                )))
            elif desc_lower in self._master_lookup:
                master = self._master_lookup[desc_lower]
                # Cache for future
                self.cache.set(desc_lower, master.master_id, master.work_code, master.description)
                cache_hits.append((i, HybridMatchResult(
                    query=desc,
                    match_type='exact',
                    similarity_score=1.0,
                    matched_tier=1,
                    master_id=master.master_id,
                    work_code=master.work_code,
                    master_description=master.description,
                )))
            else:
                cache_misses.append(desc_lower)
                miss_indices.append(i)

        logger.info(f"Batch matching: {len(cache_hits)} cache hits, {len(cache_misses)} need semantic search")

        # Process cache misses through Tier 2 and 3
        miss_results: Dict[int, HybridMatchResult] = {}

        if cache_misses and self.faiss_index.is_ready():
            # Batch encode queries
            query_embeddings = self.embedding_service.encode(cache_misses)

            # Batch FAISS search
            all_faiss_results = self.faiss_index.search_batch(
                query_embeddings,
                top_k=self.faiss_top_k,
                threshold=self.semantic_threshold
            )

            # Process each result
            for i, (orig_idx, desc_lower, faiss_results) in enumerate(
                zip(miss_indices, cache_misses, all_faiss_results)
            ):
                original_desc = descriptions[orig_idx]

                if not faiss_results:
                    miss_results[orig_idx] = HybridMatchResult(
                        query=original_desc,
                        match_type='new',
                        similarity_score=0.0,
                        matched_tier=0,
                    )
                    continue

                best_idx, best_semantic_score = faiss_results[0]

                # High semantic score - skip Tier 3
                if best_semantic_score >= self.semantic_exact_threshold:
                    master_id = self.faiss_index.index_to_master_id.get(best_idx)
                    if master_id and master_id in self._master_id_lookup:
                        master = self._master_id_lookup[master_id]
                        self.cache.set(desc_lower, master.master_id, master.work_code, master.description)
                        miss_results[orig_idx] = HybridMatchResult(
                            query=original_desc,
                            match_type='exact',
                            similarity_score=best_semantic_score,
                            matched_tier=2,
                            master_id=master.master_id,
                            work_code=master.work_code,
                            master_description=master.description,
                        )
                        continue

                # Tier 3: Fuzzy refinement
                candidates_for_fuzzy = []
                for idx, semantic_score in faiss_results:
                    cand_desc = self.faiss_index.index_to_description.get(idx)
                    if cand_desc:
                        candidates_for_fuzzy.append((cand_desc, semantic_score))

                fuzzy_results = self.fuzzy_matcher.refine_candidates(
                    desc_lower,
                    candidates_for_fuzzy,
                    min_score=self.fuzzy_match_threshold * 0.8
                )

                if fuzzy_results:
                    best_desc, best_fuzzy_score = fuzzy_results[0]
                    master = self._master_lookup.get(best_desc)

                    if master:
                        candidates = []
                        for cand_desc, cand_score in fuzzy_results[:5]:
                            cand_master = self._master_lookup.get(cand_desc)
                            if cand_master:
                                candidates.append({
                                    'work_code': cand_master.work_code,
                                    'description': cand_master.description,
                                    'similarity': round(cand_score * 100, 1),
                                    'sec_code': cand_master.sec_code,
                                })

                        if best_fuzzy_score >= self.fuzzy_exact_threshold:
                            match_type = 'exact'
                            self.cache.set(desc_lower, master.master_id, master.work_code, master.description)
                        elif best_fuzzy_score >= self.fuzzy_match_threshold:
                            match_type = 'fuzzy'
                        else:
                            match_type = 'new'

                        miss_results[orig_idx] = HybridMatchResult(
                            query=original_desc,
                            match_type=match_type,
                            similarity_score=best_fuzzy_score,
                            matched_tier=3,
                            master_id=master.master_id,
                            work_code=master.work_code,
                            master_description=master.description,
                            candidates=candidates,
                        )
                        continue

                # No match
                miss_results[orig_idx] = HybridMatchResult(
                    query=original_desc,
                    match_type='new',
                    similarity_score=0.0,
                    matched_tier=0,
                )
        else:
            # FAISS not ready, mark all as new
            for orig_idx, desc_lower in zip(miss_indices, cache_misses):
                miss_results[orig_idx] = HybridMatchResult(
                    query=descriptions[orig_idx],
                    match_type='new',
                    similarity_score=0.0,
                    matched_tier=0,
                )

        # Combine results in original order
        all_results: Dict[int, HybridMatchResult] = {}
        for idx, result in cache_hits:
            all_results[idx] = result
        all_results.update(miss_results)

        return [all_results[i] for i in range(len(descriptions))]

    def match_batch_semantic_only(self, descriptions: List[str]) -> List[HybridMatchResult]:
        """
        Match using ONLY semantic embeddings (100% AI mode).

        Skips Tier 1 (exact cache) and Tier 3 (fuzzy refinement).
        Uses only Tier 2 (semantic embedding match via FAISS).

        Args:
            descriptions: List of normalized descriptions

        Returns:
            List of HybridMatchResult for each description
        """
        if not self._initialized:
            self.initialize()

        results = []

        if not self.faiss_index.is_ready():
            logger.warning("FAISS index not ready for semantic-only matching")
            return [
                HybridMatchResult(
                    query=desc,
                    match_type='new',
                    similarity_score=0.0,
                    matched_tier=0,
                )
                for desc in descriptions
            ]

        # Prepare descriptions for batch processing
        descs_lower = [desc.lower().strip() for desc in descriptions]

        # Batch encode all queries
        query_embeddings = self.embedding_service.encode(descs_lower)

        # Batch FAISS search
        all_faiss_results = self.faiss_index.search_batch(
            query_embeddings,
            top_k=self.faiss_top_k,
            threshold=self.semantic_threshold
        )

        # Process each result using only semantic scores
        for i, (original_desc, desc_lower, faiss_results) in enumerate(
            zip(descriptions, descs_lower, all_faiss_results)
        ):
            if not faiss_results:
                results.append(HybridMatchResult(
                    query=original_desc,
                    match_type='new',
                    similarity_score=0.0,
                    matched_tier=0,
                ))
                continue

            # Get best match based on semantic score only
            best_idx, best_semantic_score = faiss_results[0]
            master_id = self.faiss_index.index_to_master_id.get(best_idx)

            if master_id and master_id in self._master_id_lookup:
                master = self._master_id_lookup[master_id]

                # Build candidates from top results
                candidates = []
                for idx, semantic_score in faiss_results[:5]:
                    cand_desc = self.faiss_index.index_to_description.get(idx)
                    cand_master_id = self.faiss_index.index_to_master_id.get(idx)
                    if cand_desc and cand_master_id in self._master_id_lookup:
                        cand_master = self._master_id_lookup[cand_master_id]
                        candidates.append({
                            'work_code': cand_master.work_code,
                            'description': cand_master.description,
                            'similarity': round(semantic_score * 100, 1),
                            'sec_code': cand_master.sec_code,
                        })

                # Determine match type based on semantic score
                if best_semantic_score >= self.semantic_exact_threshold:
                    match_type = 'exact'
                elif best_semantic_score >= self.semantic_threshold:
                    match_type = 'fuzzy'
                else:
                    match_type = 'new'

                results.append(HybridMatchResult(
                    query=original_desc,
                    match_type=match_type,
                    similarity_score=best_semantic_score,
                    matched_tier=2,  # Always tier 2 for AI-only
                    master_id=master.master_id,
                    work_code=master.work_code,
                    master_description=master.description,
                    candidates=candidates,
                ))
            else:
                results.append(HybridMatchResult(
                    query=original_desc,
                    match_type='new',
                    similarity_score=0.0,
                    matched_tier=0,
                ))

        logger.info(f"Semantic-only batch matching completed: {len(descriptions)} items processed")
        return results

    def rebuild_index(self):
        """Force rebuild of embeddings and FAISS index."""
        self._initialized = False
        self.initialize(force_rebuild=True)

    def clear_cache(self):
        """Clear the exact match cache."""
        return self.cache.clear_all()

    def get_statistics(self) -> Dict[str, Any]:
        """Get matcher statistics."""
        return {
            'initialized': self._initialized,
            'master_items_count': len(self._master_lookup),
            'cache': self.cache.get_statistics(),
            'embeddings': self.embedding_service.get_statistics(),
            'faiss_index': self.faiss_index.get_statistics(),
            'thresholds': {
                'semantic_threshold': self.semantic_threshold,
                'semantic_exact_threshold': self.semantic_exact_threshold,
                'faiss_top_k': self.faiss_top_k,
                'fuzzy_exact_threshold': self.fuzzy_exact_threshold,
                'fuzzy_match_threshold': self.fuzzy_match_threshold,
            }
        }


# Module-level singleton
_hybrid_matcher: Optional[HybridMatcherService] = None


def get_hybrid_matcher(db: Session = None) -> HybridMatcherService:
    """
    Get or create singleton HybridMatcherService instance.

    Args:
        db: Database session (required for first initialization)

    Returns:
        HybridMatcherService instance
    """
    global _hybrid_matcher

    if _hybrid_matcher is None:
        if db is None:
            raise ValueError("Database session required for initial HybridMatcherService creation")
        _hybrid_matcher = HybridMatcherService(db=db)

    return _hybrid_matcher


def init_hybrid_matcher(db: Session) -> HybridMatcherService:
    """
    Initialize the hybrid matcher at application startup.

    Args:
        db: Database session

    Returns:
        Initialized HybridMatcherService instance
    """
    global _hybrid_matcher

    logger.info("Initializing HybridMatcherService at startup...")
    _hybrid_matcher = HybridMatcherService(db=db)
    _hybrid_matcher.initialize()

    return _hybrid_matcher
