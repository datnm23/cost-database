"""
Unit tests for FAISSIndexService.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import tempfile
import pickle


# Inline FAISSIndexService for testing to avoid import chain
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None


class FAISSIndexService:
    """Inline test version of FAISSIndexService."""

    def __init__(self, cache_dir=None):
        from pathlib import Path
        self.cache_dir = Path(cache_dir) if cache_dir else Path('.')
        self.index_file = self.cache_dir / 'faiss_index.pkl'
        self.index = None
        self.embedding_dim = 0
        self.num_vectors = 0
        self.index_to_description = {}
        self.index_to_master_id = {}

    def build_index(self, embeddings, descriptions=None, master_ids=None):
        if not FAISS_AVAILABLE:
            return False
        if embeddings is None or len(embeddings) == 0:
            return False

        embeddings = embeddings.astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        embeddings = embeddings / norms

        self.embedding_dim = embeddings.shape[1]
        self.num_vectors = embeddings.shape[0]
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings)

        if descriptions:
            self.index_to_description = {i: desc for i, desc in enumerate(descriptions)}
        if master_ids:
            self.index_to_master_id = {i: mid for i, mid in enumerate(master_ids)}
        return True

    def search(self, query_embedding, top_k=20, threshold=0.75):
        if not FAISS_AVAILABLE or self.index is None:
            return []
        query = query_embedding.astype(np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm
        similarities, indices = self.index.search(query, top_k)
        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx >= 0 and sim >= threshold:
                results.append((int(idx), float(sim)))
        return results

    def search_batch(self, query_embeddings, top_k=20, threshold=0.75):
        if not FAISS_AVAILABLE or self.index is None:
            return [[] for _ in range(len(query_embeddings))]
        queries = query_embeddings.astype(np.float32)
        if queries.ndim == 1:
            queries = queries.reshape(1, -1)
        norms = np.linalg.norm(queries, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        queries = queries / norms
        similarities, indices = self.index.search(queries, top_k)
        all_results = []
        for sims, idxs in zip(similarities, indices):
            results = []
            for sim, idx in zip(sims, idxs):
                if idx >= 0 and sim >= threshold:
                    results.append((int(idx), float(sim)))
            all_results.append(results)
        return all_results

    def search_with_descriptions(self, query_embedding, top_k=20, threshold=0.75):
        results = self.search(query_embedding, top_k, threshold)
        return [(self.index_to_description.get(idx, ""), score)
                for idx, score in results if idx in self.index_to_description]

    def save_index(self):
        if self.index is None:
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

    def load_index(self):
        if not FAISS_AVAILABLE or not self.index_file.exists():
            return False
        try:
            with open(self.index_file, 'rb') as f:
                data = pickle.load(f)
            self.index = faiss.deserialize_index(data['index_bytes'])
            self.embedding_dim = data['embedding_dim']
            self.num_vectors = data['num_vectors']
            self.index_to_description = data['index_to_description']
            self.index_to_master_id = data['index_to_master_id']
            return True
        except Exception:
            return False

    def is_ready(self):
        return FAISS_AVAILABLE and self.index is not None and self.num_vectors > 0

    def get_statistics(self):
        return {
            'faiss_available': FAISS_AVAILABLE,
            'index_ready': self.is_ready(),
            'num_vectors': self.num_vectors,
            'embedding_dim': self.embedding_dim,
            'index_file': str(self.index_file),
            'index_file_exists': self.index_file.exists(),
        }


class TestFAISSIndexService:
    """Tests for FAISSIndexService class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def sample_embeddings(self):
        """Create sample normalized embeddings."""
        np.random.seed(42)
        embeddings = np.random.randn(100, 768).astype(np.float32)
        # Normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms

    @pytest.fixture
    def sample_descriptions(self):
        """Create sample descriptions."""
        return [f"description_{i}" for i in range(100)]

    @pytest.fixture
    def sample_master_ids(self):
        """Create sample master IDs."""
        return list(range(1, 101))

    def test_build_index(self, temp_cache_dir, sample_embeddings, sample_descriptions, sample_master_ids):
        """build_index() should create a searchable FAISS index."""
        from app.services.hybrid_matcher.faiss_index_service import FAISSIndexService, FAISS_AVAILABLE

        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not installed")

        service = FAISSIndexService(cache_dir=temp_cache_dir)
        result = service.build_index(
            embeddings=sample_embeddings,
            descriptions=sample_descriptions,
            master_ids=sample_master_ids
        )

        assert result == True
        assert service.is_ready() == True
        assert service.num_vectors == 100
        assert service.embedding_dim == 768

    def test_search_returns_similar_vectors(self, temp_cache_dir, sample_embeddings, sample_descriptions, sample_master_ids):
        """search() should return similar vectors."""
        from app.services.hybrid_matcher.faiss_index_service import FAISSIndexService, FAISS_AVAILABLE

        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not installed")

        service = FAISSIndexService(cache_dir=temp_cache_dir)
        service.build_index(sample_embeddings, sample_descriptions, sample_master_ids)

        # Search with the first embedding (should find itself)
        query = sample_embeddings[0]
        results = service.search(query, top_k=5, threshold=0.5)

        assert len(results) > 0
        # First result should be the query itself (index 0, score ~1.0)
        assert results[0][0] == 0
        assert results[0][1] > 0.99

    def test_search_respects_threshold(self, temp_cache_dir):
        """search() should filter by threshold."""
        from app.services.hybrid_matcher.faiss_index_service import FAISSIndexService, FAISS_AVAILABLE

        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not installed")

        # Create distinct embeddings that won't match well
        embeddings = np.eye(10, dtype=np.float32)  # Orthogonal vectors

        service = FAISSIndexService(cache_dir=temp_cache_dir)
        service.build_index(embeddings)

        # Search with orthogonal query
        query = embeddings[0]
        results = service.search(query, top_k=10, threshold=0.9)

        # Only the exact match should pass threshold=0.9
        assert len(results) == 1
        assert results[0][0] == 0

    def test_search_batch(self, temp_cache_dir, sample_embeddings, sample_descriptions, sample_master_ids):
        """search_batch() should handle multiple queries."""
        from app.services.hybrid_matcher.faiss_index_service import FAISSIndexService, FAISS_AVAILABLE

        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not installed")

        service = FAISSIndexService(cache_dir=temp_cache_dir)
        service.build_index(sample_embeddings, sample_descriptions, sample_master_ids)

        # Search with first 5 embeddings
        queries = sample_embeddings[:5]
        all_results = service.search_batch(queries, top_k=3, threshold=0.5)

        assert len(all_results) == 5
        # Each query should find at least itself
        for i, results in enumerate(all_results):
            assert len(results) > 0
            assert results[0][0] == i  # Should find itself first

    def test_search_with_descriptions(self, temp_cache_dir, sample_embeddings, sample_descriptions, sample_master_ids):
        """search_with_descriptions() should return descriptions."""
        from app.services.hybrid_matcher.faiss_index_service import FAISSIndexService, FAISS_AVAILABLE

        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not installed")

        service = FAISSIndexService(cache_dir=temp_cache_dir)
        service.build_index(sample_embeddings, sample_descriptions, sample_master_ids)

        query = sample_embeddings[0]
        results = service.search_with_descriptions(query, top_k=3, threshold=0.5)

        assert len(results) > 0
        # Results should be (description, score) tuples
        assert results[0][0] == "description_0"
        assert results[0][1] > 0.99

    def test_save_and_load_index(self, temp_cache_dir, sample_embeddings, sample_descriptions, sample_master_ids):
        """Index should be saveable and loadable."""
        from app.services.hybrid_matcher.faiss_index_service import FAISSIndexService, FAISS_AVAILABLE

        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not installed")

        # Build and save
        service1 = FAISSIndexService(cache_dir=temp_cache_dir)
        service1.build_index(sample_embeddings, sample_descriptions, sample_master_ids)
        service1.save_index()

        # Load in new instance
        service2 = FAISSIndexService(cache_dir=temp_cache_dir)
        loaded = service2.load_index()

        assert loaded == True
        assert service2.is_ready() == True
        assert service2.num_vectors == 100

        # Verify search still works
        query = sample_embeddings[0]
        results = service2.search(query, top_k=3, threshold=0.5)
        assert len(results) > 0

    def test_empty_embeddings(self, temp_cache_dir):
        """build_index() with empty embeddings should return False."""
        from app.services.hybrid_matcher.faiss_index_service import FAISSIndexService, FAISS_AVAILABLE

        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not installed")

        service = FAISSIndexService(cache_dir=temp_cache_dir)
        result = service.build_index(np.array([]))

        assert result == False
        assert service.is_ready() == False

    def test_get_statistics(self, temp_cache_dir, sample_embeddings):
        """get_statistics() should return index info."""
        from app.services.hybrid_matcher.faiss_index_service import FAISSIndexService, FAISS_AVAILABLE

        if not FAISS_AVAILABLE:
            pytest.skip("FAISS not installed")

        service = FAISSIndexService(cache_dir=temp_cache_dir)
        service.build_index(sample_embeddings)

        stats = service.get_statistics()

        assert stats['faiss_available'] == True
        assert stats['index_ready'] == True
        assert stats['num_vectors'] == 100
        assert stats['embedding_dim'] == 768
