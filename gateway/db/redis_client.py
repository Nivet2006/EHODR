import logging
import redis.asyncio as aioredis
from gateway.config import settings
from typing import Optional

logger = logging.getLogger(__name__)

class RedisClientManager:
    """
    Asynchronous Redis client interface manager.
    Exposes caching and rate-limiting helper utilities.
    """
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None

    def connect(self):
        """
        Initializes the asynchronous Redis connection pool.
        """
        if not self.client:
            logger.info("Initializing async Redis client pool...")
            self.client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5.0
            )

    async def disconnect(self):
        """
        Gracefully closes connection resources.
        """
        if self.client:
            logger.info("Closing async Redis client connections...")
            await self.client.aclose()
            self.client = None

    async def get(self, key: str) -> Optional[str]:
        """
        Fetches a string value from Redis. Fails open on connection failures.
        """
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.warning(f"Redis get operation failure (failing open): {e}")
            return None

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """
        Persists a value in cache with an explicit expiration TTL.
        """
        if not self.client:
            return False
        try:
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Redis setex operation failure: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Invalidates a given key path from the cache layer.
        """
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete operation failure: {e}")
            return False

    async def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Redis sliding/fixed-window request limit counter.
        Increments request keys and blocks if count exceeds boundaries.
        Returns: True if request is ALLOWED, False if RATE LIMITED.
        """
        if not self.client:
            return True # Fail open: do not block users if Redis is offline
        try:
            # Multi-transaction script to increment counter and apply key TTL
            pipe = self.client.pipeline()
            await pipe.incr(key)
            await pipe.expire(key, window_seconds, nx=True) # Apply TTL only on initial increment
            results = await pipe.execute()
            
            current_count = results[0]
            if current_count > max_requests:
                return False
            return True
        except Exception as e:
            logger.warning(f"Redis rate limiter exception (failing open): {e}")
            return True

    async def is_healthy(self) -> bool:
        """
        Performs a database ping test.
        """
        if not self.client:
            return False
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

# Export unified singleton manager
redis_manager = RedisClientManager()
