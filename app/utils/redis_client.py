import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    """Return (and lazily create) the shared Redis client."""
    global _redis
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            await _redis.ping()
        except Exception as exc:
            logger.warning("Redis unavailable (%s). Caching and rate-limiting disabled.", exc)
            _redis = None
    return _redis


async def cache_get(key: str) -> Optional[Any]:
    client = await get_redis()
    if client is None:
        return None
    try:
        value = await client.get(key)
        return json.loads(value) if value else None
    except Exception as exc:
        logger.warning("cache_get error for key=%s: %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    client = await get_redis()
    if client is None:
        return
    try:
        await client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("cache_set error for key=%s: %s", key, exc)


async def cache_delete(key: str) -> None:
    client = await get_redis()
    if client is None:
        return
    try:
        await client.delete(key)
    except Exception as exc:
        logger.warning("cache_delete error for key=%s: %s", key, exc)


async def cache_delete_pattern(pattern: str) -> None:
    client = await get_redis()
    if client is None:
        return
    try:
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
    except Exception as exc:
        logger.warning("cache_delete_pattern error for pattern=%s: %s", pattern, exc)
