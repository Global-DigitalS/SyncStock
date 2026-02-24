import os
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import route modules
from routes.auth import router as auth_router
from routes.suppliers import router as suppliers_router
from routes.products import router as products_router
from routes.catalogs import router as catalogs_router
from routes.woocommerce import router as woocommerce_router
from routes.dashboard import router as dashboard_router
from routes.subscriptions import router as subscriptions_router
from routes.stores import router as stores_router

# Import sync functions for scheduler
from services.sync import sync_all_suppliers, sync_all_woocommerce_stores

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
    scheduler.add_job(sync_all_suppliers, 'interval', hours=6, id='sync_suppliers', replace_existing=True)
    scheduler.add_job(sync_all_woocommerce_stores, 'interval', hours=12, id='sync_woocommerce', replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started - Supplier sync every 6 hours, WooCommerce price/stock sync every 12 hours")
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(title="SupplierSync Pro", lifespan=lifespan)

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


# Health check endpoint
@api_router.get("/health")
async def health_check():
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

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
