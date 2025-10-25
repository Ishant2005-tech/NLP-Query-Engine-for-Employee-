import redis.asyncio as redis
from typing import Optional, Any, Dict
import json
import logging
from functools import wraps
from .config import settings
from redis import asyncio as aioredis


logger = logging.getLogger(__name__)

class SmartCache:
    def __init__(self, use_redis: bool = False, redis_url: str = "redis://localhost:6379"):
        self.use_redis = use_redis      # Important!
        self.redis_url = redis_url
        self.client = None

    async def connect(self):
        if not self.use_redis:
            print("Using in-memory cache")
            return
        print("Connecting to Redis...")
        self.client = aioredis.from_url(self.redis_url)
        await self.client.ping()  # Raises exception if Redis is not available
        print("Connected to Redis!")

    async def close(self):
        if self.client:
            await self.client.close()
            print("Redis connection closed")

# Create cache instance
cache = SmartCache(use_redis=False)  # Change to True if you have Redis running

# Global cache instance


def cached(prefix: str, ttl: int = None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache.cache_key(prefix, *args, **kwargs)
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache HIT: {cache_key[:16]}...")
                return cached_result
            
            # Execute function
            logger.info(f"Cache MISS: {cache_key[:16]}...")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator