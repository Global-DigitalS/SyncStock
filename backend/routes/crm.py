"""
CRM Integration Routes
Thin route handlers — business logic lives in services/crm_clients.py and services/crm_sync.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import uuid
import logging
import asyncio
import secrets

from services.database import db
from services.auth import get_current_user
from services.crm_clients import create_crm_client, FULL_SYNC_PLATFORMS, BASIC_SYNC_PLATFORMS
from services.crm_sync import run_sync_in_background

router = APIRouter()
logger = logging.getLogger(__name__)

# Registry to prevent background tasks from being garbage-collected
_background_tasks: set = set()


# ==================== CRM ENDPOINTS ====================

@router.get("/crm/auto-sync-permissions")
async def get_crm_auto_sync_permissions(user: dict = Depends(get_current_user)):
    """Get user's CRM auto-sync permissions based on subscription plan"""
    from services.crm_scheduler import get_user_crm_sync_permission

    permission = await get_user_crm_sync_permission(user["id"])
    return permission


@router.get("/crm/connections")
async def get_crm_connections(user: dict = Depends(get_current_user)):
    """Get all CRM connections for the user"""
    connections = await db.crm_connections.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(100)

    # Batch: obtener último sync job de todas las conexiones de una vez
    if connections:
        conn_ids = [conn["id"] for conn in connections]
        pipeline = [
            {"$match": {"connection_id": {"$in": conn_ids}, "user_id": user["id"]}},
            {"$sort": {"started_at": -1}},
            {"$group": {
                "_id": "$connection_id",
                "status": {"$first": "$status"},
                "current_step": {"$first": "$current_step"}
            }}
        ]
        latest_jobs = {}
        async for job in db.sync_jobs.aggregate(pipeline):
            latest_jobs[job["_id"]] = job

        for conn in connections:
            job = latest_jobs.get(conn["id"])
            conn["last_sync_status"] = job["status"] if job else None
            conn["last_sync_message"] = job["current_step"] if job else None

    return connections


@router.post("/crm/connections")
async def create_crm_connection(request: dict, user: dict = Depends(get_current_user)):
    """Create a new CRM connection"""
    # MEDIUM #11: Validate all inputs
    platform = request.get("platform", "").strip()
    name = request.get("name", "").strip()
    config = request.get("config", {})
    sync_settings = request.get("sync_settings", {})

    # Validate required fields
    if not platform or not isinstance(platform, str):
        raise HTTPException(status_code=400, detail="Plataforma requerida")

    if not config or not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="Configuración requerida y debe ser un objeto")

    if not isinstance(sync_settings, dict):
        raise HTTPException(status_code=400, detail="sync_settings debe ser un objeto")

    # Validate sync_settings contains valid boolean/string values
    valid_sync_keys = {"products", "stock", "prices", "descriptions", "images", "suppliers", "orders"}
    for key in sync_settings:
        if key not in valid_sync_keys:
            raise HTTPException(status_code=400, detail=f"sync_settings contiene clave inválida: {key}")

    # Validate name length
    if len(name) > 255:
        raise HTTPException(status_code=400, detail="El nombre es demasiado largo (máx 255 caracteres)")

    # SECURITY FIX #8: Generate webhook secret for HMAC signature verification
    webhook_secret = secrets.token_urlsafe(32)  # 32 bytes = 256-bit secret

    connection = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "platform": platform,
        "name": name or f"Conexión {platform.capitalize()}",
        "config": config,
        "sync_settings": sync_settings,
        "auto_sync": bool(request.get("auto_sync", False)),
        "auto_sync_interval": request.get("auto_sync_interval", "daily"),
        "status": "active",
        "webhook_secret": webhook_secret,  # SECURITY: Store for HMAC verification
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_sync": None
    }

    await db.crm_connections.insert_one(connection)
    connection.pop("_id", None)

    # Return webhook URL for admin to configure in CRM
    webhook_url = f"/webhooks/crm/{platform}/order-status"
    connection["webhook_url"] = webhook_url
    connection["webhook_secret"] = webhook_secret  # Include in response for setup
    logger.info(f"Created CRM connection with webhook secret for {platform}")

    return connection


