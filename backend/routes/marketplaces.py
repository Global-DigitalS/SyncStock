import csv
import io
import logging
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response

from services.auth import DEFAULT_LIMITS, get_current_user, get_superadmin_user
from services.database import db

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== MARKETPLACE PLATFORM DEFINITIONS ====================

MARKETPLACE_PLATFORMS = {
    "google_merchant": {
        "id": "google_merchant",
        "name": "Google Merchant Center",
        "description": "Google Shopping Feed (XML/Atom)",
        "feed_format": "xml",
        "logo": "google",
        "required_fields": ["id", "title", "description", "link", "image_link", "price", "availability", "condition", "brand", "gtin"],
        "optional_fields": ["mpn", "google_product_category", "product_type", "sale_price", "shipping_weight"],
        "docs_url": "https://support.google.com/merchants/answer/7052112",
        "color": "bg-blue-100 text-blue-700",
    },
    "facebook_shops": {
        "id": "facebook_shops",
        "name": "Facebook & Instagram Shops",
        "description": "Meta Commerce Feed (XML/CSV)",
        "feed_format": "xml",
        "logo": "facebook",
        "required_fields": ["id", "title", "description", "availability", "condition", "price", "link", "image_link", "brand"],
        "optional_fields": ["sale_price", "google_product_category", "item_group_id", "color", "size", "material"],
        "docs_url": "https://www.facebook.com/business/help/120325381656392",
        "color": "bg-indigo-100 text-indigo-700",
    },
    "amazon": {
        "id": "amazon",
        "name": "Amazon Seller Central",
        "description": "Amazon Inventory Feed (CSV/TXT)",
        "feed_format": "csv",
        "logo": "amazon",
        "required_fields": ["item_sku", "item_name", "external_product_id", "external_product_id_type", "item_type", "brand_name", "bullet_point1", "standard_price", "quantity"],
        "optional_fields": ["sale_price", "sale_from_date", "sale_end_date", "product_description", "main_image_url", "parent_sku"],
        "docs_url": "https://sellercentral.amazon.es/help/hub/reference",
        "color": "bg-orange-100 text-orange-700",
    },
    "el_corte_ingles": {
        "id": "el_corte_ingles",
        "name": "El Corte Inglés",
        "description": "Feed XML para El Corte Inglés Marketplace",
        "feed_format": "xml",
        "logo": "eci",
        "required_fields": ["sku", "nombre", "descripcion", "precio", "stock", "ean", "marca", "imagen"],
        "optional_fields": ["precio_oferta", "categoria", "peso", "dimensiones", "garantia"],
        "docs_url": "https://marketplace.elcorteingles.es",
        "color": "bg-green-100 text-green-700",
    },
    "miravia": {
        "id": "miravia",
        "name": "Miravia",
        "description": "Feed XML/CSV para Miravia Marketplace",
        "feed_format": "xml",
        "logo": "miravia",
        "required_fields": ["seller_sku", "product_name", "description", "price", "quantity", "brand", "main_image"],
        "optional_fields": ["sale_price", "category_id", "weight", "barcode"],
        "docs_url": "https://seller.miravia.es",
        "color": "bg-pink-100 text-pink-700",
    },
    "idealo": {
        "id": "idealo",
        "name": "Idealo",
        "description": "Feed CSV/XML para comparador de precios Idealo",
        "feed_format": "csv",
        "logo": "idealo",
        "required_fields": ["sku", "name", "description", "url", "image_url", "price", "brand", "ean"],
        "optional_fields": ["category", "shipping_costs", "delivery_time", "condition"],
        "docs_url": "https://www.idealo.es/ayuda/vendedores",
        "color": "bg-yellow-100 text-yellow-700",
    },
    "kelkoo": {
        "id": "kelkoo",
        "name": "Kelkoo",
        "description": "Feed XML para comparador Kelkoo",
        "feed_format": "xml",
        "logo": "kelkoo",
        "required_fields": ["offer-id", "title", "description", "price", "url", "image", "brand", "ean"],
        "optional_fields": ["shipping-cost", "delivery-time", "category", "condition"],
        "docs_url": "https://developer.kelkoo.com",
        "color": "bg-red-100 text-red-700",
    },
    "trovaprezzi": {
        "id": "trovaprezzi",
        "name": "Trovaprezzi",
        "description": "Feed XML para comparador Trovaprezzi",
        "feed_format": "xml",
        "logo": "trovaprezzi",
        "required_fields": ["codice", "nome", "descrizione", "prezzo", "url", "immagine", "marca", "ean"],
        "optional_fields": ["spese_spedizione", "disponibilita", "categoria"],
        "docs_url": "https://www.trovaprezzi.it",
        "color": "bg-purple-100 text-purple-700",
    },
    "ebay": {
        "id": "ebay",
        "name": "eBay",
        "description": "Feed de inventario para eBay Marketplace",
        "feed_format": "csv",
        "logo": "ebay",
        "required_fields": ["Action", "ItemID", "Title", "Description", "PrimaryCategory", "StartPrice", "Quantity", "ConditionID"],
        "optional_fields": ["SubTitle", "PicURL", "BuyItNowPrice", "Brand", "EAN"],
        "docs_url": "https://developer.ebay.com",
        "color": "bg-sky-100 text-sky-700",
    },
    "zalando": {
        "id": "zalando",
        "name": "Zalando",
        "description": "Feed de productos para Zalando Partner",
        "feed_format": "xml",
        "logo": "zalando",
        "required_fields": ["sku", "name", "description", "price", "stock", "brand", "ean", "image_url", "size", "color"],
        "optional_fields": ["sale_price", "material", "season", "gender"],
        "docs_url": "https://partnerportal.zalando.com",
        "color": "bg-orange-100 text-orange-800",
    },
    "pricerunner": {
        "id": "pricerunner",
        "name": "PriceRunner",
        "description": "Feed XML para comparador PriceRunner",
        "feed_format": "xml",
        "logo": "pricerunner",
        "required_fields": ["id", "name", "description", "price", "url", "image_url", "brand", "ean"],
        "optional_fields": ["delivery_cost", "delivery_time", "category", "condition"],
        "docs_url": "https://www.pricerunner.es",
        "color": "bg-teal-100 text-teal-700",
    },
    "bing_shopping": {
        "id": "bing_shopping",
        "name": "Microsoft Bing Shopping",
        "description": "Feed XML para Microsoft Advertising / Bing Shopping",
        "feed_format": "xml",
        "logo": "microsoft",
        "required_fields": ["id", "title", "description", "link", "image_link", "price", "availability", "condition", "brand", "gtin"],
        "optional_fields": ["sale_price", "product_type", "shipping_weight", "mpn"],
        "docs_url": "https://help.ads.microsoft.com",
        "color": "bg-cyan-100 text-cyan-700",
    },
}


