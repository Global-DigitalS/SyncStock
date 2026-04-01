"""
Order normalization from different platforms to standard format
"""
import re
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
from .models import Order, OrderItem, OrderAddress

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_order_data(data: Dict) -> Dict:
    """Validate order data structure"""
    errors = []

    # Check customer data
    if not data.get("customer_name") or not isinstance(data["customer_name"], str):
        errors.append("Customer name is required and must be a string")
    else:
        data["customer_name"] = data["customer_name"].strip()

    if not data.get("customer_email") or not validate_email(data.get("customer_email", "")):
        errors.append("Valid customer email is required")
    else:
        data["customer_email"] = data["customer_email"].strip().lower()

    # Check items
    if not data.get("items") or not isinstance(data["items"], list) or len(data["items"]) == 0:
        errors.append("At least one item is required")

    for idx, item in enumerate(data.get("items", [])):
        if not item.get("sku"):
            errors.append(f"Item {idx}: SKU is required")
        if not isinstance(item.get("quantity", 0), (int, float)) or item.get("quantity", 0) <= 0:
            errors.append(f"Item {idx}: Quantity must be a positive number")
        if not isinstance(item.get("price", 0), (int, float)) or item.get("price", 0) < 0:
            errors.append(f"Item {idx}: Price must be a non-negative number")
        if not item.get("name"):
            errors.append(f"Item {idx}: Name is required")

    # Check addresses
    for addr_type in ["shipping", "billing"]:
        addr = data.get(f"{addr_type}_address", {})
        for field in ["street", "city", "zip_code", "country"]:
            if not addr.get(field):
                errors.append(f"{addr_type.title()} address: {field} is required")

    return {"valid": len(errors) == 0, "errors": errors}


def normalize_woocommerce_order(data: Dict) -> Optional[Order]:
    """Normalize WooCommerce webhook data to Order"""
    try:
        # Extract customer info
        billing = data.get("billing", {})
        shipping = data.get("shipping", {}) or billing

        customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
        customer_email = billing.get("email", "")
        customer_phone = billing.get("phone", "")

        # Extract items
        items = []
        for line in data.get("line_items", []):
            item = OrderItem(
                sku=line.get("sku") or str(line.get("product_id", "")),
                quantity=int(line.get("quantity", 1)),
                price=float(line.get("price", 0)),
                name=line.get("name", ""),
                ean=line.get("ean")
            )
            items.append(item)

        # Create addresses
        shipping_addr = OrderAddress(
            street=f"{shipping.get('address_1', '')} {shipping.get('address_2', '')}".strip(),
            city=shipping.get("city", ""),
            zip_code=shipping.get("postcode", ""),
            country=shipping.get("country", ""),
            state=shipping.get("state")
        )

        billing_addr = OrderAddress(
            street=f"{billing.get('address_1', '')} {billing.get('address_2', '')}".strip(),
            city=billing.get("city", ""),
            zip_code=billing.get("postcode", ""),
            country=billing.get("country", ""),
            state=billing.get("state")
        )

        # Determine payment status
        payment_status = "pending"
        if data.get("status") == "completed":
            payment_status = "paid"
        elif data.get("status") in ["failed", "cancelled"]:
            payment_status = "failed"

        order = Order(
            source="woocommerce",
            source_order_id=str(data.get("id", "")),
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            items=items,
            shipping_address=shipping_addr,
            billing_address=billing_addr,
            payment_status=payment_status
        )

        return order

    except Exception as e:
        logger.error(f"Error normalizing WooCommerce order: {e}")
        return None


def normalize_shopify_order(data: Dict) -> Optional[Order]:
    """Normalize Shopify webhook data to Order"""
    try:
        customer = data.get("customer", {})
        shipping_address = data.get("shipping_address", {})
        billing_address = data.get("billing_address", {}) or shipping_address

        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        customer_email = customer.get("email", "")
        customer_phone = customer.get("phone", "")

        items = []
        for line in data.get("line_items", []):
            item = OrderItem(
                sku=line.get("sku") or str(line.get("product_id", "")),
                quantity=int(line.get("quantity", 1)),
                price=float(line.get("price", 0)),
                name=line.get("title", ""),
                ean=line.get("barcode")
            )
            items.append(item)

        shipping_addr = OrderAddress(
            street=f"{shipping_address.get('address1', '')} {shipping_address.get('address2', '')}".strip(),
            city=shipping_address.get("city", ""),
            zip_code=shipping_address.get("zip", ""),
            country=shipping_address.get("country", ""),
            state=shipping_address.get("province")
        )

        billing_addr = OrderAddress(
            street=f"{billing_address.get('address1', '')} {billing_address.get('address2', '')}".strip(),
            city=billing_address.get("city", ""),
            zip_code=billing_address.get("zip", ""),
            country=billing_address.get("country", ""),
            state=billing_address.get("province")
        )

        payment_status = "paid" if data.get("financial_status") == "paid" else "pending"

        order = Order(
            source="shopify",
            source_order_id=str(data.get("order_number", "")),
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            items=items,
            shipping_address=shipping_addr,
            billing_address=billing_addr,
            payment_status=payment_status
        )

        return order

    except Exception as e:
        logger.error(f"Error normalizing Shopify order: {e}")
        return None


def normalize_prestashop_order(data: Dict) -> Optional[Order]:
    """Normalize PrestaShop webhook data to Order"""
    try:
        customer_name = f"{data.get('firstname', '')} {data.get('lastname', '')}".strip()
        customer_email = data.get("email", "")

        items = []
        for line in data.get("products", []):
            item = OrderItem(
                sku=line.get("reference", ""),
                quantity=int(line.get("product_quantity", 1)),
                price=float(line.get("product_price", 0)),
                name=line.get("product_name", "")
            )
            items.append(item)

        # PrestaShop provides address data differently
        shipping_addr = OrderAddress(
            street=data.get("address", ""),
            city=data.get("city", ""),
            zip_code=data.get("postcode", ""),
            country=data.get("country", "")
        )

        order = Order(
            source="prestashop",
            source_order_id=str(data.get("id", "")),
            customer_name=customer_name,
            customer_email=customer_email,
            items=items,
            shipping_address=shipping_addr,
            payment_status="paid" if data.get("payment") else "pending"
        )

        return order

    except Exception as e:
        logger.error(f"Error normalizing PrestaShop order: {e}")
        return None


def normalize_order(data: Dict, platform: str) -> Optional[Order]:
    """
    Normalize order from any platform

    Args:
        data: Raw order data from webhook
        platform: "woocommerce", "shopify", "prestashop"

    Returns:
        Normalized Order object or None if error
    """
    if platform == "woocommerce":
        return normalize_woocommerce_order(data)
    elif platform == "shopify":
        return normalize_shopify_order(data)
    elif platform == "prestashop":
        return normalize_prestashop_order(data)
    else:
        logger.warning(f"Unknown platform: {platform}")
        return None
