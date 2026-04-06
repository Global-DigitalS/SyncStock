"""
Structured error monitoring and request logging.

Provides JSON-formatted logs for production observability,
compatible with log aggregators (ELK, CloudWatch, Datadog, etc.).
"""

import json
import logging
import time
import traceback
from datetime import UTC, datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("syncstock.monitor")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with structured data:
    - method, path, status_code, duration_ms
    - client IP, user_agent
    - Errors logged with full traceback
    """

    _SKIP_PATHS = {"/health", "/api/health", "/ws/"}

    async def dispatch(self, request: Request, call_next):
        # Skip health checks and WebSocket upgrades for noise reduction
        path = request.url.path
        if any(path.startswith(p) for p in self._SKIP_PATHS):
            return await call_next(request)

        start = time.monotonic()
        client_ip = getattr(request.client, "host", "unknown")

        try:
            response = await call_next(request)
            duration_ms = round((time.monotonic() - start) * 1000, 1)

            log_data = {
                "event": "request",
                "method": request.method,
                "path": path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "ip": client_ip,
            }

            if response.status_code >= 500:
                logger.error(json.dumps(log_data))
            elif response.status_code >= 400:
                logger.warning(json.dumps(log_data))
            elif duration_ms > 5000:
                log_data["slow"] = True
                logger.warning(json.dumps(log_data))

            return response

        except Exception as exc:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            error_data = {
                "event": "unhandled_error",
                "method": request.method,
                "path": path,
                "duration_ms": duration_ms,
                "ip": client_ip,
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now(UTC).isoformat(),
            }
            logger.error(json.dumps(error_data))
            raise


class ErrorAggregator:
    """
    Tracks error counts and recent errors in memory for the admin dashboard.
    Keeps last N errors per endpoint for quick debugging.
    """

    def __init__(self, max_recent: int = 50):
        self._max_recent = max_recent
        self._recent_errors: list[dict] = []
        self._error_counts: dict[str, int] = {}

    def record_error(self, path: str, method: str, status: int, detail: str):
        """Record an error occurrence."""
        key = f"{method} {path}"
        self._error_counts[key] = self._error_counts.get(key, 0) + 1

        self._recent_errors.append({
            "path": path,
            "method": method,
            "status": status,
            "detail": detail[:200],
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Trim to max
        if len(self._recent_errors) > self._max_recent:
            self._recent_errors = self._recent_errors[-self._max_recent:]

    def get_summary(self) -> dict:
        """Return error summary for monitoring dashboard."""
        return {
            "total_errors": sum(self._error_counts.values()),
            "by_endpoint": dict(sorted(
                self._error_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:20]),
            "recent": self._recent_errors[-10:],
        }

    def reset(self):
        """Clear all tracked errors."""
        self._recent_errors.clear()
        self._error_counts.clear()


# Singleton
error_aggregator = ErrorAggregator()
