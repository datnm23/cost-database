"""
Unit tests for ExactMatchCache.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestExactMatchCache:
    """Tests for ExactMatchCache class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis = MagicMock()
        redis.ping.return_value = True

        # Simulate an in-memory cache
        cache = {}

        def mock_get(key):
            return cache.get(key)

        def mock_set(key, value, expire=3600):
            cache[key] = value
            return True

        def mock_delete(key):
            if key in cache:
                del cache[key]
                return True
            return False

        def mock_clear_pattern(pattern):
            prefix = pattern.replace('*', '')
            keys_to_delete = [k for k in cache if k.startswith(prefix)]
            for k in keys_to_delete:
                del cache[k]
            return len(keys_to_delete)

        redis.get = mock_get
        redis.set = mock_set
        redis.delete = mock_delete
        redis.clear_pattern = mock_clear_pattern

        return redis, cache

    def test_get_and_set(self, mock_redis):
        """get() and set() should work correctly."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            # Set a value
            result = cache.set(
                description="bê tông m200 móng",
                master_id=1,
                work_code="BT001",
                master_description="Bê tông M200 móng"
            )
            assert result == True

            # Get the value
            cached = cache.get("bê tông m200 móng")
            assert cached is not None
            assert cached['master_id'] == 1
            assert cached['work_code'] == "BT001"

    def test_case_insensitive_keys(self, mock_redis):
        """Keys should be case-insensitive."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            cache.set("Bê Tông M200", master_id=1, work_code="BT001")

            # Should find with different case
            assert cache.get("bê tông m200") is not None
            assert cache.get("BÊ TÔNG M200") is not None

    def test_get_nonexistent_returns_none(self, mock_redis):
        """get() for nonexistent key should return None."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            result = cache.get("nonexistent key")
            assert result is None

    def test_delete(self, mock_redis):
        """delete() should remove cached entry."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            cache.set("test description", master_id=1, work_code="T001")
            assert cache.get("test description") is not None

            cache.delete("test description")
            assert cache.get("test description") is None

    def test_get_batch(self, mock_redis):
        """get_batch() should return dict of results."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            cache.set("desc1", master_id=1, work_code="T001")
            cache.set("desc2", master_id=2, work_code="T002")

            results = cache.get_batch(["desc1", "desc2", "desc3"])

            assert results["desc1"] is not None
            assert results["desc2"] is not None
            assert results["desc3"] is None

    def test_set_batch(self, mock_redis):
        """set_batch() should cache multiple items."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            items = [
                {'description': 'desc1', 'master_id': 1, 'work_code': 'T001'},
                {'description': 'desc2', 'master_id': 2, 'work_code': 'T002'},
            ]
            count = cache.set_batch(items)

            assert count == 2
            assert cache.get("desc1") is not None
            assert cache.get("desc2") is not None

    def test_warm_cache(self, mock_redis):
        """warm_cache() should cache master items."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            master_items = [
                Mock(master_id=1, description_normalized="desc1", work_code="T001", description="Desc 1"),
                Mock(master_id=2, description_normalized="desc2", work_code="T002", description="Desc 2"),
                Mock(master_id=3, description_normalized=None, work_code="T003", description="Desc 3"),  # No normalized
            ]

            count = cache.warm_cache(master_items)

            assert count == 2  # Only 2 have normalized descriptions
            assert cache.get("desc1") is not None
            assert cache.get("desc2") is not None

    def test_clear_all(self, mock_redis):
        """clear_all() should remove all cache entries."""
        redis_client, internal_cache = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            cache.set("desc1", master_id=1, work_code="T001")
            cache.set("desc2", master_id=2, work_code="T002")

            cleared = cache.clear_all()

            assert cleared == 2
            assert cache.get("desc1") is None
            assert cache.get("desc2") is None

    def test_is_available(self, mock_redis):
        """is_available() should return Redis status."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client)

            assert cache.is_available() == True

            # Simulate Redis failure
            redis_client.ping.return_value = False
            redis_client.ping.side_effect = Exception("Connection refused")

            assert cache.is_available() == False

    def test_get_statistics(self, mock_redis):
        """get_statistics() should return cache info."""
        redis_client, _ = mock_redis

        with patch('app.services.hybrid_matcher.exact_match_cache.get_redis', return_value=redis_client):
            from app.services.hybrid_matcher.exact_match_cache import ExactMatchCache
            cache = ExactMatchCache(redis_client=redis_client, ttl=7200)

            stats = cache.get_statistics()

            assert stats['prefix'] == "match:exact:"
            assert stats['ttl'] == 7200
            assert 'redis_available' in stats
