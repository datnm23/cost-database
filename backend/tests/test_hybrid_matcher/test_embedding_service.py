"""
Unit tests for EmbeddingService.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os


class TestEmbeddingService:
    """Tests for EmbeddingService class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_model(self):
        """Create a mock sentence transformer model."""
        model = MagicMock()
        # Return normalized embeddings (768 dim like Vietnamese SBERT)
        def mock_encode(texts, show_progress_bar=False, normalize_embeddings=True):
            embeddings = np.random.randn(len(texts), 768).astype(np.float32)
            if normalize_embeddings:
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                embeddings = embeddings / norms
            return embeddings
        model.encode = mock_encode
        return model

    def test_encode_returns_normalized_embeddings(self, temp_cache_dir, mock_model):
        """encode() should return normalized embeddings."""
        with patch('app.services.hybrid_matcher.embedding_service.load_model_cpu_optimized', return_value=mock_model):
            from app.services.hybrid_matcher.embedding_service import EmbeddingService
            service = EmbeddingService(cache_dir=temp_cache_dir)

            texts = ["bê tông m200", "ván khuôn gỗ"]
            embeddings = service.encode(texts)

            assert embeddings.shape == (2, 768)
            # Check normalization (L2 norm should be ~1)
            norms = np.linalg.norm(embeddings, axis=1)
            np.testing.assert_array_almost_equal(norms, np.ones(2), decimal=5)

    def test_encode_single(self, temp_cache_dir, mock_model):
        """encode_single() should return a single embedding vector."""
        with patch('app.services.hybrid_matcher.embedding_service.load_model_cpu_optimized', return_value=mock_model):
            from app.services.hybrid_matcher.embedding_service import EmbeddingService
            service = EmbeddingService(cache_dir=temp_cache_dir)

            embedding = service.encode_single("bê tông m200")

            assert embedding.shape == (768,)

    def test_build_master_embeddings(self, temp_cache_dir, mock_model):
        """build_master_embeddings() should create embeddings and mappings."""
        with patch('app.services.hybrid_matcher.embedding_service.load_model_cpu_optimized', return_value=mock_model):
            from app.services.hybrid_matcher.embedding_service import EmbeddingService
            service = EmbeddingService(cache_dir=temp_cache_dir)

            # Create mock master items
            master_items = [
                Mock(master_id=1, description_normalized="bê tông m200 móng"),
                Mock(master_id=2, description_normalized="ván khuôn gỗ dầm"),
                Mock(master_id=3, description_normalized="cốt thép phi 12"),
            ]

            embeddings = service.build_master_embeddings(master_items)

            assert embeddings.shape == (3, 768)
            assert service.id_to_index == {1: 0, 2: 1, 3: 2}
            assert service.index_to_id == {0: 1, 1: 2, 2: 3}
            assert len(service.description_to_index) == 3

    def test_save_and_load_embeddings(self, temp_cache_dir, mock_model):
        """Embeddings should be saveable and loadable."""
        with patch('app.services.hybrid_matcher.embedding_service.load_model_cpu_optimized', return_value=mock_model):
            from app.services.hybrid_matcher.embedding_service import EmbeddingService

            # Create and save
            service1 = EmbeddingService(cache_dir=temp_cache_dir)
            master_items = [
                Mock(master_id=1, description_normalized="bê tông m200"),
                Mock(master_id=2, description_normalized="ván khuôn gỗ"),
            ]
            service1.build_master_embeddings(master_items)
            service1.save_embeddings()

            # Load in new instance
            service2 = EmbeddingService(cache_dir=temp_cache_dir)
            loaded = service2.load_embeddings()

            assert loaded == True
            assert service2.embeddings.shape == (2, 768)
            assert service2.id_to_index == {1: 0, 2: 1}

    def test_has_embeddings(self, temp_cache_dir, mock_model):
        """has_embeddings() should return correct status."""
        with patch('app.services.hybrid_matcher.embedding_service.load_model_cpu_optimized', return_value=mock_model):
            from app.services.hybrid_matcher.embedding_service import EmbeddingService
            service = EmbeddingService(cache_dir=temp_cache_dir)

            assert service.has_embeddings() == False

            service.build_master_embeddings([
                Mock(master_id=1, description_normalized="test")
            ])

            assert service.has_embeddings() == True

    def test_get_embedding_by_id(self, temp_cache_dir, mock_model):
        """get_embedding_by_id() should return correct embedding."""
        with patch('app.services.hybrid_matcher.embedding_service.load_model_cpu_optimized', return_value=mock_model):
            from app.services.hybrid_matcher.embedding_service import EmbeddingService
            service = EmbeddingService(cache_dir=temp_cache_dir)

            master_items = [
                Mock(master_id=1, description_normalized="test1"),
                Mock(master_id=2, description_normalized="test2"),
            ]
            service.build_master_embeddings(master_items)

            emb = service.get_embedding_by_id(1)
            assert emb is not None
            assert emb.shape == (768,)

            assert service.get_embedding_by_id(999) is None

    def test_get_statistics(self, temp_cache_dir, mock_model):
        """get_statistics() should return service info."""
        with patch('app.services.hybrid_matcher.embedding_service.load_model_cpu_optimized', return_value=mock_model):
            from app.services.hybrid_matcher.embedding_service import EmbeddingService
            service = EmbeddingService(cache_dir=temp_cache_dir)

            stats = service.get_statistics()

            assert 'model_name' in stats
            assert 'model_loaded' in stats
            assert 'embeddings_count' in stats
