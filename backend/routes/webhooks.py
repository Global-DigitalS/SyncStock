"""
Webhook System for Store Integrations
Allows stores to notify the app about inventory/order changes
"""
import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from services.auth import get_current_user
from services.database import db

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


# ==================== WEBHOOK CONFIGURATION ====================

@router.get("/webhooks/configs")
async def get_webhook_configs(user: dict = Depends(get_current_user)):
    """Get webhook configurations for user's stores"""
    configs = await db.webhook_configs.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(100)

    # Get store names
    store_ids = [c.get("store_id") for c in configs if c.get("store_id")]
    stores = {}
    if store_ids:
        store_docs = await db.woocommerce_configs.find({"id": {"$in": store_ids}}).to_list(100)
        stores = {s["id"]: s.get("name") for s in store_docs}

    for config in configs:
        config["store_name"] = stores.get(config.get("store_id"))
        # Mask secret key
        if config.get("secret_key"):
            config["secret_key_masked"] = config["secret_key"][:8] + "..." + config["secret_key"][-4:]
            del config["secret_key"]

    return configs


@router.post("/webhooks/configs")
async def create_webhook_config(config: dict, user: dict = Depends(get_current_user)):
    """Create a webhook configuration for a store"""
    store_id = config.get("store_id")

    # Verify store exists and belongs to user
    store = await db.woocommerce_configs.find_one({"id": store_id, "user_id": user["id"]})
    if not store:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")

    # Generate webhook secret with cryptographically secure random bytes
    secret_key = secrets.token_urlsafe(48)

    config_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    webhook_config = {
        "id": config_id,
        "user_id": user["id"],
        "store_id": store_id,
        "platform": store.get("platform", "woocommerce"),
        "secret_key": secret_key,
        "enabled": config.get("enabled", True),
        "events": config.get("events", ["inventory.updated", "order.created", "product.updated"]),
        "webhook_url": f"/api/webhooks/receive/{config_id}",
        "created_at": now,
        "last_received": None,
        "total_received": 0
    }

    await db.webhook_configs.insert_one(webhook_config)

    return {
        "id": config_id,
        "store_id": store_id,
        "store_name": store.get("name"),
        "platform": store.get("platform"),
        "webhook_url": webhook_config["webhook_url"],
        "secret_key": secret_key,  # Only shown once on creation
        "enabled": webhook_config["enabled"],
        "events": webhook_config["events"],
        "created_at": now,
        "message": "Webhook creado. Configura esta URL en tu tienda para recibir notificaciones."
    }


@router.put("/webhooks/configs/{config_id}")
async def update_webhook_config(config_id: str, update: dict, user: dict = Depends(get_current_user)):
    """Update webhook configuration"""
    existing = await db.webhook_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Configuración de webhook no encontrada")

    update_data = {}
    if "enabled" in update:
        update_data["enabled"] = update["enabled"]
    if "events" in update:
        update_data["events"] = update["events"]

    if update_data:
        await db.webhook_configs.update_one({"id": config_id}, {"$set": update_data})

    return {"message": "Webhook actualizado"}


@router.delete("/webhooks/configs/{config_id}")
async def delete_webhook_config(config_id: str, user: dict = Depends(get_current_user)):
    """Delete webhook configuration"""
    result = await db.webhook_configs.delete_one({"id": config_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return {"message": "Webhook eliminado"}


@router.post("/webhooks/configs/{config_id}/regenerate-secret")
async def regenerate_webhook_secret(config_id: str, user: dict = Depends(get_current_user)):
    """Regenerate webhook secret key"""
    existing = await db.webhook_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    new_secret = secrets.token_urlsafe(48)
    await db.webhook_configs.update_one({"id": config_id}, {"$set": {"secret_key": new_secret}})

    return {"secret_key": new_secret, "message": "Secret regenerado. Actualiza la configuración en tu tienda."}


# ==================== WEBHOOK RECEIVER ====================

def verify_webhook_signature(payload: bytes, signature: str, secret: str, platform: str) -> bool:
    """Verify webhook signature based on platform using constant-time comparison."""
    if not signature or not secret:
        return False
    try:
        if platform in ("woocommerce", "shopify"):
            # WooCommerce and Shopify both use HMAC-SHA256 hex digest
            expected = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)

        elif platform == "prestashop":
            # PrestaShop uses HMAC-SHA256 (not simple concatenation)
            expected = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)

        else:
            # Unknown platform: use HMAC-SHA256 as default
            expected = hmac.new(
                secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected)

    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


