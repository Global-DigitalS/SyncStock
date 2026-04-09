from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double-submit cookie CSRF protection.
    For state-changing methods (POST, PUT, DELETE, PATCH), verifies that
    the X-CSRF-Token header matches the csrf_token cookie.
    Exempt paths: auth endpoints (login/register/refresh need to work without prior CSRF),
    webhooks, Stripe webhooks, and CSP reports.
    """
    _EXEMPT_PREFIXES = (
        "/api/auth/login", "/api/auth/register", "/api/auth/refresh",
        "/api/auth/forgot-password", "/api/auth/reset-password",
        "/api/webhooks", "/api/stripe/webhook", "/api/stripe/create-checkout-new-user",
        "/api/stripe/checkout-status", "/api/csp-report",
        "/api/setup",
    )
    _MUTATING_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

    async def dispatch(self, request: Request, call_next):
        if request.method in self._MUTATING_METHODS:
            path = request.url.path
            if not any(path.startswith(p) for p in self._EXEMPT_PREFIXES):
                cookie_token = request.cookies.get("csrf_token")
                header_token = request.headers.get("x-csrf-token")
                if not cookie_token or not header_token or cookie_token != header_token:
                    return Response(
                        content='{"detail":"Token CSRF inválido"}',
                        status_code=403,
                        media_type="application/json",
                    )
        return await call_next(request)
