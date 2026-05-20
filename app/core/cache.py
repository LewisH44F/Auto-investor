"""Thread-safe in-memory cache replacing Redis for zero-setup local execution."""

from __future__ import annotations

import threading
import time
from functools import wraps
from typing import Any, Optional


class InMemoryCache:
    """Simple TTL-based in-memory cache with thread safety."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._store:
                value, expires_at = self._store[key]
                if expires_at == 0 or time.time() < expires_at:
                    return value
                del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        expires_at = time.time() + ttl if ttl > 0 else 0
        with self._lock:
            self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys containing the pattern (after stripping *)."""
        fragment = pattern.replace("*", "")
        with self._lock:
            keys = [k for k in self._store if fragment in k]
            for k in keys:
                del self._store[k]
        return len(keys)

    def clear_all(self) -> None:
        with self._lock:
            self._store.clear()

    # ── Async wrappers (same thread, non-blocking) ────────────────────────────

    async def aget(self, key: str) -> Optional[Any]:
        return self.get(key)

    async def aset(self, key: str, value: Any, ttl: int = 300) -> None:
        self.set(key, value, ttl)

    async def adelete(self, key: str) -> None:
        self.delete(key)

    async def aclear_pattern(self, pattern: str) -> int:
        return self.clear_pattern(pattern)


# Singleton cache instance
cache = InMemoryCache()


def cached(ttl: int = 300, key_prefix: str = "") -> Any:
    """Async function cache decorator using the in-memory cache."""
    def decorator(func: Any) -> Any:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{key_prefix or func.__name__}:{args}:{sorted(kwargs.items())}"
            result = cache.get(key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator
