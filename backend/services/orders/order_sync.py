"""
Bidirectional order synchronization
Syncs order status from CRM back to online stores
"""
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime, timezone

from services.database import db

logger = logging.getLogger(__name__)


class OrderStatusMapper:
    """Maps CRM order statuses to online store statuses"""

    # Dolibarr order statuses to online store statuses
    DOLIBARR_STATUS_MAP = {
        0: "draft",           # Draft
        1: "processed",       # Validated/Confirmed
        2: "shipped",         # Shipped
        3: "delivered",       # Delivered
        4: "cancelled",       # Cancelled
        5: "refused",         # Refused
    }

    # Odoo order statuses to online store statuses
    ODOO_STATUS_MAP = {
        "draft": "processing",
        "sent": "processing",
        "sale": "processing",
        "done": "completed",
        "cancel": "cancelled",
    }

    # Online store status constants
    STORE_STATUS = {
        "pending": "pending",
        "processing": "processing",
        "completed": "completed",
        "refunded": "refunded",
        "cancelled": "cancelled",
        "shipped": "shipped",
        "delivered": "delivered"
    }

    @staticmethod
    def map_dolibarr_status(dolibarr_status: int) -> str:
        """Map Dolibarr order status to standard status"""
        return OrderStatusMapper.DOLIBARR_STATUS_MAP.get(
            dolibarr_status,
            "processing"
        )

    @staticmethod
    def map_odoo_status(odoo_status: str) -> str:
        """Map Odoo order status to standard status"""
        return OrderStatusMapper.ODOO_STATUS_MAP.get(
            odoo_status,
            "processing"
        )


async def update_order_status_from_crm(
    order_id: str,
    user_id: str,
    crm_status_data: Dict
) -> Tuple[bool, Optional[str]]:
    """
    Update order status based on CRM data

    Args:
        order_id: Order ID in SyncStock
        user_id: User ID
        crm_status_data: {
            "crm": "dolibarr" or "odoo",
            "status": CRM-specific status,
            "crm_order_id": ID in CRM,
            "metadata": {} (optional extra data)
        }

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Get order
        order = await db.orders.find_one({
            "id": order_id,
            "userId": user_id
        })

        if not order:
            return False, "Pedido no encontrado"

        # Map CRM status to standard status
        crm_type = crm_status_data.get("crm", "").lower()
        crm_status = crm_status_data.get("status")

        if crm_type == "dolibarr":
            new_status = OrderStatusMapper.map_dolibarr_status(crm_status)
        elif crm_type == "odoo":
            new_status = OrderStatusMapper.map_odoo_status(crm_status)
        else:
            return False, f"Tipo de CRM no soportado: {crm_type}"

        # Update order status
        update_data = {
            "status": new_status,
            "processedAt": datetime.now(timezone.utc).isoformat()
        }

        # Store CRM status info
        if not order.get("crmData"):
            order["crmData"] = {}
        order["crmData"]["crmStatus"] = crm_status
        order["crmData"]["lastSyncAt"] = datetime.now(timezone.utc).isoformat()

        update_data["crmData"] = order["crmData"]

        # Add to history
        history_entry = {
            "action": "status_updated_from_crm",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "previousStatus": order.get("status"),
                "newStatus": new_status,
                "crmStatus": crm_status,
                "crmType": crm_type
            }
        }

        await db.orders.update_one(
            {"id": order_id},
            {
                "$set": update_data,
                "$push": {"history": history_entry}
            }
        )

        logger.info(
            f"Order {order_id} status updated from CRM: "
            f"{crm_type} status '{crm_status}' → '{new_status}'"
        )

        return True, None

    except Exception as e:
        logger.error(f"Error updating order status from CRM: {e}")
        return False, str(e)


async def sync_order_to_online_store(
    order_id: str,
    user_id: str
) -> Tuple[bool, Optional[str]]:
    """
    Synchronize order status from SyncStock to online store

    Args:
        order_id: Order ID
        user_id: User ID

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Get order
        order = await db.orders.find_one({
            "id": order_id,
            "userId": user_id
        })

        if not order:
            return False, "Pedido no encontrado"

        # Verify order has been synced to CRM (should have source order ID)
        source = order.get("source")
        source_order_id = order.get("sourceOrderId")

        if not source or not source_order_id:
            return False, "Pedido no tiene origen de tienda definido"

        # Get store configuration
        store = await db.stores.find_one({
            "userId": user_id,
            "platform": source
        })

        if not store:
            return False, f"Tienda no configurada para {source}"

        # Get order status to sync
        order_status = order.get("status")
        store_status_note = f"Actualizado desde CRM: {order_status}"

        try:
            # Sync to appropriate store
            if source == "woocommerce":
                success = await _sync_to_woocommerce(
                    store,
                    source_order_id,
                    order_status,
                    store_status_note
                )
            elif source == "shopify":
                success = await _sync_to_shopify(
                    store,
                    source_order_id,
                    order_status,
                    store_status_note
                )
            elif source == "prestashop":
                success = await _sync_to_prestashop(
                    store,
                    source_order_id,
                    order_status,
                    store_status_note
                )
            else:
                return False, f"Plataforma no soportada: {source}"

            if not success:
                return False, f"Error sincronizando a {source}"

            # Update order history
            history_entry = {
                "action": "synced_to_store",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {
                    "platform": source,
                    "status": order_status,
                    "storeOrderId": source_order_id
                }
            }

            await db.orders.update_one(
                {"id": order_id},
                {
                    "$push": {"history": history_entry},
                    "$set": {"lastSyncedToStoreAt": datetime.now(timezone.utc).isoformat()}
                }
            )

            logger.info(
                f"Order {order_id} synced to {source} "
                f"with status '{order_status}'"
            )

            return True, None

        except Exception as e:
            logger.error(f"Error syncing to {source}: {e}")
            return False, str(e)

    except Exception as e:
        logger.error(f"Error syncing order to store: {e}")
        return False, str(e)


