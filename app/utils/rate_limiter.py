import logging
from fastapi import Request, HTTPException, status

from app.utils.redis_client import get_redis
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def rate_limit(request: Request) -> None:
    """FastAPI dependency — raises 429 if the IP has exceeded the configured rate."""
    client_ip = request.client.host if request.client else "unknown"
    redis_key = f"rate_limit:{client_ip}"

    client = await get_redis()
    if client is None:
        return

    try:
        count = await client.incr(redis_key)
        if count == 1:
            await client.expire(redis_key, settings.rate_limit_window)

        if count > settings.rate_limit_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded. Max {settings.rate_limit_requests} requests "
                    f"per {settings.rate_limit_window} seconds."
                ),
            )
    except HTTPException:
        raise
    except Exception as exc:
        # On unexpected Redis error, allow the request through
        logger.warning("Rate limiter error for ip=%s: %s", client_ip, exc)
