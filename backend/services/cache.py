"""
Simple in-memory TTL cache for expensive dashboard queries.

No external dependencies (no Redis needed). Uses asyncio locks for
thread-safe cache access. Suitable for single-process deployments.
"""

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class TTLCache:
    """In-memory cache with per-key TTL expiration."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expires_at)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Return cached value if exists and not expired, else None."""
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 60):
        """Store value with a TTL in seconds."""
        async with self._lock:
            self._store[key] = (value, time.monotonic() + ttl_seconds)

    async def invalidate(self, prefix: str = ""):
        """Remove all keys matching a prefix (or all if empty)."""
        async with self._lock:
            if not prefix:
                self._store.clear()
            else:
                keys_to_delete = [k for k in self._store if k.startswith(prefix)]
                for k in keys_to_delete:
                    del self._store[k]

    async def cleanup_expired(self):
        """Remove all expired entries (called periodically)."""
        async with self._lock:
            now = time.monotonic()
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for k in expired:
                del self._store[k]
            if expired:
                logger.debug(f"Cache cleanup: {len(expired)} entradas expiradas eliminadas")


# Singleton instance
cache = TTLCache()


# Default TTL values (seconds)
DASHBOARD_STATS_TTL = 60       # 1 minuto — datos de usuario
SUPERADMIN_STATS_TTL = 120     # 2 minutos — datos globales (más caros)
SYNC_HISTORY_STATS_TTL = 90    # 1.5 minutos
NOTIFICATION_STATS_TTL = 30    # 30 segundos — cambian más rápido
