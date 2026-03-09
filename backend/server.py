import os
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await ensure_indexes()
    # Legacy scheduled syncs (fallback for users without unified config)
    scheduler.add_job(sync_all_suppliers, 'interval', hours=6, id='sync_suppliers_legacy', replace_existing=True)
    scheduler.add_job(sync_all_woocommerce_stores, 'interval', hours=12, id='sync_woocommerce_legacy', replace_existing=True)
    # Unified sync scheduler - runs every hour to check user-configured syncs
    scheduler.add_job(run_scheduled_syncs, 'interval', hours=1, id='unified_sync', replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started - Unified sync check every 1h, Legacy: Suppliers 6h, WooCommerce 12h")
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(title="SupplierSync Pro", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    allow_credentials=True,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