# ==================== HELPER: LIMIT CHECK ====================

async def _check_marketplace_limit(user: dict) -> None:
    """Raise 403 if the user has reached their marketplace connection limit."""
    role = user.get("role", "user")
    if role == "superadmin" or "unlimited" in DEFAULT_LIMITS.get(role, {}).values():
        return
    max_connections = user.get("max_marketplace_connections", DEFAULT_LIMITS.get(role, {}).get("max_marketplace_connections", 0))
    current_count = await db.marketplace_connections.count_documents({"user_id": user["id"]})
    if current_count >= max_connections:
        raise HTTPException(
            status_code=403,
            detail=f"Has alcanzado el límite de conexiones de marketplace ({max_connections}). Actualiza tu plan para añadir más."
        )


# ==================== FEED GENERATORS ====================

def _generate_xml_feed(platform_id: str, products: list, connection: dict) -> str:
    """Generate an XML feed for a marketplace platform."""
    if platform_id in ("google_merchant", "bing_shopping", "facebook_shops"):
        return _generate_google_style_feed(products, connection, platform_id)
    elif platform_id == "el_corte_ingles":
        return _generate_eci_feed(products, connection)
    elif platform_id in ("miravia", "zalando", "pricerunner"):
        return _generate_generic_xml_feed(products, connection, platform_id)
    elif platform_id == "kelkoo":
        return _generate_kelkoo_feed(products, connection)
    elif platform_id == "trovaprezzi":
        return _generate_trovaprezzi_feed(products, connection)
    else:
        return _generate_generic_xml_feed(products, connection, platform_id)


