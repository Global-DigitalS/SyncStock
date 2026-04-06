"""
Order management routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from typing import List, Optional
from datetime import datetime, timezone
import logging
import hmac
import hashlib

from services.auth import get_current_user
from services.database import db
from services.orders.retry_manager import RetryManager
from services.orders.order_sync import (
    update_order_status_from_crm,
    sync_order_to_online_store,
    get_order_sync_status
)

# SECURITY: Rate limiting for webhook endpoints
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ==================== SECURITY: WEBHOOK SIGNATURE VERIFICATION ====================

async def verify_webhook_signature(
    platform: str,
    user_id: str,
    payload_bytes: bytes,
    signature: str
) -> bool:
    """Verify HMAC-SHA256 signature of webhook payload - SECURITY FIX #8

    Args:
        platform: CRM platform (dolibarr, odoo, etc)
        user_id: User ID to find the correct connection
        payload_bytes: Raw request body bytes
        signature: Signature header value (format: "sha256=<hex>")

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Find the connection to get webhook secret
        connection = await db.crm_connections.find_one({
            "user_id": user_id,
            "platform": platform
        })

        if not connection or "webhook_secret" not in connection:
            logger.warning(f"Webhook signature verification failed: no secret for {platform}")
            return False

        webhook_secret = connection["webhook_secret"]

        # Calculate expected signature
        expected_sig = hmac.new(
            webhook_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        # Extract signature from header (format: "sha256=<hex>")
        if not signature.startswith("sha256="):
            logger.warning(f"Invalid signature format: {signature[:20]}...")
            return False

        provided_sig = signature[7:]  # Remove "sha256=" prefix

        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_sig, provided_sig)

        if not is_valid:
            logger.warning(f"Webhook signature mismatch for {platform}")

        return is_valid

    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