@router.put("/crm/connections/{connection_id}")
async def update_crm_connection(connection_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Update a CRM connection"""
    connection = await db.crm_connections.find_one({
        "id": connection_id,
        "user_id": user["id"]
    })

    if not connection:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")

    update_data = {}
    for field in ["name", "config", "sync_settings", "auto_sync", "auto_sync_interval", "status"]:
        if field in request:
            update_data[field] = request[field]

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # CRITICAL FIX: Always include user_id in update filter to prevent cross-user modification
    result = await db.crm_connections.update_one(
        {"id": connection_id, "user_id": user["id"]},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")

    updated = await db.crm_connections.find_one(
        {"id": connection_id, "user_id": user["id"]},
        {"_id": 0}
    )
    return updated


@router.delete("/crm/connections/{connection_id}")
async def delete_crm_connection(connection_id: str, user: dict = Depends(get_current_user)):
    """Delete a CRM connection"""
    result = await db.crm_connections.delete_one({
        "id": connection_id,
        "user_id": user["id"]
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")

    return {"status": "deleted"}


@router.post("/crm/test-connection")
async def test_crm_connection(request: dict, user: dict = Depends(get_current_user)):
    """Test CRM connection with provided credentials"""
    # MEDIUM #11 & HIGH #8: Validate input
    platform = request.get("platform", "").strip()
    config = request.get("config", {})

    # Validate platform
    if not platform or not isinstance(platform, str):
        raise HTTPException(status_code=400, detail="Platform requerida")

    # Validate config is dict
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="Config debe ser un objeto")

    # Validate required config fields based on platform
    required_fields = {
        "dolibarr": ["api_url", "api_key"],
        "odoo": ["api_url", "api_token"]
    }

    if platform in required_fields:
        missing = [f for f in required_fields[platform] if not config.get(f)]
        if missing:
            raise HTTPException(status_code=400, detail=f"Campos requeridos: {', '.join(missing)}")

    client = None
    try:
        client = create_crm_client(platform, config)
        if not client:
            raise HTTPException(status_code=400, detail=f"Plataforma no soportada: {platform}")

        try:
            result = client.test_connection()
            return result
        except TimeoutError:
            return {"status": "error", "message": "Timeout al conectar con CRM"}
        except Exception as e:
            # HIGH: Don't expose internal API structure in error messages
            logger.error(f"Test connection error for {platform}: {e}")
            return {"status": "error", "message": "No se pudo conectar con el CRM"}
    finally:
        if client:
            try:
                client.close()
            except Exception as e:
                logger.warning(f"Error closing test client: {e}")


@router.post("/crm/connections/{connection_id}/sync")
async def sync_crm_connection(connection_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Sync data with a CRM - runs in background with progress tracking"""
    connection = await db.crm_connections.find_one({
        "id": connection_id,
        "user_id": user["id"]
    })

    if not connection:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")

    sync_type = request.get("sync_type", "all")
    catalog_id = request.get("catalog_id")
    platform = connection["platform"]
    config = connection["config"]
    sync_settings = connection.get("sync_settings", {})

    # Create sync job for progress tracking
    sync_job_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    sync_job = {
        "id": sync_job_id,
        "user_id": user["id"],
        "connection_id": connection_id,
        "status": "running",
        "progress": 0,
        "current_step": "Iniciando sincronización...",
        "total_items": 0,
        "processed_items": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "started_at": started_at,  # MEDIUM #22: Store as variable for validation
        "completed_at": None
    }
    await db.sync_jobs.insert_one(sync_job)

    # MEDIUM #22: Cleanup old sync jobs in background (don't block request)
    try:
        from services.crm_sync import validate_and_cleanup_sync_jobs
        asyncio.create_task(validate_and_cleanup_sync_jobs(user["id"], max_age_days=30))
    except Exception as e:
        logger.warning(f"Could not schedule sync job cleanup: {e}")

    # Run sync in background task with timeout protection (1 hour max)
    # HIGH: Wrap in timeout to prevent indefinite hanging
    async def sync_with_timeout():
        try:
            return await asyncio.wait_for(
                run_sync_in_background(
                    sync_job_id=sync_job_id,
                    user_id=user["id"],
                    connection_id=connection_id,
                    platform=platform,
                    config=config,
                    sync_settings=sync_settings,
                    sync_type=sync_type,
                    catalog_id=catalog_id
                ),
                timeout=3600  # 1 hour max
            )
        except asyncio.TimeoutError:
            logger.error(f"Sync job {sync_job_id} exceeded 1 hour timeout")
            try:
                await db.sync_jobs.update_one(
                    {"id": sync_job_id},
                    {"$set": {
                        "status": "error",
                        "current_step": "Sincronización excedió el tiempo máximo (1 hora)",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            except Exception as e:
                logger.error(f"Failed to update sync_job on timeout: {e}")

    task = asyncio.create_task(sync_with_timeout())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    # Return immediately with job ID
    return {
        "status": "started",
        "sync_job_id": sync_job_id,
        "message": "Sincronización iniciada en segundo plano"
    }


@router.get("/crm/sync-jobs/{job_id}")
async def get_sync_job_status(job_id: str, user: dict = Depends(get_current_user)):
    """Get the status of a sync job for progress tracking"""
    job = await db.sync_jobs.find_one(
        {"id": job_id, "user_id": user["id"]},
        {"_id": 0}
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    return job


@router.get("/crm/connections/{connection_id}/orders")
async def get_synced_orders(connection_id: str, user: dict = Depends(get_current_user)):
    """Get orders synced from stores"""
    orders = await db.crm_synced_orders.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("synced_at", -1).to_list(100)

    return orders


# ==================== MONITORING & ANALYTICS ====================

@router.get("/crm/statistics/{sync_job_id}")
async def get_sync_statistics(sync_job_id: str, user: dict = Depends(get_current_user)):
    """Get detailed statistics for a completed sync job - OPTIMIZATION"""
    # First verify the sync job belongs to the user
    job = await db.sync_jobs.find_one(
        {"id": sync_job_id, "user_id": user["id"]},
        {"_id": 0}
    )

    if not job:
        raise HTTPException(status_code=404, detail="Sync job no encontrado")

    # Get statistics for this job
    stats = await db.sync_statistics.find_one(
        {"sync_job_id": sync_job_id},
        {"_id": 0}
    )

    if not stats:
        return {
            "sync_job_id": sync_job_id,
            "message": "Statistics not yet recorded",
            "status": job.get("status")
        }

    return stats


@router.get("/crm/statistics")
async def get_recent_sync_statistics(user: dict = Depends(get_current_user), limit: int = 10):
    """Get recent sync statistics for user - OPTIMIZATION

    Returns the latest N sync operations with performance metrics.
    Useful for monitoring sync trends and identifying performance issues.
    """
    if limit < 1 or limit > 100:
        limit = 10

    stats = await db.sync_statistics.find(
        {},
        {"_id": 0}
    ).sort("recorded_at", -1).to_list(limit)

    if not stats:
        return {
            "message": "No sync statistics available",
            "count": 0,
            "statistics": []
        }

    # Calculate aggregate metrics
    total_duration = sum(s.get("duration_seconds", 0) for s in stats)
    total_processed = sum(s.get("products_processed", 0) for s in stats)
    total_created = sum(s.get("products_created", 0) for s in stats)
    total_updated = sum(s.get("products_updated", 0) for s in stats)
    total_errors = sum(s.get("error_count", 0) for s in stats)

    return {
        "count": len(stats),
        "statistics": stats,
        "aggregate_metrics": {
            "total_duration_seconds": round(total_duration, 2),
            "total_products_processed": total_processed,
            "total_created": total_created,
            "total_updated": total_updated,
            "total_errors": total_errors,
            "average_duration_seconds": round(total_duration / len(stats), 2) if stats else 0,
            "average_products_per_sync": round(total_processed / len(stats), 2) if stats else 0
        }
    }


@router.get("/crm/statistics/platform/{platform}")
async def get_platform_statistics(platform: str, user: dict = Depends(get_current_user), days: int = 30):
    """Get performance statistics for a specific CRM platform - OPTIMIZATION

    Shows trends, success rates, and performance metrics for a platform.
    Helps identify patterns and potential issues.
    """
    if days < 1 or days > 365:
        days = 30

    # Calculate cutoff date
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Get stats for platform in the time range
    stats = await db.sync_statistics.find(
        {
            "platform": platform.lower(),
            "recorded_at": {"$gte": cutoff.isoformat()}
        },
        {"_id": 0}
    ).sort("recorded_at", -1).to_list(1000)

    if not stats:
        return {
            "platform": platform,
            "days": days,
            "message": "No statistics available for this platform in the specified time range",
            "count": 0
        }

    # Calculate metrics
    success_count = sum(1 for s in stats if s.get("success", False))
    error_count = len(stats) - success_count
    total_duration = sum(s.get("duration_seconds", 0) for s in stats)
    total_processed = sum(s.get("products_processed", 0) for s in stats)
    total_errors = sum(s.get("error_count", 0) for s in stats)

    # Find slowest and fastest syncs
    slowest = max(stats, key=lambda s: s.get("duration_seconds", 0)) if stats else None
    fastest = min(stats, key=lambda s: s.get("duration_seconds", float('inf'))) if stats else None

    return {
        "platform": platform,
        "days": days,
        "count": len(stats),
        "success_rate_percent": round((success_count / len(stats) * 100), 2) if stats else 0,
        "metrics": {
            "total_syncs": len(stats),
            "successful_syncs": success_count,
            "failed_syncs": error_count,
            "total_duration_seconds": round(total_duration, 2),
            "total_products_processed": total_processed,
            "total_errors": total_errors,
            "average_duration_seconds": round(total_duration / len(stats), 2) if stats else 0,
            "average_products_per_sync": round(total_processed / len(stats), 2) if stats else 0,
            "slowest_sync_seconds": slowest.get("duration_seconds", 0) if slowest else 0,
            "fastest_sync_seconds": fastest.get("duration_seconds", 0) if fastest else 0,
        },
        "recent_statistics": stats[:5]  # Return 5 most recent for detail
    }
