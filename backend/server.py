import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, APIRouter
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

# Import sync functions for scheduler
from services.sync import sync_all_suppliers, sync_all_woocommerce_stores

# Initialize scheduler
scheduler = AsyncIOScheduler()


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


# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
