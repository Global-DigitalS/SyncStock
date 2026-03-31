"""
Order service: enrichment, validation, and CRM synchronization
"""
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timezone
from services.database import db
from services.crm_clients.factory import create_crm_client
from .models import Order
from .normalizer import normalize_order, validate_order_data

logger = logging.getLogger(__name__)


async def check_duplicate_order(source: str, source_order_id: str) -> bool:
    """Check if order already exists"""
    existing = await db.orders.find_one({
        "source": source,
        "sourceOrderId": source_order_id
    })
    return existing is not None


async def enrich_order(order: Order, user_id: str) -> Tuple[Order, Optional[str]]:
    """
    Enrich order with product data and stock information

    Returns:
        Tuple of (enriched_order, error_message)
    """
    try:
        # Validate and map products
        for item in order.items:
            # Find product by SKU
            product = await db.products.find_one({
                "user_id": user_id,
                "sku": item.sku
            })

            if not product:
                logger.warning(f"Product not found for SKU: {item.sku}")
                item.status = "not_found"
                item.product_id = None
                continue

            item.product_id = product.get("id")
            item.status = "available"

            # Check stock
            available_stock = product.get("stock", 0)
            if available_stock < item.quantity:
                if available_stock == 0:
                    item.status = "backorder"
                else:
                    # Partially available - mark as backorder
                    item.status = "backorder"
                logger.info(f"Stock shortage for {item.sku}: need {item.quantity}, have {available_stock}")

        return order, None

    except Exception as e:
        error_msg = f"Error enriching order: {str(e)}"
        logger.error(error_msg)
        return order, error_msg


async def get_user_crm(user_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get user's configured CRM connection

    Returns:
        Tuple of (crm_client, crm_platform_name)
    """
    try:
        # Get user's CRM connection
        crm_conn = await db.crm_connections.find_one({"user_id": user_id})

        if not crm_conn:
            return None, None

        platform = crm_conn.get("platform")
        config = crm_conn.get("config", {})

        # Create CRM client
        client = create_crm_client(platform, config)

        if not client:
            logger.warning(f"Could not create CRM client for platform: {platform}")
            return None, None

        return client, platform

    except Exception as e:
        logger.error(f"Error getting user CRM: {e}")
        return None, None


async def sync_order_to_crm(order: Order, crm_client, crm_platform: str, user_id: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Synchronize order to configured CRM

    Returns:
        Tuple of (success, error_message, crm_data)
    """
    try:
        if crm_platform == "dolibarr":
            return await _sync_to_dolibarr(order, crm_client, user_id)
        elif crm_platform == "odoo":
            return await _sync_to_odoo(order, crm_client, user_id)
        else:
            return False, f"Unsupported CRM: {crm_platform}", None

    except Exception as e:
        error_msg = f"Error syncing to CRM: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, None


async def _sync_to_dolibarr(order: Order, crm_client, user_id: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """Sync order to Dolibarr CRM"""
    try:
        # Get or create customer in Dolibarr
        customers = crm_client.get_thirdparties(limit=10000)
        dolibarr_customer_id = None

        # Search for existing customer by email
        for customer in customers:
            if customer.get("email") == order.customer["email"]:
                dolibarr_customer_id = int(customer.get("id"))
                break

        # Create customer if not found
        if not dolibarr_customer_id:
            create_result = crm_client.create_thirdparty({
                "name": order.customer["name"],
                "email": order.customer["email"],
                "phone": order.customer.get("phone", ""),
                "address": order.addresses["shipping"].get("street", ""),
                "zip": order.addresses["shipping"].get("zipCode", ""),
                "city": order.addresses["shipping"].get("city", ""),
                "country": order.addresses["shipping"].get("country", ""),
                "client": 1,  # Mark as client
                "status": 1  # Active
            })

            if create_result.get("status") != "success":
                return False, f"Failed to create customer in Dolibarr: {create_result.get('message')}", None

            dolibarr_customer_id = create_result.get("customer_id")

        # Create order in Dolibarr
        lines = []
        for item in order.items:
            if item.product_id:
                lines.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price,
                    "description": item.name
                })

        if not lines:
            logger.warning(f"Order {order.id} has no valid products to sync to Dolibarr")
            return False, "No valid products to sync", None

        order_result = crm_client.create_order({
            "customer_id": dolibarr_customer_id,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "external_ref": f"{order.source.upper()}-{order.source_order_id}",
            "notes": f"Order from {order.source} (ID: {order.source_order_id})",
            "lines": lines
        })

        if order_result.get("status") != "success":
            return False, f"Failed to create order in Dolibarr: {order_result.get('message')}", None

        return True, None, {
            "dolibarr_order_id": order_result.get("order_id"),
            "dolibarr_customer_id": dolibarr_customer_id,
            "crm": "dolibarr"
        }

    except Exception as e:
        logger.error(f"Error syncing to Dolibarr: {e}")
        return False, str(e), None


