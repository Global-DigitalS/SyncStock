import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Import security configuration
from config.cors import CORS_CONFIG, SECURITY_HEADERS

# Import route modules
from routes.admin import router as admin_router
from routes.auth import router as auth_router
from routes.catalogs import router as catalogs_router
from routes.competitors import router as competitors_router
from routes.crm import router as crm_router
from routes.dashboard import router as dashboard_router
from routes.email import router as email_router
from routes.marketplaces import router as marketplaces_router
from routes.orders import router as orders_router
from routes.products import router as products_router
from routes.setup import router as setup_router
from routes.stores import router as stores_router
from routes.stripe import router as stripe_router
from routes.subscriptions import router as subscriptions_router
from routes.suppliers import router as suppliers_router
from routes.support import router as support_router
from routes.webhooks import router as webhooks_router
from routes.woocommerce import router as woocommerce_router
from services.cache import cache
from services.database import ensure_indexes
from services.error_monitor import RequestLoggingMiddleware

# Import sync functions for scheduler
from services.sync import sync_all_suppliers, sync_all_woocommerce_stores
from services.sync_queue import SyncType, get_sync_queue
from services.unified_sync import run_scheduled_syncs

# WebSocket manager (módulo propio)
from websocket.manager import ws_manager

# Middlewares de seguridad (módulo propio)
from middleware import CSRFMiddleware, SecurityHeadersMiddleware, UUIDValidationMiddleware

# Initialize rate limiter with default limits for all endpoints
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    storage_uri="memory://",
)

# Initialize scheduler
scheduler = AsyncIOScheduler()


# ==================== JOBS PROGRAMADOS ====================

async def _purge_expired_security_records():
    """Scheduled job: remove expired password-reset tokens and stale login-attempt records."""
    from services.database import db as _db
    now = datetime.now(UTC).isoformat()
    result_tokens = await _db.password_resets.delete_many({"expires_at": {"$lt": now}})
    result_attempts = await _db.login_attempts.delete_many({"last_attempt": {"$lt": now}})
    logger.info(
        f"Security purge: eliminados {result_tokens.deleted_count} tokens expirados, "
        f"{result_attempts.deleted_count} registros de intentos caducados"
    )


