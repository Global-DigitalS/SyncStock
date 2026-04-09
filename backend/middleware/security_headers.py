from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security HTTP headers to every API response.

    CSP note (MDN):
    - This middleware protects API (JSON) responses.  The React SPA is served
      by Nginx which applies its own, richer CSP for HTML/JS/CSS (see
      scripts/nginx_config_plesk.conf).
    - API endpoints don't render HTML, so `default-src 'none'` is the correct
      baseline per MDN's "start with the most restrictive policy" guidance.
    - `frame-ancestors 'none'` supersedes the deprecated X-Frame-Options header
      (kept for older user agents that don't support CSP Level 2).
    - `upgrade-insecure-requests` instructs the browser to upgrade any HTTP
      sub-resource requests to HTTPS before fetching.
    - `report-uri` / `report-to`: violation reports are sent to the dedicated
      endpoint POST /api/csp-report which logs them server-side.
    """

    _REPORT_URI = "/api/csp-report"

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # --- Transport Security ---
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

        # --- Framing ---
        response.headers["X-Frame-Options"] = "DENY"

        # --- Sniffing / Content ---
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # --- Content Security Policy (API responses) ---
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "img-src 'self'; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "form-action 'none'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests; "
            f"report-uri {self._REPORT_URI}"
        )

        response.headers["Reporting-Endpoints"] = (
            f'csp-endpoint="{self._REPORT_URI}"'
        )

        return response
