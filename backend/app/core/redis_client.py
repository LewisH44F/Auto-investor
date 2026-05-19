"""Redis connection pool, helpers, and cache decorator."""

from __future__ import annotations

import functools
import json
from typing import Any, Callable, Optional, TypeVar
from collections.abc import Awaitable

import redis.asyncio as aioredis
from loguru import logger

from app.core.config import settings

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])

_pool: Optional[aioredis.ConnectionPool] = None
_client: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    """Initialise the global Redis connection pool."""
    global _pool, _client
    _pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=20,
        decode_responses=True,
    )
    _client = aioredis.Redis(connection_pool=_pool)
    await _client.ping()
    logger.info("Redis connected: {}", settings.REDIS_URL)


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _client, _pool
    if _client:
        await _client.aclose()
    if _pool:
        await _pool.aclose()
    logger.info("Redis connection closed.")


def get_redis() -> aioredis.Redis:
    """Return the shared Redis client (must call init_redis first)."""
    if _client is None:
        raise RuntimeError("Redis has not been initialised. Call init_redis() first.")
    return _client


# ── Typed helpers ─────────────────────────────────────────────────────────────

async def cache_get(key: str) -> Optional[Any]:
    """Retrieve a JSON-encoded value from Redis."""
    try:
        client = get_redis()
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Redis cache_get error for key '{}': {}", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int = settings.REDIS_CACHE_TTL) -> bool:
    """Store a JSON-encoded value in Redis with an optional TTL (seconds)."""
    try:
        client = get_redis()
        serialized = json.dumps(value, default=str)
        await client.set(key, serialized, ex=ttl)
        return True
    except Exception as exc:
        logger.warning("Redis cache_set error for key '{}': {}", key, exc)
        return False


async def cache_delete(key: str) -> bool:
    """Delete a key from Redis."""
    try:
        client = get_redis()
        await client.delete(key)
        return True
    except Exception as exc:
        logger.warning("Redis cache_delete error for key '{}': {}", key, exc)
        return False


async def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a glob pattern. Returns number deleted."""
    try:
        client = get_redis()
        keys = [k async for k in client.scan_iter(match=pattern)]
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as exc:
        logger.warning("Redis cache_delete_pattern error '{}': {}", pattern, exc)
        return 0


async def cache_exists(key: str) -> bool:
    """Check whether a key exists in Redis."""
    try:
        client = get_redis()
        return bool(await client.exists(key))
    except Exception:
        return False


async def cache_increment(key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
    """Atomically increment an integer counter."""
    try:
        client = get_redis()
        val = await client.incrby(key, amount)
        if ttl and val == amount:  # first time set expiry
            await client.expire(key, ttl)
        return val
    except Exception:
        return 0


# ── Cache decorator ───────────────────────────────────────────────────────────

def cached(key_prefix: str, ttl: int = settings.REDIS_CACHE_TTL) -> Callable[[F], F]:
    """
    Async function cache decorator.

    Usage::

        @cached("stock:price", ttl=60)
        async def get_price(ticker: str) -> dict:
            ...

    The cache key is built as  ``<key_prefix>:<arg0>:<arg1>...``
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            parts = [key_prefix] + [str(a) for a in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
            cache_key = ":".join(parts)

            cached_val = await cache_get(cache_key)
            if cached_val is not None:
                logger.debug("Cache HIT: {}", cache_key)
                return cached_val

            result = await func(*args, **kwargs)
            if result is not None:
                await cache_set(cache_key, result, ttl=ttl)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