async def _purge_old_database_records():
    """Scheduled job: limpieza de datos antiguos como complemento a los TTL indexes."""
    from datetime import timedelta
    from services.database import db as _db

    now = datetime.now(UTC)
    cutoff_90d = (now - timedelta(days=90)).isoformat()
    cutoff_180d = (now - timedelta(days=180)).isoformat()
    cutoff_30d = (now - timedelta(days=30)).isoformat()

    totals = {}
    try:
        r = await _db.notifications.delete_many({"created_at": {"$lt": cutoff_90d}})
        totals["notifications"] = r.deleted_count
        r = await _db.price_history.delete_many({"created_at": {"$lt": cutoff_180d}})
        totals["price_history"] = r.deleted_count
        r = await _db.price_snapshots.delete_many({"scraped_at": {"$lt": cutoff_90d}})
        totals["price_snapshots"] = r.deleted_count
        r = await _db.sync_history.delete_many({"started_at": {"$lt": cutoff_90d}})
        totals["sync_history"] = r.deleted_count
        r = await _db.sync_status.delete_many({"created_at": {"$lt": cutoff_30d}})
        totals["sync_status"] = r.deleted_count
        r = await _db.sync_jobs.delete_many({"started_at": {"$lt": cutoff_90d}})
        totals["sync_jobs"] = r.deleted_count

        deleted_total = sum(totals.values())
        if deleted_total > 0:
            logger.info(f"DB cleanup: {deleted_total} docs eliminados - {totals}")
        else:
            logger.debug("DB cleanup: sin documentos antiguos que eliminar")
    except Exception as e:
        logger.error(f"Error en limpieza de BD: {e}")


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await ensure_indexes()
    except Exception as e:
        logger.warning(f"No se pudieron crear los índices de MongoDB (continuando sin ellos): {e}")

    queue_manager = get_sync_queue()

    async def sync_supplier_handler(user_id: str, supplier_id: str, task):
        from services.sync import sync_supplier
        supplier = await app.state.db.suppliers.find_one({"id": supplier_id, "user_id": user_id})
        if not supplier:
            raise ValueError(f"Supplier {supplier_id} not found")
        return await sync_supplier(supplier)

    async def sync_store_handler(user_id: str, store_id: str, task):
        from services.sync import sync_woocommerce_store_price_stock
        store = await app.state.db.stores.find_one({"id": store_id, "user_id": user_id})
        if not store:
            raise ValueError(f"Store {store_id} not found")
        return await sync_woocommerce_store_price_stock(store)

    async def sync_crm_handler(user_id: str, connection_id: str, task):
        from services.crm_scheduler import sync_crm_connection
        return await sync_crm_connection(connection_id)

    await queue_manager.register_handler(SyncType.SUPPLIER, sync_supplier_handler)
    await queue_manager.register_handler(SyncType.STORE, sync_store_handler)
    await queue_manager.register_handler(SyncType.CRM, sync_crm_handler)

    await queue_manager.start_worker()
    logger.info("SyncQueueManager initialized and worker started")

    # Scheduled jobs
    scheduler.add_job(sync_all_suppliers, 'interval', hours=6, id='sync_suppliers_legacy', replace_existing=True)
    scheduler.add_job(sync_all_woocommerce_stores, 'interval', hours=12, id='sync_woocommerce_legacy', replace_existing=True)
    scheduler.add_job(run_scheduled_syncs, 'interval', hours=1, id='unified_sync', replace_existing=True)
    scheduler.add_job(_purge_expired_security_records, 'interval', hours=6, id='security_purge', replace_existing=True)
    scheduler.add_job(cache.cleanup_expired, 'interval', minutes=10, id='cache_cleanup', replace_existing=True)
    scheduler.add_job(_purge_old_database_records, 'interval', hours=24, id='db_cleanup', replace_existing=True)
    from services.scrapers.scheduler import run_scheduled_crawls
    scheduler.add_job(run_scheduled_crawls, 'interval', hours=8, id='competitor_crawl', replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started - Unified sync 1h, Legacy: Suppliers 6h, WooCommerce 12h, Security purge 6h, Competitor crawl 8h")

    app.state.sync_queue = queue_manager

    yield

    # Shutdown
    await queue_manager.stop_worker()
    scheduler.shutdown()


# ==================== APP ====================

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
api_router.include_router(orders_router)
api_router.include_router(setup_router)
api_router.include_router(email_router)
api_router.include_router(admin_router)
api_router.include_router(stripe_router)
api_router.include_router(crm_router)
api_router.include_router(support_router)
api_router.include_router(marketplaces_router)
api_router.include_router(competitors_router)


# Health check endpoints
@api_router.get("/health")
async def api_health_check():
    from services.database import get_db
    _health_db = get_db()
    try:
        await _health_db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    status = "ok" if db_status == "connected" else "degraded"
    return {"status": status, "database": db_status, "timestamp": datetime.now(UTC).isoformat()}


@app.get("/health")
async def health_check():
    """Health check endpoint at root level for Kubernetes liveness/readiness probes"""
    from services.database import get_db
    _health_db = get_db()
    try:
        await _health_db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    status = "ok" if db_status == "connected" else "degraded"
    return {"status": status, "database": db_status, "timestamp": datetime.now(UTC).isoformat()}


# ==================== WEBSOCKET ====================

@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint para notificaciones en tiempo real.
    Implementa heartbeat automático para detectar conexiones muertas.
    """
    import jwt as _jwt
    from services.auth import JWT_ALGORITHM, JWT_SECRET

    # Priorizar cookie httpOnly sobre query parameter (más seguro)
    token = websocket.cookies.get("auth_token")
    if not token:
        token = websocket.query_params.get("token")
        if token:
            logger.warning(
                "WebSocket auth via query parameter (inseguro). IP: %s",
                websocket.client.host if websocket.client else "unknown",
            )
    if not token:
        await websocket.close(code=4001)
        return

    try:
        payload = _jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_user_id = payload.get("user_id")
    except _jwt.InvalidTokenError:
        await websocket.close(code=4001)
        return

    if token_user_id != user_id:
        await websocket.close(code=4003)
        return

    await ws_manager.connect(websocket, user_id)

    HEARTBEAT_INTERVAL = 60
    heartbeat_task = None

    async def send_heartbeat():
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                try:
                    await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": time.time()}))
                except Exception as e:
                    logger.debug(f"Error sending heartbeat to {user_id}: {e}")
                    break
        except asyncio.CancelledError:
            pass

    try:
        heartbeat_task = asyncio.create_task(send_heartbeat())

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                if data == "ping":
                    await websocket.send_text("pong")
                continue

            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": time.time()}))
            elif message.get("type") == "heartbeat_ack":
                logger.debug(f"Heartbeat ACK from {user_id}")
            else:
                logger.debug(f"Received message from {user_id}: {message.get('type')}")

    except WebSocketDisconnect:
        logger.info(f"Client {user_id} disconnected normally")
        await ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {e}")
        await ws_manager.disconnect(websocket, user_id)
    finally:
        if heartbeat_task and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass


app.include_router(api_router)

# Mount static files for uploads
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# ==================== CSP VIOLATION REPORTING ====================

@app.post("/api/csp-report")
async def csp_report(request: Request):
    """Receive Content-Security-Policy violation reports from browsers."""
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


# ==================== MIDDLEWARES ====================

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(UUIDValidationMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS Configuration (from config/cors.py)
_environment = os.environ.get('ENVIRONMENT', 'development').lower()
if _environment == 'production' and CORS_CONFIG["allow_origins"] == ["*"]:
    raise RuntimeError(
        "CORS_ORIGINS es obligatorio en producción. "
        "Define CORS_ORIGINS en variables de entorno con orígenes específicos, "
        "ej: CORS_ORIGINS=https://app.tudominio.com"
    )

app.add_middleware(
    CORSMiddleware,
    allow_credentials=CORS_CONFIG["allow_credentials"],
    allow_origins=CORS_CONFIG["allow_origins"],
    allow_methods=CORS_CONFIG["allow_methods"],
    allow_headers=CORS_CONFIG["allow_headers"],
    expose_headers=CORS_CONFIG.get("expose_headers", []),
    max_age=CORS_CONFIG.get("max_age", 600),
)
