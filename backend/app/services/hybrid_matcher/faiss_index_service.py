"""
FAISS Index Service for fast vector similarity search.

Uses FAISS IndexFlatIP (Inner Product) for O(log M) similarity search
on normalized embeddings (equivalent to cosine similarity).
"""

import logging
import pickle
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class FAISSIndexService:
    """
    Service for FAISS-based vector similarity search.

    Uses IndexFlatIP for inner product search on L2-normalized vectors,
    which is equivalent to cosine similarity.
    """

    def __init__(self, cache_dir: str = None):
        """
        Initialize FAISSIndexService.

        Args:
            cache_dir: Directory for caching the FAISS index
        """
        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available. Install with: pip install faiss-cpu")

        self.cache_dir = Path(cache_dir or settings.MODEL_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.cache_dir / 'faiss_index.pkl'

        self.index: Optional[Any] = None  # faiss.IndexFlatIP
        self.embedding_dim: int = 0
        self.num_vectors: int = 0

        # Mapping from FAISS index position to original data
        self.index_to_description: Dict[int, str] = {}
        self.index_to_master_id: Dict[int, int] = {}

    def build_index(
        self,
        embeddings: np.ndarray,
        descriptions: List[str] = None,
        master_ids: List[int] = None
    ) -> bool:
        """
        Build FAISS index from embeddings.

        Args:
            embeddings: Numpy array of embeddings (N x dim)
            descriptions: Optional list of descriptions for each embedding
            master_ids: Optional list of master_ids for each embedding

        Returns:
            True if successful, False otherwise
        """
        if not FAISS_AVAILABLE:
            logger.error("FAISS not available")
            return False

        if embeddings is None or len(embeddings) == 0:
            logger.warning("No embeddings to index")
            return False

        # Ensure embeddings are float32 and normalized
        embeddings = embeddings.astype(np.float32)

        # Normalize if not already (for cosine similarity via inner product)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        embeddings = embeddings / norms

        self.embedding_dim = embeddings.shape[1]
        self.num_vectors = embeddings.shape[0]

        # Create IndexFlatIP (Inner Product for cosine similarity on normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings)

        # Store mappings
        if descriptions:
            self.index_to_description = {
                i: desc for i, desc in enumerate(descriptions)
            }
        if master_ids:
            self.index_to_master_id = {
                i: mid for i, mid in enumerate(master_ids)
            }

        logger.info(f"Built FAISS index with {self.num_vectors} vectors of dimension {self.embedding_dim}")
        return True

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = None,
        threshold: float = None
    ) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query vector (dim,) or (1, dim)
            top_k: Number of results to return (default from settings)
            threshold: Minimum similarity threshold (default from settings)

        Returns:
            List of (index, similarity_score) tuples
        """
        if not FAISS_AVAILABLE or self.index is None:
            logger.warning("FAISS index not available")
            return []

        top_k = top_k or settings.FAISS_TOP_K
        threshold = threshold or settings.SEMANTIC_THRESHOLD

        # Ensure correct shape and type
        query = query_embedding.astype(np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)

        # Normalize query
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm

        # Search
        similarities, indices = self.index.search(query, top_k)

        # Filter by threshold and format results
        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx >= 0 and sim >= threshold:  # FAISS uses -1 for invalid
                results.append((int(idx), float(sim)))

        return results

    def search_batch(
        self,
        query_embeddings: np.ndarray,
        top_k: int = None,
        threshold: float = None
    ) -> List[List[Tuple[int, float]]]:
        """
        Search for similar vectors in batch.

        Args:
            query_embeddings: Query vectors (N, dim)
            top_k: Number of results per query
            threshold: Minimum similarity threshold

        Returns:
            List of results for each query
        """
        if not FAISS_AVAILABLE or self.index is None:
            logger.warning("FAISS index not available")
            return [[] for _ in range(len(query_embeddings))]

        top_k = top_k or settings.FAISS_TOP_K
        threshold = threshold or settings.SEMANTIC_THRESHOLD

        # Ensure correct shape and type
        queries = query_embeddings.astype(np.float32)
        if queries.ndim == 1:
            queries = queries.reshape(1, -1)

        # Normalize queries
        norms = np.linalg.norm(queries, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        queries = queries / norms

        # Batch search
        similarities, indices = self.index.search(queries, top_k)

        # Format results
        all_results = []
        for sims, idxs in zip(similarities, indices):
            results = []
            for sim, idx in zip(sims, idxs):
                if idx >= 0 and sim >= threshold:
                    results.append((int(idx), float(sim)))
            all_results.append(results)

        return all_results

    def search_with_descriptions(
        self,
        query_embedding: np.ndarray,
        top_k: int = None,
        threshold: float = None
    ) -> List[Tuple[str, float]]:
        """
        Search and return descriptions instead of indices.

        Args:
            query_embedding: Query vector
            top_k: Number of results
            threshold: Minimum similarity

        Returns:
            List of (description, similarity) tuples
        """
        results = self.search(query_embedding, top_k, threshold)

        return [
            (self.index_to_description.get(idx, ""), score)
            for idx, score in results
            if idx in self.index_to_description
        ]

    def save_index(self):
        """Save FAISS index and mappings to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return

        data = {
            'index_bytes': faiss.serialize_index(self.index) if FAISS_AVAILABLE else None,
            'embedding_dim': self.embedding_dim,
            'num_vectors': self.num_vectors,
            'index_to_description': self.index_to_description,
            'index_to_master_id': self.index_to_master_id,
        }

        with open(self.index_file, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"FAISS index saved to {self.index_file}")

    def load_index(self) -> bool:
        """
        Load FAISS index from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not FAISS_AVAILABLE:
            logger.error("FAISS not available")
            return False

        if not self.index_file.exists():
            logger.info("No saved FAISS index found")
            return False

        try:
            with open(self.index_file, 'rb') as f:
                data = pickle.load(f)

            self.index = faiss.deserialize_index(data['index_bytes'])
            self.embedding_dim = data['embedding_dim']
            self.num_vectors = data['num_vectors']
            self.index_to_description = data['index_to_description']
            self.index_to_master_id = data['index_to_master_id']

            logger.info(f"Loaded FAISS index with {self.num_vectors} vectors")
            return True

        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False

    def is_ready(self) -> bool:
        """Check if index is ready for search."""
        return FAISS_AVAILABLE and self.index is not None and self.num_vectors > 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'faiss_available': FAISS_AVAILABLE,
            'index_ready': self.is_ready(),
            'num_vectors': self.num_vectors,
            'embedding_dim': self.embedding_dim,
            'index_file': str(self.index_file),
            'index_file_exists': self.index_file.exists(),
        }


# Module-level singleton
_faiss_index_service: Optional[FAISSIndexService] = None


def get_faiss_index_service() -> FAISSIndexService:
    """Get or create singleton FAISSIndexService instance."""
    global _faiss_index_service
    if _faiss_index_service is None:
        _faiss_index_service = FAISSIndexService()
    return _faiss_index_service