def _generate_google_style_feed(products: list, connection: dict, platform_id: str) -> str:
    """Generate Google Merchant / Facebook / Bing compatible XML feed."""
    root = ET.Element("rss", version="2.0")
    root.set("xmlns:g", "http://base.google.com/ns/1.0")
    channel = ET.SubElement(root, "channel")

    ET.SubElement(channel, "title").text = connection.get("name", "Product Feed")
    ET.SubElement(channel, "link").text = connection.get("store_url", "")
    ET.SubElement(channel, "description").text = f"Feed generado por SyncStock para {platform_id}"

    field_map = connection.get("field_mapping", {})

    for product in products:
        item = ET.SubElement(channel, "item")

        def pval(field, default=""):
            mapped = field_map.get(field)
            if mapped and mapped in product:
                return str(product[mapped]) if product[mapped] is not None else default
            return str(product.get(field, default))

        ET.SubElement(item, "g:id").text = pval("id", product.get("id", ""))
        ET.SubElement(item, "g:title").text = pval("title", product.get("name", ""))
        ET.SubElement(item, "g:description").text = pval("description", product.get("description", ""))
        ET.SubElement(item, "g:link").text = pval("link", connection.get("store_url", ""))
        ET.SubElement(item, "g:image_link").text = pval("image_link", product.get("image_url", ""))

        price_val = product.get("price", 0) or 0
        currency = connection.get("currency", "EUR")
        ET.SubElement(item, "g:price").text = f"{price_val:.2f} {currency}"

        stock_val = product.get("stock", 0) or 0
        availability = "in stock" if stock_val > 0 else "out of stock"
        ET.SubElement(item, "g:availability").text = availability

        ET.SubElement(item, "g:condition").text = connection.get("condition", "new")
        ET.SubElement(item, "g:brand").text = pval("brand", product.get("brand", ""))

        ean = product.get("ean") or product.get("gtin") or product.get("upc") or ""
        if ean:
            ET.SubElement(item, "g:gtin").text = str(ean)

        mpn = product.get("part_number") or product.get("referencia") or ""
        if mpn:
            ET.SubElement(item, "g:mpn").text = str(mpn)

        category = product.get("category", "")
        if category:
            ET.SubElement(item, "g:product_type").text = category

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _generate_eci_feed(products: list, connection: dict) -> str:
    """Generate El Corte Inglés XML feed."""
    root = ET.Element("productos")
    field_map = connection.get("field_mapping", {})

    for product in products:
        prod_elem = ET.SubElement(root, "producto")

        def pval(field, default=""):
            mapped = field_map.get(field)
            if mapped and mapped in product:
                return str(product[mapped]) if product[mapped] is not None else default
            return str(product.get(field, default))

        ET.SubElement(prod_elem, "sku").text = pval("sku", product.get("id", ""))
        ET.SubElement(prod_elem, "nombre").text = pval("nombre", product.get("name", ""))
        ET.SubElement(prod_elem, "descripcion").text = pval("descripcion", product.get("description", ""))
        ET.SubElement(prod_elem, "precio").text = str(product.get("price", 0) or 0)
        ET.SubElement(prod_elem, "stock").text = str(product.get("stock", 0) or 0)
        ET.SubElement(prod_elem, "ean").text = pval("ean", product.get("ean", ""))
        ET.SubElement(prod_elem, "marca").text = pval("marca", product.get("brand", ""))
        ET.SubElement(prod_elem, "imagen").text = pval("imagen", product.get("image_url", ""))
        category = product.get("category", "")
        if category:
            ET.SubElement(prod_elem, "categoria").text = category

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _generate_kelkoo_feed(products: list, connection: dict) -> str:
    """Generate Kelkoo XML feed."""
    root = ET.Element("offers")
    field_map = connection.get("field_mapping", {})

    for product in products:
        offer = ET.SubElement(root, "offer")

        def pval(field, default=""):
            mapped = field_map.get(field)
            if mapped and mapped in product:
                return str(product[mapped]) if product[mapped] is not None else default
            return str(product.get(field, default))

        ET.SubElement(offer, "offer-id").text = pval("offer-id", product.get("id", ""))
        ET.SubElement(offer, "title").text = pval("title", product.get("name", ""))
        ET.SubElement(offer, "description").text = pval("description", product.get("description", ""))
        currency = connection.get("currency", "EUR")
        ET.SubElement(offer, "price").text = f"{product.get('price', 0) or 0:.2f} {currency}"
        ET.SubElement(offer, "url").text = connection.get("store_url", "")
        ET.SubElement(offer, "image").text = pval("image", product.get("image_url", ""))
        ET.SubElement(offer, "brand").text = pval("brand", product.get("brand", ""))
        ean = product.get("ean") or product.get("gtin") or ""
        if ean:
            ET.SubElement(offer, "ean").text = str(ean)

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _generate_trovaprezzi_feed(products: list, connection: dict) -> str:
    """Generate Trovaprezzi XML feed."""
    root = ET.Element("prodotti")
    field_map = connection.get("field_mapping", {})

    for product in products:
        prod = ET.SubElement(root, "prodotto")

        def pval(field, default=""):
            mapped = field_map.get(field)
            if mapped and mapped in product:
                return str(product[mapped]) if product[mapped] is not None else default
            return str(product.get(field, default))

        ET.SubElement(prod, "codice").text = pval("codice", product.get("id", ""))
        ET.SubElement(prod, "nome").text = pval("nome", product.get("name", ""))
        ET.SubElement(prod, "descrizione").text = pval("descrizione", product.get("description", ""))
        currency = connection.get("currency", "EUR")
        ET.SubElement(prod, "prezzo").text = f"{product.get('price', 0) or 0:.2f}"
        ET.SubElement(prod, "valuta").text = currency
        ET.SubElement(prod, "url").text = connection.get("store_url", "")
        ET.SubElement(prod, "immagine").text = pval("immagine", product.get("image_url", ""))
        ET.SubElement(prod, "marca").text = pval("marca", product.get("brand", ""))
        ean = product.get("ean") or product.get("gtin") or ""
        if ean:
            ET.SubElement(prod, "ean").text = str(ean)

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _generate_generic_xml_feed(products: list, connection: dict, platform_id: str) -> str:
    """Generate a generic XML feed for platforms like Miravia, Zalando, PriceRunner."""
    root = ET.Element("products")
    root.set("platform", platform_id)
    field_map = connection.get("field_mapping", {})

    for product in products:
        prod = ET.SubElement(root, "product")

        def pval(field, default=""):
            mapped = field_map.get(field)
            if mapped and mapped in product:
                return str(product[mapped]) if product[mapped] is not None else default
            return str(product.get(field, default))

        ET.SubElement(prod, "id").text = pval("id", product.get("id", ""))
        ET.SubElement(prod, "name").text = pval("name", product.get("name", ""))
        ET.SubElement(prod, "description").text = pval("description", product.get("description", ""))
        currency = connection.get("currency", "EUR")
        ET.SubElement(prod, "price").text = f"{product.get('price', 0) or 0:.2f}"
        ET.SubElement(prod, "currency").text = currency
        stock_val = product.get("stock", 0) or 0
        ET.SubElement(prod, "stock").text = str(stock_val)
        ET.SubElement(prod, "availability").text = "in stock" if stock_val > 0 else "out of stock"
        ET.SubElement(prod, "brand").text = pval("brand", product.get("brand", ""))
        ET.SubElement(prod, "image_url").text = pval("image_url", product.get("image_url", ""))
        ET.SubElement(prod, "url").text = connection.get("store_url", "")
        ean = product.get("ean") or product.get("gtin") or product.get("upc") or ""
        if ean:
            ET.SubElement(prod, "ean").text = str(ean)
        category = product.get("category", "")
        if category:
            ET.SubElement(prod, "category").text = category

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def _generate_csv_feed(platform_id: str, products: list, connection: dict) -> str:
    """Generate a CSV feed for Amazon, Idealo or eBay."""
    output = io.StringIO()
    field_map = connection.get("field_mapping", {})

    if platform_id == "amazon":
        fieldnames = ["item_sku", "item_name", "external_product_id", "external_product_id_type",
                      "brand_name", "bullet_point1", "standard_price", "quantity", "main_image_url",
                      "product_description", "parent_sku"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for product in products:
            def pval(field, default=""):
                mapped = field_map.get(field)
                if mapped and mapped in product:
                    return str(product[mapped]) if product[mapped] is not None else default
                return str(product.get(field, default))
            writer.writerow({
                "item_sku": pval("item_sku", product.get("id", "")),
                "item_name": pval("item_name", product.get("name", "")),
                "external_product_id": product.get("ean") or product.get("asin") or "",
                "external_product_id_type": "EAN" if product.get("ean") else "ASIN",
                "brand_name": pval("brand_name", product.get("brand", "")),
                "bullet_point1": pval("bullet_point1", product.get("short_description", "") or ""),
                "standard_price": str(product.get("price", 0) or 0),
                "quantity": str(product.get("stock", 0) or 0),
                "main_image_url": product.get("image_url", ""),
                "product_description": product.get("description", ""),
                "parent_sku": "",
            })
    elif platform_id == "idealo":
        fieldnames = ["sku", "name", "description", "url", "image_url", "price", "brand", "ean",
                      "category", "shipping_costs", "delivery_time", "condition"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        currency = connection.get("currency", "EUR")
        for product in products:
            def pval(field, default=""):
                mapped = field_map.get(field)
                if mapped and mapped in product:
                    return str(product[mapped]) if product[mapped] is not None else default
                return str(product.get(field, default))
            writer.writerow({
                "sku": pval("sku", product.get("id", "")),
                "name": pval("name", product.get("name", "")),
                "description": product.get("description", ""),
                "url": connection.get("store_url", ""),
                "image_url": product.get("image_url", ""),
                "price": f"{product.get('price', 0) or 0:.2f} {currency}",
                "brand": product.get("brand", ""),
                "ean": product.get("ean") or product.get("gtin") or "",
                "category": product.get("category", ""),
                "shipping_costs": connection.get("shipping_cost", ""),
                "delivery_time": connection.get("delivery_time", ""),
                "condition": connection.get("condition", "new"),
            })
    elif platform_id == "ebay":
        fieldnames = ["Action", "ItemID", "Title", "Description", "PrimaryCategory",
                      "StartPrice", "Quantity", "ConditionID", "PicURL", "Brand", "EAN"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for product in products:
            def pval(field, default=""):
                mapped = field_map.get(field)
                if mapped and mapped in product:
                    return str(product[mapped]) if product[mapped] is not None else default
                return str(product.get(field, default))
            writer.writerow({
                "Action": "Add",
                "ItemID": "",
                "Title": pval("Title", product.get("name", "")),
                "Description": product.get("description", ""),
                "PrimaryCategory": product.get("category", ""),
                "StartPrice": str(product.get("price", 0) or 0),
                "Quantity": str(product.get("stock", 0) or 0),
                "ConditionID": "1000",
                "PicURL": product.get("image_url", ""),
                "Brand": product.get("brand", ""),
                "EAN": product.get("ean") or product.get("gtin") or "",
            })
    else:
        # Generic CSV
        fieldnames = ["id", "name", "description", "price", "stock", "brand", "ean", "image_url", "category"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for product in products:
            writer.writerow({
                "id": product.get("id", ""),
                "name": product.get("name", ""),
                "description": product.get("description", ""),
                "price": str(product.get("price", 0) or 0),
                "stock": str(product.get("stock", 0) or 0),
                "brand": product.get("brand", ""),
                "ean": product.get("ean") or product.get("gtin") or "",
                "image_url": product.get("image_url", ""),
                "category": product.get("category", ""),
            })

    return output.getvalue()


# ==================== ROUTES ====================

@router.get("/marketplaces/platforms")
async def get_marketplace_platforms(user: dict = Depends(get_current_user)):
    """Get list of supported marketplace platforms."""
    return list(MARKETPLACE_PLATFORMS.values())


@router.get("/marketplaces/connections")
async def get_marketplace_connections(user: dict = Depends(get_current_user)):
    """Get all marketplace connections for the current user."""
    connections = await db.marketplace_connections.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    return connections


@router.post("/marketplaces/connections")
async def create_marketplace_connection(
    data: dict,
    user: dict = Depends(get_current_user)
):
    """Create a new marketplace connection."""
    await _check_marketplace_limit(user)

    platform_id = data.get("platform_id")
    if not platform_id or platform_id not in MARKETPLACE_PLATFORMS:
        raise HTTPException(status_code=400, detail="Plataforma de marketplace no válida")

    catalog_id = data.get("catalog_id")
    if not catalog_id:
        raise HTTPException(status_code=400, detail="Debes seleccionar un catálogo")

    # Validate catalog belongs to user
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    connection_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    connection = {
        "id": connection_id,
        "user_id": user["id"],
        "platform_id": platform_id,
        "platform_name": MARKETPLACE_PLATFORMS[platform_id]["name"],
        "name": data.get("name", MARKETPLACE_PLATFORMS[platform_id]["name"]),
        "catalog_id": catalog_id,
        "catalog_name": catalog.get("name", ""),
        "store_url": data.get("store_url", ""),
        "currency": data.get("currency", "EUR"),
        "condition": data.get("condition", "new"),
        "shipping_cost": data.get("shipping_cost", ""),
        "delivery_time": data.get("delivery_time", ""),
        "field_mapping": data.get("field_mapping", {}),
        "include_out_of_stock": data.get("include_out_of_stock", False),
        "is_active": True,
        "feed_format": MARKETPLACE_PLATFORMS[platform_id]["feed_format"],
        "last_generated": None,
        "products_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    await db.marketplace_connections.insert_one(connection)
    connection.pop("_id", None)
    logger.info(f"Marketplace connection created: {connection_id} for user {user['id']} - platform {platform_id}")
    return connection


@router.get("/marketplaces/connections/{connection_id}")
async def get_marketplace_connection(
    connection_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific marketplace connection."""
    connection = await db.marketplace_connections.find_one(
        {"id": connection_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not connection:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    return connection


@router.put("/marketplaces/connections/{connection_id}")
async def update_marketplace_connection(
    connection_id: str,
    data: dict,
    user: dict = Depends(get_current_user)
):
    """Update a marketplace connection."""
    connection = await db.marketplace_connections.find_one(
        {"id": connection_id, "user_id": user["id"]}
    )
    if not connection:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")

    allowed_fields = [
        "name", "store_url", "currency", "condition", "shipping_cost",
        "delivery_time", "field_mapping", "include_out_of_stock", "is_active"
    ]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    # If catalog_id changes, validate new catalog
    if "catalog_id" in data and data["catalog_id"] != connection.get("catalog_id"):
        catalog = await db.catalogs.find_one({"id": data["catalog_id"], "user_id": user["id"]})
        if not catalog:
            raise HTTPException(status_code=404, detail="Catálogo no encontrado")
        update_data["catalog_id"] = data["catalog_id"]
        update_data["catalog_name"] = catalog.get("name", "")

    update_data["updated_at"] = datetime.now(UTC).isoformat()

    await db.marketplace_connections.update_one(
        {"id": connection_id},
        {"$set": update_data}
    )

    updated = await db.marketplace_connections.find_one({"id": connection_id}, {"_id": 0})
    return updated


@router.delete("/marketplaces/connections/{connection_id}")
async def delete_marketplace_connection(
    connection_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a marketplace connection."""
    result = await db.marketplace_connections.delete_one(
        {"id": connection_id, "user_id": user["id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    return {"message": "Conexión eliminada correctamente"}


@router.get("/marketplaces/feeds/{connection_id}/feed")
async def get_marketplace_feed(connection_id: str):
    """
    Public endpoint to retrieve the generated feed for a marketplace connection.
    No authentication required — the connection_id acts as the access token.
    Supports ?format=xml|csv query parameter override.
    """
    connection = await db.marketplace_connections.find_one(
        {"id": connection_id, "is_active": True}, {"_id": 0}
    )
    if not connection:
        raise HTTPException(status_code=404, detail="Feed no encontrado o inactivo")

    user_id = connection["user_id"]
    catalog_id = connection["catalog_id"]
    platform_id = connection["platform_id"]
    feed_format = connection.get("feed_format", "xml")

    # Fetch catalog items with their products
    catalog_items = await db.catalog_items.find(
        {"catalog_id": catalog_id}, {"_id": 0}
    ).to_list(10000)

    if not catalog_items:
        # Try fetching products directly from the catalog's supplier
        catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user_id}, {"_id": 0})
        if not catalog:
            raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    # Build product list from catalog items
    products = []
    include_out_of_stock = connection.get("include_out_of_stock", False)

    for item in catalog_items:
        product_id = item.get("product_id")
        if not product_id:
            continue
        product = await db.products.find_one({"id": product_id, "user_id": user_id}, {"_id": 0})
        if not product:
            continue

        stock = product.get("stock", 0) or 0
        if not include_out_of_stock and stock <= 0:
            continue

        # Use catalog item price if set, otherwise product price
        price = item.get("custom_price") or item.get("final_price") or product.get("price") or 0
        products.append({**product, "price": price})

    # Update last_generated and products_count
    await db.marketplace_connections.update_one(
        {"id": connection_id},
        {"$set": {
            "last_generated": datetime.now(UTC).isoformat(),
            "products_count": len(products)
        }}
    )

    if feed_format == "csv":
        content = _generate_csv_feed(platform_id, products, connection)
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{platform_id}_feed.csv"'}
        )
    else:
        content = _generate_xml_feed(platform_id, products, connection)
        return Response(
            content=content,
            media_type="application/xml; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{platform_id}_feed.xml"'}
        )


@router.post("/marketplaces/connections/{connection_id}/preview")
async def preview_marketplace_feed(
    connection_id: str,
    user: dict = Depends(get_current_user)
):
    """Preview the first 5 products of a marketplace feed (authenticated)."""
    connection = await db.marketplace_connections.find_one(
        {"id": connection_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not connection:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")

    catalog_id = connection["catalog_id"]
    include_out_of_stock = connection.get("include_out_of_stock", False)

    catalog_items = await db.catalog_items.find(
        {"catalog_id": catalog_id}, {"_id": 0}
    ).to_list(50)

    products = []
    for item in catalog_items:
        product_id = item.get("product_id")
        if not product_id:
            continue
        product = await db.products.find_one({"id": product_id, "user_id": user["id"]}, {"_id": 0})
        if not product:
            continue
        stock = product.get("stock", 0) or 0
        if not include_out_of_stock and stock <= 0:
            continue
        price = item.get("custom_price") or item.get("final_price") or product.get("price") or 0
        products.append({**product, "price": price})
        if len(products) >= 5:
            break

    return {
        "platform": connection.get("platform_name"),
        "format": connection.get("feed_format"),
        "total_products_preview": len(products),
        "products": products,
    }


# ==================== ADMIN: STATS ====================

@router.get("/marketplaces/stats")
async def get_marketplace_stats(superadmin: dict = Depends(get_superadmin_user)):
    """SuperAdmin: get marketplace usage statistics."""
    total_connections = await db.marketplace_connections.count_documents({})
    active_connections = await db.marketplace_connections.count_documents({"is_active": True})

    pipeline = [
        {"$group": {"_id": "$platform_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_platform = await db.marketplace_connections.aggregate(pipeline).to_list(100)

    return {
        "total_connections": total_connections,
        "active_connections": active_connections,
        "by_platform": by_platform,
    }