async def _sync_to_odoo(order: Order, crm_client, user_id: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """Sync order to Odoo CRM"""
    try:
        # Get or create customer in Odoo
        partners = crm_client.get_suppliers(limit=10000)  # Get all customers/suppliers
        odoo_customer_id = None

        # Search for existing customer by email
        for partner in partners:
            if partner.get("email") == order.customer["email"]:
                odoo_customer_id = partner.get("id")
                break

        # Create customer if not found
        if not odoo_customer_id:
            create_result = crm_client.create_supplier({
                "name": order.customer["name"],
                "email": order.customer["email"],
                "phone": order.customer.get("phone", ""),
                "address": order.addresses["shipping"].get("street", ""),
                "city": order.addresses["shipping"].get("city", "")
            })

            if create_result.get("status") != "success":
                return False, f"Failed to create customer in Odoo: {create_result.get('message')}", None

            odoo_customer_id = create_result.get("supplier_id")

        # Prepare order lines
        lines = []
        for item in order.items:
            if item.product_id:
                lines.append({
                    "product_id": item.product_id,
                    "product_qty": item.quantity,
                    "price_unit": item.price,
                    "name": item.name
                })

        if not lines:
            logger.warning(f"Order {order.id} has no valid products to sync to Odoo")
            return False, "No valid products to sync", None

        # Create sales order in Odoo
        order_payload = {
            "partner_id": odoo_customer_id,
            "order_line": lines,
            "client_order_ref": f"{order.source.upper()}-{order.source_order_id}",
            "note": f"Order from {order.source} (ID: {order.source_order_id})\nTotal: {order.total_amount}"
        }

        # Make POST request to create order (using requests directly)
        import requests
        headers = crm_client.headers if hasattr(crm_client, 'headers') else {}
        response = requests.post(
            f"{crm_client.base_url}/api/sale.order",
            json=order_payload,
            headers=headers,
            timeout=30
        )

        if response.status_code not in [200, 201]:
            error_msg = response.text[:200] if response.text else f"Status {response.status_code}"
            return False, f"Failed to create order in Odoo: {error_msg}", None

        result = response.json()
        odoo_order_id = result.get("id") if isinstance(result, dict) else result

        return True, None, {
            "odoo_order_id": odoo_order_id,
            "odoo_customer_id": odoo_customer_id,
            "crm": "odoo"
        }

    except Exception as e:
        logger.error(f"Error syncing to Odoo: {e}")
        return False, str(e), None


async def save_order_to_db(order: Order, user_id: str, crm_data: Optional[Dict] = None,
                          status: str = "completed", error: Optional[Dict] = None) -> bool:
    """Save order to MongoDB"""
    try:
        doc = order.to_dict()
        doc["userId"] = user_id
        doc["status"] = status
        doc["processedAt"] = datetime.now(timezone.utc).isoformat()

        if crm_data:
            doc["crmData"] = crm_data

        if error:
            doc["error"] = error

        # Add history entry
        doc["history"].append({
            "action": "created",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {"status": status}
        })

        await db.orders.insert_one(doc)

        logger.info(f"Order {order.id} saved to database with status: {status}")
        return True

    except Exception as e:
        logger.error(f"Error saving order to database: {e}")
        return False


async def process_order_webhook(data: Dict, platform: str, user_id: str, store_id: str) -> Dict:
    """
    Main function to process order webhook

    Returns:
        Dict with status and details
    """
    try:
        # Normalize order
        order = normalize_order(data, platform)
        if not order:
            return {"status": "error", "message": "Could not normalize order"}

        logger.info(f"Processing {platform} order {order.source_order_id} for user {user_id}")

        # Check for duplicates
        if await check_duplicate_order(order.source, order.source_order_id):
            logger.warning(f"Duplicate order detected: {order.source}#{order.source_order_id}")
            return {"status": "duplicate", "message": "Order already exists"}

        # Enrich with product data
        order, enrich_error = await enrich_order(order, user_id)
        if enrich_error:
            logger.warning(f"Error enriching order: {enrich_error}")
            # Continue anyway, save with error

        # Get user's CRM
        crm_client, crm_platform = await get_user_crm(user_id)
        crm_data = None

        if crm_client and crm_platform:
            # Sync to CRM
            success, crm_error, crm_data = await sync_order_to_crm(order, crm_client, crm_platform, user_id)

            if not success:
                logger.error(f"Failed to sync to CRM: {crm_error}")
                # Save with error
                await save_order_to_db(
                    order, user_id,
                    status="error",
                    error={"code": "CRM_SYNC_ERROR", "message": crm_error}
                )
                return {"status": "error", "message": f"CRM sync failed: {crm_error}"}
        else:
            logger.info(f"No CRM configured for user {user_id}")

        # Save order
        await save_order_to_db(order, user_id, crm_data=crm_data, status="completed")

        return {
            "status": "success",
            "order_id": order.id,
            "source_order_id": order.source_order_id,
            "crm_data": crm_data,
            "message": "Order processed successfully"
        }

    except Exception as e:
        logger.error(f"Error processing order webhook: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