async def process_webhook_event(webhook_config: dict, event_type: str, data: dict):
    """Process incoming webhook event"""
    platform = webhook_config.get("platform", "woocommerce")
    store_id = webhook_config.get("store_id")
    user_id = webhook_config.get("user_id")

    now = datetime.now(UTC).isoformat()

    # Log the webhook event
    event_log = {
        "id": str(uuid.uuid4()),
        "webhook_config_id": webhook_config["id"],
        "store_id": store_id,
        "user_id": user_id,
        "platform": platform,
        "event_type": event_type,
        "data": data,
        "processed": False,
        "created_at": now
    }
    await db.webhook_events.insert_one(event_log)

    # Update webhook config stats
    await db.webhook_configs.update_one(
        {"id": webhook_config["id"]},
        {
            "$set": {"last_received": now},
            "$inc": {"total_received": 1}
        }
    )

    try:
        # Process based on event type
        if event_type in ["inventory.updated", "stock.updated", "product.stock_changed"]:
            await process_inventory_update(user_id, store_id, platform, data)

        elif event_type in ["order.created", "order.completed"]:
            await process_order_event(user_id, store_id, platform, data)

        elif event_type in ["product.updated", "product.created"]:
            await process_product_update(user_id, store_id, platform, data)

        # Mark as processed
        await db.webhook_events.update_one(
            {"id": event_log["id"]},
            {"$set": {"processed": True, "processed_at": datetime.now(UTC).isoformat()}}
        )

        # Create notification
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "type": "webhook_received",
            "message": f"Evento recibido de tienda: {event_type}",
            "product_id": data.get("product_id") or data.get("sku"),
            "product_name": data.get("product_name") or data.get("name"),
            "user_id": user_id,
            "read": False,
            "created_at": now
        })

    except Exception as e:
        logger.error(f"Error processing webhook event: {e}")
        await db.webhook_events.update_one(
            {"id": event_log["id"]},
            {"$set": {"error": str(e)}}
        )


async def process_inventory_update(user_id: str, store_id: str, platform: str, data: dict):
    """Process inventory update from webhook"""
    sku = data.get("sku") or data.get("product_sku") or data.get("id")
    new_quantity = data.get("quantity") or data.get("stock_quantity") or data.get("available")

    if not sku:
        logger.warning("Inventory update without SKU")
        return

    # Find matching product in our database
    product = await db.products.find_one({"user_id": user_id, "sku": sku})

    if product:
        old_stock = product.get("stock", 0)

        # Update product stock
        await db.products.update_one(
            {"id": product["id"]},
            {"$set": {
                "external_stock": new_quantity,
                "stock_sync_source": store_id,
                "stock_synced_at": datetime.now(UTC).isoformat()
            }}
        )

        logger.info(f"Updated stock for {sku}: {old_stock} -> {new_quantity}")


async def process_order_event(user_id: str, store_id: str, platform: str, data: dict):
    """Process order event from webhook - enhanced with CRM sync"""
    from services.orders import process_order_webhook

    order_id = data.get("order_id") or data.get("id")
    items = data.get("line_items") or data.get("items") or []

    logger.info(f"Order event received: {order_id} with {len(items)} items from {platform}")

    # Use new order service to process the order
    result = await process_order_webhook(data, platform, user_id, store_id)

    # Log based on result
    if result["status"] == "success":
        logger.info(f"Order processed successfully: {result.get('order_id')}")

        # Create notification
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "type": "order_processed",
            "message": f"Pedido #{order_id} procesado y sincronizado con CRM",
            "order_id": result.get("order_id"),
            "user_id": user_id,
            "read": False,
            "created_at": datetime.now(UTC).isoformat()
        })
    elif result["status"] == "duplicate":
        logger.warning(f"Duplicate order detected: {order_id}")
    else:
        logger.error(f"Failed to process order: {result.get('message')}")

        # Create error notification
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "type": "order_error",
            "message": f"Error procesando pedido #{order_id}: {result.get('message')}",
            "order_id": order_id,
            "user_id": user_id,
            "read": False,
            "created_at": datetime.now(UTC).isoformat()
        })


