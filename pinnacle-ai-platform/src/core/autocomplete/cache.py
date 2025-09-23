"""
Auto-Completion Cache

This module provides a multi-layer caching system for auto-completion results
with Redis as the primary cache and in-memory fallback.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    ttl: int = 300  # 5 minutes default TTL
    hits: int = 0


class AutoCompletionCache:
    """
    Multi-layer caching system for auto-completion results.

    This cache provides:
    - Redis-based distributed caching (primary)
    - In-memory caching (fallback)
    - Cache warming and preloading
    - Automatic cache invalidation
    - Performance monitoring
    """

    def __init__(self, redis_url: str = None, max_memory_items: int = 10000):
        """
        Initialize the cache system.

        Args:
            redis_url: Redis connection URL (optional)
            max_memory_items: Maximum items to store in memory cache
        """
        self.logger = logging.getLogger(__name__)

        # Redis cache (primary)
        self.redis_client = None
        self.redis_url = redis_url or "redis://localhost:6379"
        self._initialize_redis()

        # In-memory cache (fallback)
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.max_memory_items = max_memory_items

        # Cache statistics
        self.stats = {
            "redis_hits": 0,
            "redis_misses": 0,
            "memory_hits": 0,
            "memory_misses": 0,
            "total_requests": 0,
            "cache_size": 0,
            "evictions": 0
        }

        # Cache warming
        self.warmup_tasks: Dict[str, asyncio.Task] = {}

        self.logger.info("AutoCompletionCache initialized")

    def _initialize_redis(self):
        """Initialize Redis connection."""
        if redis is None:
            self.logger.warning("Redis not available, using memory cache only")
            return

        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            asyncio.create_task(self._test_redis_connection())
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None

    async def _test_redis_connection(self):
        """Test Redis connection."""
        if self.redis_client:
            try:
                await self.redis_client.ping()
                self.logger.info("Redis connection established successfully")
            except Exception as e:
                self.logger.error(f"Redis connection test failed: {e}")
                self.redis_client = None

    async def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached auto-completion results.

        Args:
            key: Cache key

        Returns:
            Cached completion results or None if not found
        """
        self.stats["total_requests"] += 1
        start_time = time.time()

        # Try Redis first (primary cache)
        if self.redis_client:
            try:
                redis_data = await self.redis_client.get(f"ac:{key}")
                if redis_data:
                    self.stats["redis_hits"] += 1
                    # Update access metadata
                    await self.redis_client.setex(
                        f"ac_meta:{key}",
                        3600,  # 1 hour TTL for metadata
                        json.dumps({
                            "accessed_at": datetime.utcnow().isoformat(),
                            "access_count": await self._get_redis_access_count(key) + 1
                        })
                    )
                    return json.loads(redis_data)
            except Exception as e:
                self.logger.error(f"Redis get error: {e}")
                self.stats["redis_misses"] += 1

        # Fallback to memory cache
        memory_result = self._get_from_memory(key)
        if memory_result:
            self.stats["memory_hits"] += 1
            return memory_result
        else:
            self.stats["memory_misses"] += 1

        return None

    async def set(self, key: str, data: List[Dict[str, Any]], ttl: int = 300):
        """
        Cache auto-completion results.

        Args:
            key: Cache key
            data: Completion results to cache
            ttl: Time to live in seconds
        """
        start_time = time.time()

        # Store in Redis (primary cache)
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"ac:{key}",
                    ttl,
                    json.dumps(data)
                )
                # Store metadata
                await self.redis_client.setex(
                    f"ac_meta:{key}",
                    ttl + 3600,  # Metadata lives longer
                    json.dumps({
                        "created_at": datetime.utcnow().isoformat(),
                        "ttl": ttl,
                        "data_size": len(json.dumps(data))
                    })
                )
            except Exception as e:
                self.logger.error(f"Redis set error: {e}")

        # Also store in memory cache
        self._set_in_memory(key, data, ttl)

    async def delete(self, key: str):
        """Delete cached entry."""
        # Delete from Redis
        if self.redis_client:
            try:
                await self.redis_client.delete(f"ac:{key}")
                await self.redis_client.delete(f"ac_meta:{key}")
            except Exception as e:
                self.logger.error(f"Redis delete error: {e}")

        # Delete from memory
        self._delete_from_memory(key)

    async def clear(self):
        """Clear all cached entries."""
        # Clear Redis
        if self.redis_client:
            try:
                # Get all keys matching our pattern
                keys = await self.redis_client.keys("ac:*")
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception as e:
                self.logger.error(f"Redis clear error: {e}")

        # Clear memory
        self.memory_cache.clear()
        self.stats["cache_size"] = 0

    def _get_from_memory(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Get data from memory cache."""
        if key not in self.memory_cache:
            return None

        entry = self.memory_cache[key]

        # Check if entry has expired
        if datetime.utcnow() - entry.created_at > timedelta(seconds=entry.ttl):
            del self.memory_cache[key]
            self.stats["cache_size"] = len(self.memory_cache)
            return None

        # Update access metadata
        entry.accessed_at = datetime.utcnow()
        entry.access_count += 1

        return entry.data

    def _set_in_memory(self, key: str, data: List[Dict[str, Any]], ttl: int):
        """Set data in memory cache."""
        # Check if we need to evict items
        if len(self.memory_cache) >= self.max_memory_items:
            self._evict_memory_cache()

        # Create cache entry
        entry = CacheEntry(
            data=data,
            ttl=ttl
        )

        self.memory_cache[key] = entry
        self.stats["cache_size"] = len(self.memory_cache)

    def _delete_from_memory(self, key: str):
        """Delete data from memory cache."""
        if key in self.memory_cache:
            del self.memory_cache[key]
            self.stats["cache_size"] = len(self.memory_cache)

    def _evict_memory_cache(self):
        """Evict least recently used items from memory cache."""
        if not self.memory_cache:
            return

        # Sort by access time and count (LRU with frequency consideration)
        entries = list(self.memory_cache.items())
        entries.sort(key=lambda x: (x[1].accessed_at, x[1].access_count))

        # Remove oldest 20% of entries
        to_remove = max(1, len(entries) // 5)
        for key, _ in entries[:to_remove]:
            del self.memory_cache[key]
            self.stats["evictions"] += 1

        self.stats["cache_size"] = len(self.memory_cache)

    async def _get_redis_access_count(self, key: str) -> int:
        """Get access count from Redis metadata."""
        try:
            meta_data = await self.redis_client.get(f"ac_meta:{key}")
            if meta_data:
                metadata = json.loads(meta_data)
                return metadata.get("access_count", 0)
        except Exception:
            pass
        return 0

    async def warmup(self, keys: List[str]):
        """
        Warm up cache with pre-computed completions.

        Args:
            keys: List of cache keys to warm up
        """
        for key in keys:
            if key not in self.warmup_tasks:
                self.warmup_tasks[key] = asyncio.create_task(self._warmup_key(key))

    async def _warmup_key(self, key: str):
        """Warm up a specific cache key."""
        try:
            # This would typically call the actual completion service
            # For now, we'll just mark it as attempted
            await asyncio.sleep(0.1)  # Simulate some work
            self.logger.debug(f"Cache warmup attempted for key: {key}")
        except Exception as e:
            self.logger.error(f"Cache warmup failed for key {key}: {e}")
        finally:
            self.warmup_tasks.pop(key, None)

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_hits = self.stats["redis_hits"] + self.stats["memory_hits"]
        total_requests = self.stats["total_requests"]

        hit_rate = total_hits / max(total_requests, 1)

        # Get Redis info if available
        redis_info = {}
        if self.redis_client:
            try:
                redis_info = await self.redis_client.info("memory")
            except Exception as e:
                self.logger.error(f"Error getting Redis info: {e}")

        return {
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "redis_hits": self.stats["redis_hits"],
            "redis_misses": self.stats["redis_misses"],
            "memory_hits": self.stats["memory_hits"],
            "memory_misses": self.stats["memory_misses"],
            "cache_size": self.stats["cache_size"],
            "evictions": self.stats["evictions"],
            "redis_available": self.redis_client is not None,
            "memory_items": len(self.memory_cache),
            "redis_info": redis_info,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the cache system."""
        health = {
            "status": "healthy",
            "redis_available": False,
            "memory_available": True,
            "stats": await self.get_stats()
        }

        # Check Redis health
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["redis_available"] = True
            except Exception as e:
                health["status"] = "degraded"
                health["redis_error"] = str(e)

        # Check memory cache health
        if len(self.memory_cache) > self.max_memory_items * 0.9:
            health["status"] = "warning"
            health["memory_warning"] = "Memory cache near capacity"

        return health

    async def cleanup(self):
        """Cleanup expired entries and perform maintenance."""
        # Cleanup memory cache
        expired_keys = []
        now = datetime.utcnow()

        for key, entry in self.memory_cache.items():
            if now - entry.created_at > timedelta(seconds=entry.ttl):
                expired_keys.append(key)

        for key in expired_keys:
            del self.memory_cache[key]

        self.stats["cache_size"] = len(self.memory_cache)

        # Cleanup Redis (if implemented as a separate cleanup task)
        if self.redis_client:
            try:
                # This would typically be done by Redis itself with TTL
                # but we could implement additional cleanup logic here
                pass
            except Exception as e:
                self.logger.error(f"Redis cleanup error: {e}")

    async def shutdown(self):
        """Shutdown the cache system."""
        self.logger.info("Shutting down AutoCompletionCache...")

        # Cancel warmup tasks
        for task in self.warmup_tasks.values():
            task.cancel()

        self.warmup_tasks.clear()

        # Clear caches
        await self.clear()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        self.logger.info("AutoCompletionCache shutdown complete")
