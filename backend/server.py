import os
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Import route modules
from routes.auth import router as auth_router
from routes.suppliers import router as suppliers_router
from routes.products import router as products_router
from routes.catalogs import router as catalogs_router
from routes.woocommerce import router as woocommerce_router
from routes.dashboard import router as dashboard_router
from routes.subscriptions import router as subscriptions_router
from routes.stores import router as stores_router
from routes.webhooks import router as webhooks_router
from routes.setup import router as setup_router
from routes.email import router as email_router
from routes.admin import router as admin_router
from routes.stripe import router as stripe_router
from routes.crm import router as crm_router
from routes.support import router as support_router

# Import sync functions for scheduler
from services.sync import sync_all_suppliers, sync_all_woocommerce_stores
from services.crm_scheduler import run_scheduled_crm_syncs
from services.unified_sync import run_scheduled_syncs
from services.database import ensure_indexes

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize scheduler
scheduler = AsyncIOScheduler()


# ==================== WEBSOCKET MANAGER ====================

class ConnectionManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> set of websockets
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")
                    disconnected.add(connection)
            # Clean up disconnected
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)


# Global connection manager
ws_manager = ConnectionManager()


async def _purge_expired_security_records():
    """Scheduled job: remove expired password-reset tokens and stale login-attempt records."""
    from datetime import datetime, timezone
    from services.database import db as _db
    now = datetime.now(timezone.utc).isoformat()
    result_tokens = await _db.password_resets.delete_many({"expires_at": {"$lt": now}})
    result_attempts = await _db.login_attempts.delete_many({"last_attempt": {"$lt": now}})
    logger.info(
        f"Security purge: eliminados {result_tokens.deleted_count} tokens expirados, "
        f"{result_attempts.deleted_count} registros de intentos caducados"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await ensure_indexes()
    except Exception as e:
        logger.warning(f"No se pudieron crear los índices de MongoDB (continuando sin ellos): {e}")
    # Legacy scheduled syncs (fallback for users without unified config)
    scheduler.add_job(sync_all_suppliers, 'interval', hours=6, id='sync_suppliers_legacy', replace_existing=True)
    scheduler.add_job(sync_all_woocommerce_stores, 'interval', hours=12, id='sync_woocommerce_legacy', replace_existing=True)
    # Unified sync scheduler - runs every hour to check user-configured syncs
    scheduler.add_job(run_scheduled_syncs, 'interval', hours=1, id='unified_sync', replace_existing=True)
    # Security maintenance: purge expired password-reset tokens and old login-attempt records
    scheduler.add_job(_purge_expired_security_records, 'interval', hours=6, id='security_purge', replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started - Unified sync check every 1h, Legacy: Suppliers 6h, WooCommerce 12h, Security purge 6h")
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(title="SyncStock", lifespan=lifespan)
app.state.limiter = limiter


async def _logged_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Log rate-limit violations before delegating to the default SlowAPI handler (OWASP A09)."""
    logger.warning(
        "Rate limit exceeded | ip=%s path=%s limit=%s",
        getattr(request.client, "host", "?"),
        request.url.path,
        exc.detail,
    )
    return await _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(RateLimitExceeded, _logged_rate_limit_handler)

# Main API router with /api prefix
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(auth_router)
api_router.include_router(suppliers_router)
api_router.include_router(products_router)
api_router.include_router(catalogs_router)
api_router.include_router(woocommerce_router)
api_router.include_router(dashboard_router)
api_router.include_router(subscriptions_router)
api_router.include_router(stores_router)
api_router.include_router(webhooks_router)
api_router.include_router(setup_router)
api_router.include_router(email_router)
api_router.include_router(admin_router)
api_router.include_router(stripe_router)
api_router.include_router(crm_router)
api_router.include_router(support_router)


# Health check endpoint under /api
@api_router.get("/health")
async def api_health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# Root-level health check for Kubernetes deployment
@app.get("/health")
async def health_check():
    """Health check endpoint at root level for Kubernetes liveness/readiness probes"""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# WebSocket endpoint for real-time notifications
@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: str):
    # Authenticate before accepting the connection.
    # The JWT token is expected as a query parameter: ?token=<jwt>
    # (browsers cannot set custom headers on WebSocket connections).
    from services.auth import JWT_SECRET, JWT_ALGORITHM
    import jwt as _jwt

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    try:
        payload = _jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_user_id = payload.get("user_id")
    except _jwt.InvalidTokenError:
        await websocket.close(code=4001)
        return

    # Prevent a user from subscribing to another user's notification stream
    if token_user_id != user_id:
        await websocket.close(code=4003)
        return

    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive, listen for pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, user_id)


app.include_router(api_router)

# Mount static files for uploads (logos, favicons, hero images)
# Using /api/uploads to ensure proper routing through ingress
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ==================== CSP VIOLATION REPORTING ====================

@app.post("/api/csp-report")
async def csp_report(request: Request):
    """
    Receive Content-Security-Policy violation reports from browsers.
    Browsers POST a JSON body with a 'csp-report' key (CSP Level 2)
    or a flat object (Reporting API / report-to).
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    report = body.get("csp-report", body)
    logger.warning(
        "CSP violation | blocked-uri=%s | violated-directive=%s | document-uri=%s",
        report.get("blocked-uri", "?"),
        report.get("violated-directive", "?"),
        report.get("document-uri", "?"),
    )
    return Response(status_code=204)

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

    # Build the Reporting-Endpoints / Report-To header value once at class level.
    _REPORT_URI = "/api/csp-report"

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # --- Transport Security ---
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )

        # --- Framing (CSP frame-ancestors + legacy X-Frame-Options) ---
        # X-Frame-Options kept for browsers without CSP Level 2 support
        response.headers["X-Frame-Options"] = "DENY"

        # --- Sniffing / Content ---
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # --- Content Security Policy (API responses) ---
        # Per MDN: for resources that do not serve HTML, use 'none' as the
        # default and only open what is strictly necessary.
        response.headers["Content-Security-Policy"] = (
            # Fetch directives
            "default-src 'none'; "
            # API responses serve images from /api/uploads — allow same-origin
            "img-src 'self'; "
            # No scripts, styles, fonts or frames needed on API JSON responses
            "object-src 'none'; "
            # Navigation / document directives
            "base-uri 'none'; "
            "form-action 'none'; "
            # Navigation directive: prevent embedding in any frame (MDN §frame-ancestors)
            "frame-ancestors 'none'; "
            # Instructs browsers to upgrade HTTP sub-resources to HTTPS (MDN §upgrade-insecure-requests)
            "upgrade-insecure-requests; "
            # Violation reporting — report-uri (CSP Level 2, broad support) +
            # Reporting-Endpoints header (CSP Level 3, future-proof)
            f"report-uri {self._REPORT_URI}"
        )

        # Reporting API v1 endpoint declaration (CSP Level 3 / MDN §report-to)
        response.headers["Reporting-Endpoints"] = (
            f'csp-endpoint="{self._REPORT_URI}"'
        )

        return response


app.add_middleware(SecurityHeadersMiddleware)

_cors_origins_env = os.environ.get('CORS_ORIGINS', '')
if not _cors_origins_env or _cors_origins_env.strip() == '*':
    logger.warning(
        "CORS_ORIGINS no está configurado o usa '*'. "
        "Define orígenes explícitos en producción (ej: CORS_ORIGINS=https://app.tudominio.com)"
    )
    _cors_origins = ["*"]
else:
    _cors_origins = [o.strip() for o in _cors_origins_env.split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=_cors_origins != ["*"],
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
