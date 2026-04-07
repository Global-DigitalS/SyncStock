"""
Unified Sync Scheduler Service
Handles automatic scheduled synchronization for all services:
- Suppliers (catalog data from FTP/URL)
- Stores (WooCommerce, PrestaShop, Shopify, Magento, Wix)
- CRM (Dolibarr)

SEQUENTIAL EXECUTION: Only 1 sync process runs at a time on the server
to avoid overloading the server. Suppliers, stores, and CRM sync one by one.
"""
import asyncio
import logging
from datetime import UTC, datetime
from typing import Optional

from services.database import db

logger = logging.getLogger(__name__)

# Global semaphore: only 1 sync process at a time on the entire server
_global_sync_lock = asyncio.Semaphore(1)

# Available sync intervals in hours
SYNC_INTERVALS = [1, 6, 12, 24]


async def get_user_sync_settings(user_id: str) -> dict:
    """
    Get user's sync settings including allowed intervals from subscription plan
    """
    user = await db.users.find_one({"id": user_id})
    if not user:
        return {
            "enabled": False,
            "intervals": [],
            "current_interval": None,
            "sync_suppliers": True,
            "sync_stores": True,
            "sync_crm": True
        }

    # Get user's current sync config
    sync_config = user.get("sync_config", {})

    # Get plan permissions
    plan_id = user.get("subscription_plan_id")
    allowed_intervals = []
    sync_enabled = False

    if plan_id:
        plan = await db.subscription_plans.find_one({"id": plan_id})
        if plan:
            sync_enabled = plan.get("auto_sync_enabled", False)
            allowed_intervals = plan.get("sync_intervals", plan.get("crm_sync_intervals", []))

    return {
        "enabled": sync_enabled,
        "intervals": allowed_intervals,
        "current_interval": sync_config.get("interval", None),
        "last_sync": sync_config.get("last_sync"),
        "next_sync": sync_config.get("next_sync")
    }


async def update_user_sync_settings(user_id: str, settings: dict) -> dict:
    """
    Update user's sync configuration
    """
    # Validate interval
    user = await db.users.find_one({"id": user_id})
    if not user:
        return {"status": "error", "message": "Usuario no encontrado"}

    # Get allowed intervals from plan
    plan_id = user.get("subscription_plan_id")
    allowed_intervals = []
    if plan_id:
        plan = await db.subscription_plans.find_one({"id": plan_id})
        if plan:
            allowed_intervals = plan.get("sync_intervals", plan.get("crm_sync_intervals", []))

    interval = settings.get("interval")
    if interval and interval not in allowed_intervals:
        return {"status": "error", "message": f"Intervalo {interval}h no permitido en tu plan"}

    sync_config = {
        "interval": interval,
        "updated_at": datetime.now(UTC).isoformat()
    }

    # Calculate next sync time
    if interval:
        from datetime import timedelta
        next_sync = datetime.now(UTC) + timedelta(hours=interval)
        sync_config["next_sync"] = next_sync.isoformat()

    await db.users.update_one(
        {"id": user_id},
        {"$set": {"sync_config": sync_config}}
    )

    return {"status": "success", "message": "Configuración actualizada", "config": sync_config}


async def sync_user_suppliers(user_id: str, queue_task: Optional['SyncTask'] = None) -> dict:
    """
    Sync all suppliers for a user, one by one (sequential).
    """
    from services.sync import sync_supplier

    suppliers = await db.suppliers.find({"user_id": user_id}).to_list(100)
    results = {"total": len(suppliers), "synced": 0, "errors": 0, "details": []}

    for supplier in suppliers:
        try:
            await sync_supplier(supplier)
            results["synced"] += 1
            results["details"].append({
                "name": supplier.get("name"),
                "status": "success"
            })

            if queue_task:
                queue_task.progress = {
                    "processed": results["synced"],
                    "total": results["total"],
                    "pct": int((results["synced"] / results["total"]) * 100)
                }
        except Exception as e:
            logger.error(f"Error syncing supplier {supplier.get('name')}: {e}")
            results["errors"] += 1
            results["details"].append({
                "name": supplier.get("name"),
                "status": "error",
                "message": str(e)
            })

    return results


async def sync_user_stores(user_id: str, queue_task: Optional['SyncTask'] = None) -> dict:
    """
    Sync all stores for a user, one by one (sequential).
    """
    from services.sync import sync_woocommerce_store_price_stock

    stores = await db.stores.find({"user_id": user_id, "is_connected": True}).to_list(100)
    results = {"total": len(stores), "synced": 0, "errors": 0, "details": []}

    for store in stores:
        try:
            platform = store.get("platform", "woocommerce")
            if platform == "woocommerce":
                await sync_woocommerce_store_price_stock(store)
            results["synced"] += 1
            results["details"].append({
                "name": store.get("name"),
                "platform": platform,
                "status": "success"
            })

            if queue_task:
                queue_task.progress = {
                    "processed": results["synced"],
                    "total": results["total"],
                    "pct": int((results["synced"] / results["total"]) * 100)
                }
        except Exception as e:
            logger.error(f"Error syncing store {store.get('name')}: {e}")
            results["errors"] += 1
            results["details"].append({
                "name": store.get("name"),
                "platform": store.get("platform"),
                "status": "error",
                "message": str(e)
            })

    return results