async def process_product_update(user_id: str, store_id: str, platform: str, data: dict):
    """Process product update from webhook"""
    sku = data.get("sku") or data.get("id")
    price = data.get("price") or data.get("regular_price")

    if not sku:
        return

    # Find matching product
    product = await db.products.find_one({"user_id": user_id, "sku": sku})

    if product and price:
        old_price = product.get("price", 0)
        try:
            new_price = float(price)
            if old_price != new_price:
                # Log price change
                await db.price_history.insert_one({
                    "id": str(uuid.uuid4()),
                    "product_id": product["id"],
                    "old_price": old_price,
                    "new_price": new_price,
                    "change_percent": ((new_price - old_price) / old_price * 100) if old_price else 0,
                    "source": f"webhook_{platform}",
                    "user_id": user_id,
                    "created_at": datetime.now(UTC).isoformat()
                })
        except (ValueError, TypeError):
            pass


@router.post("/webhooks/receive/{config_id}")
@limiter.limit("60/minute")
async def receive_webhook(config_id: str, request: Request, background_tasks: BackgroundTasks):
    """Receive webhook from external store"""
    # Get webhook config (no auth required for webhook endpoints)
    webhook_config = await db.webhook_configs.find_one({"id": config_id})
    if not webhook_config:
        raise HTTPException(status_code=404, detail="Webhook no encontrado")

    if not webhook_config.get("enabled", True):
        return {"status": "ignored", "message": "Webhook deshabilitado"}

    # Get request body
    body = await request.body()

    # Verify signature — reject if secret is configured but signature is missing or invalid
    signature = (
        request.headers.get("X-Webhook-Signature")
        or request.headers.get("X-WC-Webhook-Signature")
        or request.headers.get("X-Shopify-Hmac-SHA256")
    )
    secret_key = webhook_config.get("secret_key")
    if secret_key:
        if not signature:
            logger.warning(f"Webhook {config_id}: cabecera de firma ausente")
            raise HTTPException(status_code=401, detail="Firma de webhook requerida")
        if not verify_webhook_signature(body, signature, secret_key, webhook_config.get("platform", "")):
            logger.warning(f"Webhook {config_id}: firma inválida")
            raise HTTPException(status_code=401, detail="Firma de webhook inválida")

    # Parse body
    try:
        data = await request.json()
    except Exception:
        data = {"raw": body.decode() if body else ""}

    # Determine event type
    event_type = request.headers.get("X-WC-Webhook-Topic") or \
                 request.headers.get("X-Shopify-Topic") or \
                 data.get("event") or \
                 data.get("type") or \
                 "unknown"

    # Process in background
    background_tasks.add_task(process_webhook_event, webhook_config, event_type, data)

    return {"status": "received", "event": event_type}


# ==================== WEBHOOK LOGS ====================

@router.get("/webhooks/events")
async def get_webhook_events(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    store_id: str | None = None
):
    """Get webhook event logs"""
    query = {"user_id": user["id"]}
    if store_id:
        query["store_id"] = store_id

    events = await db.webhook_events.find(
        query,
        {"_id": 0, "data": 0}  # Exclude large data field
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return events


@router.get("/webhooks/stats")
async def get_webhook_stats(user: dict = Depends(get_current_user)):
    """Get webhook statistics"""
    # Count by event type
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_type = await db.webhook_events.aggregate(pipeline).to_list(100)

    # Count by store
    pipeline_store = [
        {"$match": {"user_id": user["id"]}},
        {"$group": {"_id": "$store_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_store = await db.webhook_events.aggregate(pipeline_store).to_list(100)

    # Get store names
    store_ids = [s["_id"] for s in by_store if s["_id"]]
    stores = {}
    if store_ids:
        store_docs = await db.woocommerce_configs.find({"id": {"$in": store_ids}}).to_list(100)
        stores = {s["id"]: s.get("name") for s in store_docs}

    total = await db.webhook_events.count_documents({"user_id": user["id"]})
    processed = await db.webhook_events.count_documents({"user_id": user["id"], "processed": True})

    return {
        "total_events": total,
        "processed": processed,
        "pending": total - processed,
        "by_event_type": {e["_id"]: e["count"] for e in by_type},
        "by_store": [{"store_id": s["_id"], "store_name": stores.get(s["_id"]), "count": s["count"]} for s in by_store]
    }
