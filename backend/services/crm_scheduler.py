"""
CRM Scheduler Service
Handles automatic scheduled synchronization with CRM systems
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from services.database import db

logger = logging.getLogger(__name__)


async def get_user_crm_sync_permission(user_id: str) -> dict:
    """
    Check if user's subscription plan allows CRM auto-sync
    Returns dict with enabled status and allowed intervals
    """
    user = await db.users.find_one({"id": user_id})
    if not user:
        return {"enabled": False, "intervals": []}
    
    plan_id = user.get("subscription_plan_id")
    if not plan_id:
        return {"enabled": False, "intervals": []}
    
    plan = await db.subscription_plans.find_one({"id": plan_id})
    if not plan:
        return {"enabled": False, "intervals": []}
    
    return {
        "enabled": plan.get("crm_sync_enabled", False),
        "intervals": plan.get("crm_sync_intervals", [])
    }


async def sync_crm_connection(connection_id: str) -> dict:
    """
    Execute sync for a single CRM connection
    """
    from routes.crm import DolibarrClient, sync_products_to_dolibarr, sync_suppliers_to_dolibarr, sync_orders_to_dolibarr
    
    connection = await db.crm_connections.find_one({"id": connection_id})
    if not connection:
        return {"status": "error", "message": "Connection not found"}
    
    if not connection.get("is_connected"):
        return {"status": "error", "message": "Connection not active"}
    
    user_id = connection.get("user_id")
    platform = connection.get("platform")
    config = connection.get("config", {})
    sync_settings = connection.get("sync_settings", {})
    
    results = {
        "products": None,
        "suppliers": None,
        "orders": None
    }
    
    try:
        if platform == "dolibarr":
            client = DolibarrClient(
                api_url=config.get("api_url", ""),
                api_key=config.get("api_key", "")
            )
            
            # Test connection first
            test_result = client.test_connection()
            if test_result["status"] != "success":
                await db.crm_connections.update_one(
                    {"id": connection_id},
                    {"$set": {
                        "last_sync_error": test_result.get("message"),
                        "last_sync_attempt": datetime.now(timezone.utc).isoformat()
                    }}
                )
                return {"status": "error", "message": test_result.get("message")}
            
            # Sync products
            if sync_settings.get("products", True):
                results["products"] = await sync_products_to_dolibarr(client, user_id, sync_settings)
            
            # Sync suppliers
            if sync_settings.get("suppliers", True):
                results["suppliers"] = await sync_suppliers_to_dolibarr(client, user_id)
            
            # Sync orders
            if sync_settings.get("orders", True):
                results["orders"] = await sync_orders_to_dolibarr(client, user_id)
            
            # Update last sync time
            await db.crm_connections.update_one(
                {"id": connection_id},
                {"$set": {
                    "last_sync": datetime.now(timezone.utc).isoformat(),
                    "last_sync_error": None,
                    "last_sync_results": results
                }}
            )
            
            logger.info(f"CRM sync completed for connection {connection_id}: {results}")
            return {"status": "success", "results": results}
        
        return {"status": "error", "message": f"Unknown platform: {platform}"}
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"CRM sync error for connection {connection_id}: {error_msg}")
        
        await db.crm_connections.update_one(
            {"id": connection_id},
            {"$set": {
                "last_sync_error": error_msg,
                "last_sync_attempt": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"status": "error", "message": error_msg}


async def run_scheduled_crm_syncs():
    """
    Main scheduler function - runs periodically to check and execute due syncs
    Called by APScheduler every hour
    """
    logger.info("Running scheduled CRM syncs check...")
    
    now = datetime.now(timezone.utc)
    
    # Find all connections with auto_sync enabled
    connections = await db.crm_connections.find({
        "auto_sync_enabled": True,
        "is_connected": True
    }).to_list(1000)
    
    synced_count = 0
    error_count = 0
    
    for connection in connections:
        try:
            connection_id = connection.get("id")
            user_id = connection.get("user_id")
            sync_interval = connection.get("auto_sync_interval", 24)  # Default 24 hours
            last_sync = connection.get("last_sync")
            
            # Check if user's plan allows this sync
            permission = await get_user_crm_sync_permission(user_id)
            if not permission["enabled"]:
                logger.debug(f"User {user_id} plan doesn't allow CRM auto-sync")
                continue
            
            if sync_interval not in permission["intervals"]:
                logger.debug(f"Interval {sync_interval}h not allowed for user {user_id}")
                continue
            
            # Check if it's time to sync
            should_sync = False
            if not last_sync:
                should_sync = True
            else:
                try:
                    last_sync_dt = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
                    hours_since_sync = (now - last_sync_dt).total_seconds() / 3600
                    should_sync = hours_since_sync >= sync_interval
                except:
                    should_sync = True
            
            if should_sync:
                logger.info(f"Executing scheduled sync for CRM connection {connection_id}")
                result = await sync_crm_connection(connection_id)
                
                if result["status"] == "success":
                    synced_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Sync failed for {connection_id}: {result.get('message')}")
        
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing CRM connection {connection.get('id')}: {e}")
    
    logger.info(f"Scheduled CRM syncs completed: {synced_count} synced, {error_count} errors")
    return {"synced": synced_count, "errors": error_count}
