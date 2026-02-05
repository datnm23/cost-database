"""
Pytest configuration and shared fixtures.

This file provides common fixtures for testing the BOQ Cost Database backend.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from typing import Generator

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ===========================================
# Database Fixtures
# ===========================================

@pytest.fixture
def mock_db_session() -> MagicMock:
    """
    Create a mock database session.

    Returns a MagicMock that simulates SQLAlchemy session behavior.
    """
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.flush = MagicMock()
    session.refresh = MagicMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session


@pytest.fixture
def mock_redis() -> MagicMock:
    """
    Create a mock Redis client with in-memory dict storage.
    """
    cache = {}

    redis = MagicMock()
    redis.ping.return_value = True

    def mock_get(key):
        return cache.get(key)

    def mock_set(key, value, ex=None):
        cache[key] = value
        return True

    def mock_delete(key):
        if key in cache:
            del cache[key]
        return True

    def mock_exists(key):
        return key in cache

    def mock_keys(pattern):
        prefix = pattern.replace('*', '')
        return [k for k in cache.keys() if k.startswith(prefix)]

    redis.get = mock_get
    redis.set = mock_set
    redis.delete = mock_delete
    redis.exists = mock_exists
    redis.keys = mock_keys
    redis._cache = cache  # Expose for testing

    return redis


# ===========================================
# Model Fixtures
# ===========================================

@pytest.fixture
def mock_master_item() -> MagicMock:
    """Create a mock MasterWorkItem."""
    item = MagicMock()
    item.master_id = 1
    item.work_code = "BT-M200-001"
    item.description = "Bê tông M200 móng"
    item.description_normalized = "bê tông m200 móng"
    item.sec_code = "SEC-01"
    item.unit_standard = "m3"
    item.is_active = True
    item.is_verified = True
    return item


@pytest.fixture
def mock_pending_item() -> MagicMock:
    """Create a mock PendingMasterItem."""
    item = MagicMock()
    item.pending_id = 1
    item.description = "Bê tông M200 móng test"
    item.description_normalized = "bê tông m200 móng test"
    item.sec_code = "SEC-01"
    item.unit_standard = "m3"
    item.quality_score = 72.5
    item.quality_reasons = '["Good structure"]'
    item.quality_indicators = '{"has_verb": true, "has_material": true}'
    item.status = "PENDING"
    item.reviewed_by = None
    item.reviewed_at = None
    item.review_notes = None
    item.master_id = None
    return item


@pytest.fixture
def mock_synonym() -> MagicMock:
    """Create a mock MasterSynonym."""
    synonym = MagicMock()
    synonym.synonym_id = 1
    synonym.master_id = 1
    synonym.synonym_text = "BT lót móng"
    synonym.synonym_normalized = "bt lót móng"
    synonym.synonym_type = "abbreviation"
    synonym.is_active = True
    return synonym


@pytest.fixture
def mock_quarantine_log() -> MagicMock:
    """Create a mock QuarantineLog."""
    log = MagicMock()
    log.log_id = 1
    log.description = "Invalid item XYZ"
    log.description_normalized = "invalid item xyz"
    log.source_file_id = 10
    log.rejection_reason = "forbidden_pattern"
    log.quality_score = 25.0
    log.matched_forbidden_pattern = "XYZ"
    log.quality_indicators = '{"has_verb": false, "has_material": false}'
    return log


# ===========================================
# Service Fixtures
# ===========================================

@pytest.fixture
def mock_sbert_model() -> MagicMock:
    """Create a mock SBERT model for testing."""
    import numpy as np

    model = MagicMock()

    def mock_encode(texts, show_progress_bar=False, normalize_embeddings=True):
        embeddings = []
        for text in texts:
            # Create deterministic embeddings based on text hash
            np.random.seed(hash(text) % 2**32)
            emb = np.random.randn(768).astype(np.float32)
            if normalize_embeddings:
                emb = emb / np.linalg.norm(emb)
            embeddings.append(emb)
        return np.array(embeddings)

    model.encode = mock_encode
    model.eval = MagicMock()

    return model


# ===========================================
# Test Client Fixtures
# ===========================================

@pytest.fixture
def test_client():
    """
    Create a FastAPI test client.

    Note: This requires the actual app to be importable.
    Use mock_db_session for unit tests instead.
    """
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            yield client
    except ImportError:
        pytest.skip("FastAPI app not available for integration testing")


# ===========================================
# Utility Fixtures
# ===========================================

@pytest.fixture
def temp_cache_dir(tmp_path) -> str:
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return str(cache_dir)


@pytest.fixture
def sample_descriptions() -> list:
    """Sample Vietnamese construction descriptions for testing."""
    return [
        "Bê tông M200 móng",
        "Bê tông M200 cột",
        "Ván khuôn gỗ dầm",
        "Thép D12 cột",
        "Cốt thép móng D16",
        "Cung cấp lắp đặt ống HDPE D110",
        "Đào đất móng máy",
        "Xây tường gạch 220",
        "Trát tường trong nhà",
        "Sơn nước nội thất",
    ]


@pytest.fixture
def sample_abbreviations() -> dict:
    """Sample Vietnamese construction abbreviations."""
    return {
        "BT": "Bê tông",
        "BTCT": "Bê tông cốt thép",
        "VK": "Ván khuôn",
        "CT": "Cốt thép",
        "CPĐD": "Cung cấp lắp đặt",
    }


# ===========================================
# Async Support
# ===========================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
