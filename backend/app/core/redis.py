from redis import Redis
from typing import Optional, Any
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for caching"""
    
    def __init__(self):
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration"""
        try:
            serialized = json.dumps(value)
            self.redis.setex(key, expire, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis CLEAR_PATTERN error for pattern {pattern}: {e}")
            return 0
    
    def ping(self) -> bool:
        """Check if Redis is alive"""
        try:
            return self.redis.ping()
        except Exception as e:
            logger.error(f"Redis PING error: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Dependency to get Redis client"""
    return redis_client