async def sync_user_crm(user_id: str, queue_task: Optional['SyncTask'] = None) -> dict:
    """
    Sync all CRM connections for a user, one by one (sequential).
    """
    from services.crm_scheduler import sync_crm_connection

    connections = await db.crm_connections.find({
        "user_id": user_id,
        "is_connected": True
    }).to_list(100)

    results = {"total": len(connections), "synced": 0, "errors": 0, "details": []}

    for conn in connections:
        try:
            result = await sync_crm_connection(conn["id"])
            if result["status"] == "success":
                results["synced"] += 1
                results["details"].append({
                    "name": conn.get("name"),
                    "platform": conn.get("platform"),
                    "status": "success"
                })

                if queue_task:
                    queue_task.progress = {
                        "processed": results["synced"],
                        "total": results["total"],
                        "pct": int((results["synced"] / results["total"]) * 100)
                    }
            else:
                results["errors"] += 1
                results["details"].append({
                    "name": conn.get("name"),
                    "platform": conn.get("platform"),
                    "status": "error",
                    "message": result.get("message")
                })
        except Exception as e:
            logger.error(f"Error syncing CRM {conn.get('name')}: {e}")
            results["errors"] += 1
            results["details"].append({
                "name": conn.get("name"),
                "platform": conn.get("platform"),
                "status": "error",
                "message": str(e)
            })

    return results


async def run_user_sync(user_id: str, queue_task: Optional['SyncTask'] = None) -> dict:
    """
    Run full sync for a user based on their settings.

    SEQUENTIAL: Suppliers → Stores → CRM, one after another.
    Protected by global semaphore so only 1 sync runs at a time on the server.

    Args:
        user_id: User ID to sync
        queue_task: Optional SyncTask for progress tracking
    """
    async with _global_sync_lock:
        logger.info(f"[SYNC] Global lock acquired for user {user_id}")
        settings = await get_user_sync_settings(user_id)

        results = {
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "suppliers": None,
            "stores": None,
            "crm": None
        }

        # Execute sequentially: suppliers → stores → CRM
        logger.info(f"[SYNC] User {user_id}: starting suppliers sync")
        results["suppliers"] = await sync_user_suppliers(user_id, queue_task)
        if results["suppliers"]:
            logger.info(f"User {user_id} suppliers sync: {results['suppliers']['synced']}/{results['suppliers']['total']}")

        logger.info(f"[SYNC] User {user_id}: starting stores sync")
        results["stores"] = await sync_user_stores(user_id, queue_task)
        if results["stores"]:
            logger.info(f"User {user_id} stores sync: {results['stores']['synced']}/{results['stores']['total']}")

        logger.info(f"[SYNC] User {user_id}: starting CRM sync")
        results["crm"] = await sync_user_crm(user_id, queue_task)
        if results["crm"]:
            logger.info(f"User {user_id} crm sync: {results['crm']['synced']}/{results['crm']['total']}")

        # Update last sync time and calculate next sync
        interval = settings.get("current_interval")
        update_data = {
            "sync_config.last_sync": results["timestamp"]
        }

        if interval:
            from datetime import timedelta
            next_sync = datetime.now(UTC) + timedelta(hours=interval)
            update_data["sync_config.next_sync"] = next_sync.isoformat()

        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )

        logger.info(f"[SYNC] Global lock released for user {user_id}")
        return results


async def run_scheduled_syncs():
    """
    Main scheduler function - runs every hour to check and execute due syncs
    Called by APScheduler
    """
    logger.info("Running scheduled sync check...")

    now = datetime.now(UTC)

    # Find all users with auto-sync enabled
    users = await db.users.find({
        "sync_config.interval": {"$exists": True, "$ne": None}
    }).to_list(10000)

    synced_count = 0
    error_count = 0

    for user in users:
        try:
            user_id = user.get("id")
            sync_config = user.get("sync_config", {})
            interval = sync_config.get("interval")
            last_sync = sync_config.get("last_sync")

            if not interval:
                continue

            # Check if user's plan allows this sync
            plan_id = user.get("subscription_plan_id")
            if plan_id:
                plan = await db.subscription_plans.find_one({"id": plan_id})
                if not plan or not plan.get("auto_sync_enabled"):
                    continue
                allowed_intervals = plan.get("sync_intervals", plan.get("crm_sync_intervals", []))
                if interval not in allowed_intervals:
                    continue

            # Check if it's time to sync
            should_sync = False
            if not last_sync:
                should_sync = True
            else:
                try:
                    last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                    hours_since_sync = (now - last_sync_dt).total_seconds() / 3600
                    should_sync = hours_since_sync >= interval
                except:
                    should_sync = True

            if should_sync:
                logger.info(f"Executing scheduled sync for user {user_id} (interval: {interval}h)")
                result = await run_user_sync(user_id)

                # Count results
                total_synced = 0
                total_errors = 0
                for key in ["suppliers", "stores", "crm"]:
                    if result.get(key):
                        total_synced += result[key].get("synced", 0)
                        total_errors += result[key].get("errors", 0)

                if total_errors == 0:
                    synced_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Sync for user {user_id} completed with {total_errors} errors")

        except Exception as e:
            error_count += 1
            logger.error(f"Error processing sync for user {user.get('id')}: {e}")

    logger.info(f"Scheduled syncs completed: {synced_count} users synced, {error_count} with errors")
    return {"synced": synced_count, "errors": error_count}
