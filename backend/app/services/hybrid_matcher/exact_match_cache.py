"""
Exact Match Cache using Redis.

Provides O(1) lookup for exact matches by storing a hash of
the normalized description.
"""

import hashlib
import logging
import json
from typing import Optional, Dict, Any, List

from app.core.redis import get_redis, RedisClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class ExactMatchCache:
    """
    Redis-based cache for exact string matching.

    Uses hash(normalized_description_lowercase) as key for O(1) lookup.
    Stores master_id and work_code for matched items.
    """

    CACHE_PREFIX = "match:exact:"

    def __init__(self, redis_client: RedisClient = None, ttl: int = None):
        """
        Initialize ExactMatchCache.

        Args:
            redis_client: Redis client instance (uses default if None)
            ttl: Cache TTL in seconds (default from settings)
        """
        self._redis_client = redis_client
        self.ttl = ttl or settings.MATCH_CACHE_TTL

    @property
    def redis(self) -> RedisClient:
        """Get Redis client, lazy-loading if needed."""
        if self._redis_client is None:
            self._redis_client = get_redis()
        return self._redis_client

    def _make_key(self, description: str) -> str:
        """
        Create cache key from description.

        Uses MD5 hash of lowercase normalized description for
        consistent, fixed-length keys.

        Args:
            description: Normalized description

        Returns:
            Cache key string
        """
        desc_lower = description.lower().strip()
        hash_value = hashlib.md5(desc_lower.encode('utf-8')).hexdigest()
        return f"{self.CACHE_PREFIX}{hash_value}"

    def get(self, description: str) -> Optional[Dict[str, Any]]:
        """
        Get cached match for a description.

        Args:
            description: Normalized description to look up

        Returns:
            Dict with master_id, work_code, description if found, None otherwise
        """
        key = self._make_key(description)
        try:
            cached = self.redis.get(key)
            if cached:
                logger.debug(f"Cache hit for: {description[:50]}...")
                return cached
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    def set(
        self,
        description: str,
        master_id: int,
        work_code: str,
        master_description: str = None
    ) -> bool:
        """
        Cache an exact match.

        Args:
            description: Normalized description (key)
            master_id: Master item ID
            work_code: Master work code
            master_description: Original master description

        Returns:
            True if cached successfully
        """
        key = self._make_key(description)
        value = {
            'master_id': master_id,
            'work_code': work_code,
            'description': master_description or description,
        }

        try:
            return self.redis.set(key, value, expire=self.ttl)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def get_batch(self, descriptions: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get cached matches for multiple descriptions.

        Args:
            descriptions: List of normalized descriptions

        Returns:
            Dict mapping description -> cached value (or None if not found)
        """
        results = {}
        for desc in descriptions:
            results[desc] = self.get(desc)
        return results

    def set_batch(self, items: List[Dict[str, Any]]) -> int:
        """
        Cache multiple matches.

        Args:
            items: List of dicts with keys: description, master_id, work_code

        Returns:
            Number of successfully cached items
        """
        count = 0
        for item in items:
            success = self.set(
                description=item['description'],
                master_id=item['master_id'],
                work_code=item['work_code'],
                master_description=item.get('master_description')
            )
            if success:
                count += 1
        return count

    def warm_cache(self, master_items: List[Any]) -> int:
        """
        Warm the cache with master items.

        Args:
            master_items: List of MasterWorkItem objects

        Returns:
            Number of items cached
        """
        logger.info(f"Warming exact match cache with {len(master_items)} items")
        count = 0

        for item in master_items:
            if item.description_normalized:
                success = self.set(
                    description=item.description_normalized,
                    master_id=item.master_id,
                    work_code=item.work_code,
                    master_description=item.description
                )
                if success:
                    count += 1

        logger.info(f"Cached {count} items in exact match cache")
        return count

    def delete(self, description: str) -> bool:
        """
        Delete a cached match.

        Args:
            description: Normalized description

        Returns:
            True if deleted
        """
        key = self._make_key(description)
        try:
            return self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    def clear_all(self) -> int:
        """
        Clear all exact match cache entries.

        Returns:
            Number of entries cleared
        """
        try:
            return self.redis.clear_pattern(f"{self.CACHE_PREFIX}*")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0

    def is_available(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.redis.ping()
        except Exception:
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'prefix': self.CACHE_PREFIX,
            'ttl': self.ttl,
            'redis_available': self.is_available(),
        }


# Module-level singleton
_exact_match_cache: Optional[ExactMatchCache] = None


def get_exact_match_cache() -> ExactMatchCache:
    """Get or create singleton ExactMatchCache instance."""
    global _exact_match_cache
    if _exact_match_cache is None:
        _exact_match_cache = ExactMatchCache()
    return _exact_match_cache
