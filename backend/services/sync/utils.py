"""
Funciones auxiliares puras de sync.py - Sin dependencias de BD, WebSocket ni async.
Solo helpers de cálculo y transformación de datos.
"""

import logging

logger = logging.getLogger(__name__)


def format_file_size(size: int) -> str:
    """Formatea el tamaño de archivo en formato legible"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


def mask_key(key: str) -> str:
    """Enmascara clave - muestra solo últimos 4 caracteres"""
    if len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


def calculate_final_price(base_price: float, product: dict, rules: list) -> float:
    """Calculate final price by cumulatively applying all matching margin rules.

    HIGH FIX #11: Apply rules cumulatively in priority order, not just the first match.
    Each rule is applied on top of the previous result.

    Example:
    - base_price: 100€
    - rule 1 (all, +10%): 100 * 1.10 = 110€
    - rule 2 (category, +20%): 110 * 1.20 = 132€
    """
    final_price = base_price

    # Rules are already sorted by priority (descending) from the caller
    for rule in rules:
        applies = False

        # Check if rule applies to this product
        if rule["apply_to"] == "all" or rule["apply_to"] == "category" and product.get("category") == rule.get("apply_to_value") or rule["apply_to"] == "supplier" and product.get("supplier_id") == rule.get("apply_to_value") or rule["apply_to"] == "product" and product.get("id") == rule.get("apply_to_value"):
            applies = True

        if applies:
            # Check min/max price bounds (on base price)
            if rule.get("min_price") and base_price < rule["min_price"]:
                continue
            if rule.get("max_price") and base_price > rule["max_price"]:
                continue

            # SECURITY FIX #11: Apply cumulatively on final_price, not base_price
            # This allows multiple rules to be stacked
            if rule["rule_type"] == "percentage":
                final_price = final_price * (1 + rule["value"] / 100)
            elif rule["rule_type"] == "fixed":
                final_price = final_price + rule["value"]

            # DO NOT BREAK - continue applying other rules
            logger.debug(f"Applied margin rule: {rule.get('name', 'unnamed')} → {final_price:.2f}€")

    return final_price


def extract_store_product_info(store_prod: dict, platform: str) -> dict:
    """
    Extract matching fields from store product.
    Price and stock come from SyncStock supplier products, not the store.

    Fields extracted: SKU, EAN, name, description, image, category, brand
    """
    info = {
        "sku": "",
        "ean": "",
        "name": "",
        "description": "",
        "image_url": "",
        "category": "",
        "brand": ""
    }

    if platform == "woocommerce":
        info["sku"] = (store_prod.get("sku") or "").strip()
        info["ean"] = (store_prod.get("ean") or "").strip()
        info["name"] = (store_prod.get("name") or "").strip()
        info["description"] = store_prod.get("description") or store_prod.get("short_description") or ""
        images = store_prod.get("images") or []
        info["image_url"] = images[0].get("src", "") if images else ""
        cats = store_prod.get("categories") or []
        info["category"] = cats[0].get("name", "") if cats else ""
        info["brand"] = store_prod.get("brands", [{}])[0].get("name", "") if store_prod.get("brands") else ""
    elif platform == "prestashop":
        info["sku"] = (store_prod.get("reference") or "").strip()
        info["ean"] = (store_prod.get("ean13") or "").strip()
        name_val = store_prod.get("name") or ""
        if isinstance(name_val, list):
            name_val = name_val[0].get("value", "") if name_val else ""
        elif isinstance(name_val, dict):
            name_val = name_val.get("value", "") or name_val.get("language", "")
        info["name"] = str(name_val).strip()
        info["description"] = store_prod.get("description") or store_prod.get("description_short") or ""
        info["category"] = store_prod.get("id_category_default", "")
        info["brand"] = ""
    elif platform == "shopify":
        variants = store_prod.get("variants") or []
        first_variant = variants[0] if variants else {}
        info["sku"] = (first_variant.get("sku") or "").strip()
        info["ean"] = (first_variant.get("barcode") or "").strip()
        info["name"] = (store_prod.get("title") or "").strip()
        info["description"] = store_prod.get("body_html") or ""
        info["brand"] = store_prod.get("vendor") or ""
        info["category"] = store_prod.get("product_type") or ""
        images = store_prod.get("images") or []
        info["image_url"] = images[0].get("src", "") if images else ""
    elif platform == "magento":
        info["sku"] = (store_prod.get("sku") or "").strip()
        info["name"] = (store_prod.get("name") or "").strip()
        info["description"] = store_prod.get("description") or ""
        info["ean"] = ""
        info["brand"] = ""
        info["category"] = ""
    elif platform == "wix":
        info["sku"] = (store_prod.get("sku") or "").strip()
        info["name"] = (store_prod.get("name") or "").strip()
        info["description"] = store_prod.get("description") or ""
        info["ean"] = ""
        media = store_prod.get("media", {}).get("items") or []
        info["image_url"] = media[0].get("url", "") if media else ""
        info["category"] = ""
        info["brand"] = ""

    return info
