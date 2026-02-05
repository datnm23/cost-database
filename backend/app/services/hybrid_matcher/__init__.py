"""
Hybrid 3-Tier Matcher Module

Provides O(N*log M) matching performance vs O(N*M) brute force.

Tiers:
1. Exact Match Cache (O(1)) - Redis hash lookup
2. Semantic Embedding Match (O(log M)) - FAISS vector search
3. Fuzzy String Refinement (O(K)) - RapidFuzz on top-K candidates

Use get_hybrid_matcher(db) to get a configured instance.
"""

# Lazy imports to avoid import chain issues during testing
def get_hybrid_matcher(db=None):
    """Get or create singleton HybridMatcherService instance."""
    from app.services.hybrid_matcher.hybrid_matcher_service import get_hybrid_matcher as _get_hybrid_matcher
    return _get_hybrid_matcher(db)


def init_hybrid_matcher(db):
    """Initialize the hybrid matcher at application startup."""
    from app.services.hybrid_matcher.hybrid_matcher_service import init_hybrid_matcher as _init_hybrid_matcher
    return _init_hybrid_matcher(db)


# For direct imports (when all dependencies are available)
__all__ = [
    "get_hybrid_matcher",
    "init_hybrid_matcher",
]

