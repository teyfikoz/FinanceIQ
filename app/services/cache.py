"""
Cache Service Module
Provides unified caching interface with Redis backend or in-memory fallback.
"""

import os
import logging
import random
from typing import Any, Optional
from datetime import datetime, timedelta
import pickle
import json

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


class InMemoryCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, max_size: int = 1000):
        self._cache = {}
        self._expiry = {}
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check if expired
        if key in self._expiry:
            if datetime.now() > self._expiry[key]:
                del self._cache[key]
                del self._expiry[key]
                return None

        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL in seconds (with jitter)."""
        # Evict if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        # Add jitter (+/-10%) to TTL to avoid thundering herd
        jitter = random.uniform(0.9, 1.1)
        actual_ttl = int(ttl * jitter)

        self._cache[key] = value
        self._expiry[key] = datetime.now() + timedelta(seconds=actual_ttl)

    def delete(self, key: str):
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]

    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._expiry.clear()

    def _evict_oldest(self):
        """Evict the oldest expired entry or random entry."""
        # First try to evict expired entries
        now = datetime.now()
        expired_keys = [k for k, exp in self._expiry.items() if now > exp]

        if expired_keys:
            key_to_evict = expired_keys[0]
        else:
            # Evict random entry
            key_to_evict = next(iter(self._cache))

        self.delete(key_to_evict)


class RedisCache:
    """Redis-based cache wrapper."""

    def __init__(self, redis_url: str):
        try:
            self.client = redis.from_url(redis_url, decode_responses=False)
            # Test connection
            self.client.ping()
            logger.info(f"Redis cache connected: {redis_url}")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            value = self.client.get(key)
            if value is None:
                return None

            # Try to unpickle (for Python objects)
            try:
                return pickle.loads(value)
            except:
                # Fallback to decode as string
                return value.decode('utf-8') if isinstance(value, bytes) else value

        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in Redis cache with TTL in seconds (with jitter)."""
        try:
            # Add jitter (+/-10%) to TTL to avoid thundering herd
            jitter = random.uniform(0.9, 1.1)
            actual_ttl = int(ttl * jitter)

            # Serialize with pickle
            serialized = pickle.dumps(value)
            self.client.setex(key, actual_ttl, serialized)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")

    def delete(self, key: str):
        """Delete key from Redis cache."""
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")

    def clear(self):
        """Clear all cache (use with caution)."""
        try:
            self.client.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {e}")


# Global cache instance
_cache_instance = None


def get_cache():
    """Get or create cache instance."""
    global _cache_instance

    if _cache_instance is not None:
        return _cache_instance

    # Try Redis first
    redis_url = os.getenv('REDIS_URL')

    if redis_url and REDIS_AVAILABLE:
        try:
            _cache_instance = RedisCache(redis_url)
            return _cache_instance
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache, falling back to in-memory: {e}")

    # Fallback to in-memory cache
    _cache_instance = InMemoryCache(max_size=1000)
    logger.info("Using in-memory cache")

    return _cache_instance


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache (module-level function)."""
    cache = get_cache()
    return cache.get(key)


def cache_set(key: str, value: Any, ttl: int = 3600):
    """Set value in cache (module-level function)."""
    cache = get_cache()
    cache.set(key, value, ttl)


def cache_delete(key: str):
    """Delete key from cache (module-level function)."""
    cache = get_cache()
    cache.delete(key)


def cache_clear():
    """Clear all cache (module-level function)."""
    cache = get_cache()
    cache.clear()


def cache_invalidate(prefix: Optional[str] = None):
    """
    Invalidate cache keys matching prefix.

    Args:
        prefix: Key prefix to match (None = clear all)
    """
    cache = get_cache()

    if prefix is None:
        cache.clear()
        logger.info("Cleared all cache")
        return

    # For Redis, use SCAN to find matching keys
    if isinstance(cache, RedisCache):
        try:
            pattern = f"{prefix}*"
            keys = []
            for key in cache.client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                cache.client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} keys matching '{pattern}'")
        except Exception as e:
            logger.error(f"Redis invalidation error: {e}")

    # For in-memory, iterate and delete matching keys
    elif isinstance(cache, InMemoryCache):
        keys_to_delete = [k for k in cache._cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            cache.delete(key)
        logger.info(f"Invalidated {len(keys_to_delete)} keys from memory")