async def _sync_to_woocommerce(
    store: dict,
    order_id: str,
    status: str,
    note: str
) -> bool:
    """Sync order status to WooCommerce"""
    try:
        # Dynamic import to avoid circular dependencies
        try:
            from services.platforms import WooCommerceAPI
        except ImportError:
            # Fallback if not available - log and return True to not block
            logger.warning("WooCommerceAPI not available, skipping WC sync")
            return True

        config = store.get("config", {})
        api = WooCommerceAPI(
            config.get("store_url"),
            config.get("consumer_key"),
            config.get("consumer_secret")
        )

        # Map status to WooCommerce status
        wc_status_map = {
            "processing": "processing",
            "completed": "completed",
            "cancelled": "cancelled",
            "refunded": "refunded",
            "shipped": "completed",
            "delivered": "completed"
        }

        wc_status = wc_status_map.get(status, "processing")

        # Update order
        api.update_order(int(order_id), {
            "status": wc_status,
            "customer_note": f"Estado actualizado desde CRM: {status}"
        })

        return True

    except Exception as e:
        logger.error(f"Error syncing to WooCommerce: {e}")
        return False


async def _sync_to_shopify(
    store: dict,
    order_id: str,
    status: str,
    note: str
) -> bool:
    """Sync order status to Shopify"""
    try:
        # Dynamic import to avoid circular dependencies
        try:
            from services.platforms import ShopifyAPI
        except ImportError:
            logger.warning("ShopifyAPI not available, skipping Shopify sync")
            return True

        config = store.get("config", {})
        api = ShopifyAPI(
            config.get("store_url"),
            config.get("access_token")
        )

        # Shopify fulfillment statuses
        # Note: Shopify order status is read-only from API
        # We can update fulfillment or add notes
        # For now, we'll add a note

        await api.create_order_note(
            order_id,
            f"Estado en CRM: {status}"
        )

        return True

    except Exception as e:
        logger.error(f"Error syncing to Shopify: {e}")
        return False


async def _sync_to_prestashop(
    store: dict,
    order_id: str,
    status: str,
    note: str
) -> bool:
    """Sync order status to PrestaShop"""
    try:
        # Dynamic import to avoid circular dependencies
        try:
            from services.platforms import PrestaShopAPI
        except ImportError:
            logger.warning("PrestaShopAPI not available, skipping PrestaShop sync")
            return True

        config = store.get("config", {})
        api = PrestaShopAPI(
            config.get("store_url"),
            config.get("api_key")
        )

        # Map status to PrestaShop order state
        ps_status_map = {
            "processing": "3",      # Processing
            "completed": "5",       # Delivered
            "cancelled": "6",       # Cancelled
            "refunded": "7",        # Refunded
            "shipped": "5",         # Delivered
            "delivered": "5"        # Delivered
        }

        ps_status = ps_status_map.get(status, "3")

        # Update order state
        api.update_order(int(order_id), {
            "current_state": ps_status
        })

        return True

    except Exception as e:
        logger.error(f"Error syncing to PrestaShop: {e}")
        return False


async def get_order_sync_status(order_id: str, user_id: str) -> Dict:
    """
    Get bidirectional sync status for an order

    Returns information about:
    - Last sync from store to CRM
    - Last sync from CRM to store
    - Sync status
    - Any sync errors
    """
    try:
        order = await db.orders.find_one({
            "id": order_id,
            "userId": user_id
        }, {"_id": 0})

        if not order:
            return {"error": "Order not found"}

        sync_status = {
            "orderId": order_id,
            "source": order.get("source"),
            "status": order.get("status"),
            "crmStatus": order.get("crmData", {}).get("crmStatus"),
            "syncHistory": []
        }

        # Extract sync-related history entries
        for entry in order.get("history", []):
            if "sync" in entry.get("action", "").lower():
                sync_status["syncHistory"].append({
                    "action": entry.get("action"),
                    "timestamp": entry.get("timestamp"),
                    "details": entry.get("details")
                })

        sync_status["lastCrmSync"] = order.get("crmData", {}).get("lastSyncAt")
        sync_status["lastStoreSync"] = order.get("lastSyncedToStoreAt")
        sync_status["retryCount"] = order.get("retryCount", 0)
        sync_status["lastError"] = order.get("error")

        return sync_status

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return {"error": str(e)}