@router.get("/orders")
async def get_orders(
    user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """Get user's orders with optional filtering"""
    query = {"userId": user["id"]}

    if status:
        query["status"] = status

    if source:
        query["source"] = source

    orders = await db.orders.find(
        query,
        {"_id": 0}
    ).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)

    total = await db.orders.count_documents(query)

    return {
        "orders": orders,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/orders/{order_id}")
async def get_order(order_id: str, user: dict = Depends(get_current_user)):
    """Get order details"""
    order = await db.orders.find_one({
        "id": order_id,
        "userId": user["id"]
    }, {"_id": 0})

    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    return order


@router.get("/orders/status/failed")
async def get_failed_orders(
    user: dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """Get orders with errors"""
    query = {
        "userId": user["id"],
        "status": "error"
    }

    orders = await db.orders.find(
        query,
        {"_id": 0}
    ).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)

    total = await db.orders.count_documents(query)

    return {
        "failed_orders": orders,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/orders/status/summary")
async def get_orders_summary(user: dict = Depends(get_current_user)):
    """Get orders summary by status"""
    pipeline = [
        {"$match": {"userId": user["id"]}},
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "totalAmount": {"$sum": "$totalAmount"}
            }
        }
    ]

    summary = await db.orders.aggregate(pipeline).to_list(100)

    return {
        "by_status": {item["_id"]: {
            "count": item["count"],
            "totalAmount": item["totalAmount"]
        } for item in summary},
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/orders/{order_id}/retry")
async def retry_order(
    order_id: str,
    user: dict = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Retry processing a failed order with exponential backoff"""
    order = await db.orders.find_one({
        "id": order_id,
        "userId": user["id"],
        "status": "error"
    }, {"_id": 0})

    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado o no está en error")

    # Check if it's time to retry based on exponential backoff
    should_retry, reason = RetryManager.should_retry(order)
    if not should_retry:
        raise HTTPException(
            status_code=429,
            detail=f"No se puede reintentar aún: {reason}"
        )

    # Get original webhook data from order
    webhook_data = order.get("originalWebhookData", {})
    if not webhook_data:
        raise HTTPException(
            status_code=400,
            detail="No se puede reintentar sin datos originales del webhook"
        )

    # Re-process the order
    from services.orders import process_order_webhook

    result = await process_order_webhook(
        webhook_data,
        order.get("source"),
        user["id"],
        order.get("storeId", "")
    )

    # Update order with retry info if it failed again
    if result["status"] == "error":
        retry_count = result.get("retryCount", order.get("retryCount", 0))
        next_retry = result.get("nextRetryAt")

        return {
            "status": "error",
            "message": result.get("message"),
            "order_id": order_id,
            "retryCount": retry_count,
            "nextRetryAt": next_retry,
            "maxRetries": RetryManager.MAX_RETRIES
        }
    else:
        return {
            "status": "success",
            "message": "Pedido procesado exitosamente en el reintento",
            "order_id": result.get("order_id")
        }


@router.get("/orders/stats/by-source")
async def get_orders_by_source(user: dict = Depends(get_current_user)):
    """Get order statistics by source platform"""
    pipeline = [
        {"$match": {"userId": user["id"]}},
        {
            "$group": {
                "_id": "$source",
                "count": {"$sum": 1},
                "completed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                },
                "errors": {
                    "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
                },
                "totalAmount": {"$sum": "$totalAmount"}
            }
        },
        {"$sort": {"count": -1}}
    ]

    stats = await db.orders.aggregate(pipeline).to_list(100)

    return {
        "by_source": {item["_id"]: {
            "count": item["count"],
            "completed": item["completed"],
            "errors": item["errors"],
            "totalAmount": item["totalAmount"],
            "success_rate": (item["completed"] / item["count"] * 100) if item["count"] > 0 else 0
        } for item in stats}
    }


@router.post("/orders/admin/process-retries")
async def process_failed_orders_retries(user: dict = Depends(get_current_user)):
    """
    Process pending retries for failed orders (scheduled job endpoint)
    Only accessible to authenticated users for now, can be restricted to background tasks
    """
    import logging
    logger = logging.getLogger(__name__)

    from services.orders import process_order_webhook

    # Get all failed orders for this user that are eligible for retry
    # SECURITY FIX: Limit unbounded query to prevent OOM
    # Fetch failed orders in batches to prevent memory exhaustion
    MAX_FAILED_ORDERS = 10000  # Process max 10k orders per request

    failed_orders = await db.orders.find(
        {"userId": user["id"], "status": "error"},
        {"_id": 0}
    ).sort("created_at", -1).limit(MAX_FAILED_ORDERS).to_list(MAX_FAILED_ORDERS)

    if len(failed_orders) >= MAX_FAILED_ORDERS:
        logger.warning(f"User {user['id']} has {MAX_FAILED_ORDERS}+ failed orders, capping at {MAX_FAILED_ORDERS}")

    # Filter orders that should be retried
    retryable_orders = RetryManager.get_retryable_orders(failed_orders)

    if not retryable_orders:
        return {
            "status": "success",
            "message": "No hay pedidos listos para reintento",
            "processed": 0,
            "failed": 0
        }

    processed = 0
    failed_count = 0

    for order in retryable_orders:
        try:
            webhook_data = order.get("originalWebhookData", {})
            if not webhook_data:
                logger.warning(f"No webhook data for order {order.get('id')}, skipping")
                continue

            logger.info(f"Retrying order {order.get('id')} (attempt {order.get('retryCount', 0) + 1})")

            result = await process_order_webhook(
                webhook_data,
                order.get("source"),
                user["id"],
                order.get("storeId", "")
            )

            if result["status"] == "success":
                processed += 1
                logger.info(f"Order {order.get('id')} succeeded on retry")
            else:
                failed_count += 1
                logger.warning(f"Order {order.get('id')} failed retry: {result.get('message')}")

        except Exception as e:
            failed_count += 1
            logger.error(f"Error retrying order {order.get('id')}: {e}")

    return {
        "status": "success",
        "message": f"Procesados {processed} reintentos de {len(retryable_orders)} pendientes",
        "processed": processed,
        "failed": failed_count,
        "total_eligible": len(retryable_orders)
    }


# ==================== BIDIRECTIONAL SYNC ====================

@router.post("/orders/{order_id}/sync-status-from-crm")
async def sync_order_status_from_crm(
    order_id: str,
    user: dict = Depends(get_current_user),
    crm_status_data: Optional[dict] = None
):
    """
    Manually trigger status update from CRM for an order

    Body:
    {
        "crm": "dolibarr" | "odoo",
        "status": <crm-specific status>,
        "crm_order_id": <optional>,
        "metadata": {}
    }
    """
    if not crm_status_data:
        raise HTTPException(status_code=400, detail="Se requiere información de estado del CRM")

    success, error = await update_order_status_from_crm(
        order_id,
        user["id"],
        crm_status_data
    )

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {
        "status": "success",
        "message": "Estado actualizado desde CRM",
        "order_id": order_id
    }


@router.post("/orders/{order_id}/sync-to-store")
async def sync_order_to_store(
    order_id: str,
    user: dict = Depends(get_current_user)
):
    """Sync order status to online store"""
    success, error = await sync_order_to_online_store(order_id, user["id"])

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {
        "status": "success",
        "message": "Pedido sincronizado a la tienda",
        "order_id": order_id
    }


@router.get("/orders/{order_id}/sync-status")
async def get_order_sync_status_endpoint(
    order_id: str,
    user: dict = Depends(get_current_user)
):
    """Get bidirectional sync status for an order"""
    status = await get_order_sync_status(order_id, user["id"])

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return status


@router.post("/webhooks/crm/dolibarr/order-status")
@limiter.limit("30/minute")  # SECURITY FIX: Rate limit webhooks (30 per minute per IP)
async def handle_dolibarr_order_webhook(request: Request):
    """
    Webhook endpoint for Dolibarr order status updates

    Expected webhook body:
    {
        "event_type": "order_status_updated",
        "object_type": "order",
        "object_id": <dolibarr_order_id>,
        "user_id": <user_id>,
        "new_status": <status_code>,
        "timestamp": <timestamp>
    }
    """
    try:
        # SECURITY FIX #8: Verify webhook signature first (before parsing)
        payload_bytes = await request.body()
        signature = request.headers.get("X-Webhook-Signature", "")

        payload = await request.json()

        # Parse and validate all fields with safe type conversion
        user_id = payload.get("user_id")
        object_id = payload.get("object_id")
        new_status = payload.get("new_status")

        if not all([user_id, object_id, new_status is not None]):
            logger.warning(f"Invalid webhook payload: missing required fields")
            return {"status": "error", "message": "Invalid payload"}

        # SECURITY FIX #8: Verify HMAC signature
        is_valid = await verify_webhook_signature(
            platform="dolibarr",
            user_id=user_id,
            payload_bytes=payload_bytes,
            signature=signature
        )

        if not is_valid:
            logger.warning(f"Webhook signature verification failed for user {user_id}")
            return {"status": "error", "message": "Invalid webhook signature"}

        # SECURITY FIX: Safe int conversion with error handling
        try:
            crm_order_id = int(object_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid object_id format: {object_id} (not an integer)")
            return {"status": "error", "message": "Invalid payload"}

        try:
            status_code = int(new_status)
        except (ValueError, TypeError):
            logger.warning(f"Invalid status format: {new_status} (not an integer)")
            return {"status": "error", "message": "Invalid payload"}

        # Find order by CRM order ID
        order = await db.orders.find_one({
            "userId": user_id,
            "crmData.dolibarr_order_id": crm_order_id
        })

        if not order:
            return {
                "status": "warning",
                "message": "Order not found for Dolibarr webhook"
            }

        # Update order status
        success, error = await update_order_status_from_crm(
            order["id"],
            user_id,
            {
                "crm": "dolibarr",
                "status": status_code,
                "crm_order_id": crm_order_id
            }
        )

        if success:
            # Sync updated status to online store
            await sync_order_to_online_store(order["id"], user_id)

        return {
            "status": "success" if success else "error",
            "message": error if error else "Order status updated"
        }

    except Exception as e:
        # SECURITY FIX: Don't expose exception details to client
        logger.error(f"Error handling Dolibarr webhook: {type(e).__name__}: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "Internal server error"
        }


@router.post("/webhooks/crm/odoo/order-status")
@limiter.limit("30/minute")  # SECURITY FIX: Rate limit webhooks (30 per minute per IP)
async def handle_odoo_order_webhook(request: Request):
    """
    Webhook endpoint for Odoo order status updates

    Expected webhook body:
    {
        "event_type": "sale_order_status_changed",
        "object_type": "sale.order",
        "object_id": <odoo_order_id>,
        "user_id": <user_id>,
        "state": <order_state>,
        "timestamp": <timestamp>
    }
    """
    try:
        # SECURITY FIX #8: Verify webhook signature first (before parsing)
        payload_bytes = await request.body()
        signature = request.headers.get("X-Webhook-Signature", "")

        payload = await request.json()

        # Parse and validate all fields with safe type conversion
        user_id = payload.get("user_id")
        object_id = payload.get("object_id")
        state = payload.get("state")

        if not all([user_id, object_id, state]):
            logger.warning(f"Invalid webhook payload: missing required fields")
            return {"status": "error", "message": "Invalid payload"}

        # SECURITY FIX #8: Verify HMAC signature
        is_valid = await verify_webhook_signature(
            platform="odoo",
            user_id=user_id,
            payload_bytes=payload_bytes,
            signature=signature
        )

        if not is_valid:
            logger.warning(f"Webhook signature verification failed for user {user_id}")
            return {"status": "error", "message": "Invalid webhook signature"}

        # SECURITY FIX: Safe int conversion with error handling
        try:
            crm_order_id = int(object_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid object_id format: {object_id} (not an integer)")
            return {"status": "error", "message": "Invalid payload"}

        # Find order by CRM order ID
        order = await db.orders.find_one({
            "userId": user_id,
            "crmData.odoo_order_id": crm_order_id
        })

        if not order:
            return {
                "status": "warning",
                "message": "Order not found for Odoo webhook"
            }

        # Update order status
        success, error = await update_order_status_from_crm(
            order["id"],
            user_id,
            {
                "crm": "odoo",
                "status": state,
                "crm_order_id": crm_order_id
            }
        )

        if success:
            # Sync updated status to online store
            await sync_order_to_online_store(order["id"], user_id)

        return {
            "status": "success" if success else "error",
            "message": error if error else "Order status updated"
        }

    except Exception as e:
        # SECURITY FIX: Don't expose exception details to client
        logger.error(f"Error handling Odoo webhook: {type(e).__name__}: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "Internal server error"
        }
