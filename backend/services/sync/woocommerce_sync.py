"""
Integración con tiendas WooCommerce, Shopify, PrestaShop, Magento y Wix.
Sincronización de precios/stock y creación de catálogos desde tiendas.
"""
import asyncio
import json
import logging
import re
import uuid
from datetime import UTC, datetime

from woocommerce import API as WooCommerceAPI

from config import WOOCOMMERCE_API_TIMEOUT
from services.database import db
from services.sync.notifications import send_realtime_notification
from services.sync.utils import calculate_final_price, extract_store_product_info

logger = logging.getLogger(__name__)


def get_woocommerce_client(config: dict) -> WooCommerceAPI:
    return WooCommerceAPI(
        url=config['store_url'],
        consumer_key=config['consumer_key'],
        consumer_secret=config['consumer_secret'],
        version="wc/v3",
        timeout=WOOCOMMERCE_API_TIMEOUT
    )


async def sync_woocommerce_store_price_stock(config: dict):
    store_name = config.get("name", "Unknown")
    catalog_id = config.get("catalog_id")
    if not catalog_id:
        logger.warning(f"No catalog associated with WooCommerce store {store_name}")
        return
    logger.info(f"Starting price/stock sync for WooCommerce store: {store_name}")
    try:
        wcapi = get_woocommerce_client(config)
        catalog_items = await db.catalog_items.find({"catalog_id": catalog_id, "active": True}).to_list(10000)
        if not catalog_items:
            logger.info(f"No active products in catalog for store {store_name}")
            return
        margin_rules = await db.catalog_margin_rules.find({"catalog_id": catalog_id}).to_list(100)
        wc_products_by_ean = {}
        wc_products_by_sku = {}
        page = 1
        while True:
            response = await asyncio.to_thread(wcapi.get, "products", params={"per_page": 100, "page": page})
            if response.status_code == 200:
                products_batch = response.json()
                if not products_batch:
                    break
                for p in products_batch:
                    for meta in p.get("meta_data", []):
                        if meta.get("key") in ["_global_unique_id", "_gtin", "_ean", "gtin"]:
                            ean_value = meta.get("value")
                            if ean_value:
                                wc_products_by_ean[ean_value] = p["id"]
                                break
                    if p.get("sku"):
                        wc_products_by_sku[p["sku"]] = p["id"]
                page += 1
                if len(products_batch) < 100:
                    break
            else:
                logger.error(f"Error fetching WooCommerce products: {response.text}")
                break
        logger.info(f"Found {len(wc_products_by_ean)} products by EAN, {len(wc_products_by_sku)} by SKU")
        updated = 0
        failed = 0
        for item in catalog_items:
            try:
                product = await db.products.find_one({"id": item["product_id"]})
                if not product:
                    continue
                base_price = item.get("custom_price") or product.get("price", 0)
                final_price = calculate_final_price(base_price, product, margin_rules)
                ean = product.get("ean", "")
                sku = product.get("sku", "")
                wc_product_id = wc_products_by_ean.get(ean) if ean else None
                if not wc_product_id and sku:
                    wc_product_id = wc_products_by_sku.get(sku)
                if wc_product_id:
                    update_data = {"regular_price": str(round(final_price, 2)), "stock_quantity": product.get("stock", 0)}
                    response = await asyncio.to_thread(wcapi.put, f"products/{wc_product_id}", update_data)
                    if response.status_code in [200, 201]:
                        updated += 1
                    else:
                        failed += 1
                        logger.warning(f"Failed to update product {ean or sku}: {response.text[:100]}")
            except Exception as e:
                failed += 1
                logger.error(f"Error processing catalog item: {e}")
        now = datetime.now(UTC).isoformat()
        await db.woocommerce_configs.update_one(
            {"id": config["id"]},
            {"$set": {"last_sync": now, "products_synced": updated}}
        )
        logger.info(f"WooCommerce sync completed for {store_name}: {updated} updated, {failed} failed")
    except Exception as e:
        logger.error(f"Error syncing WooCommerce store {store_name}: {e}")


async def sync_all_woocommerce_stores():
    from services.unified_sync import _global_sync_lock
    logger.info("Starting scheduled WooCommerce sync for all stores (waiting for global lock)...")
    async with _global_sync_lock:
        configs = await db.woocommerce_configs.find({
            "auto_sync_enabled": True,
            "catalog_id": {"$nin": [None, ""]}
        }).to_list(1000)
        logger.info(f"Found {len(configs)} WooCommerce stores with auto-sync enabled")
        for config in configs:
            try:
                await sync_woocommerce_store_price_stock(config)
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error syncing WooCommerce store {config.get('name', config['id'])}: {e}")
        logger.info("Scheduled WooCommerce sync completed")


def get_woocommerce_categories_sync(config: dict) -> list:
    """Obtiene todas las categorias de WooCommerce"""
    wcapi = get_woocommerce_client(config)
    categories = []
    page = 1
    try:
        while True:
            response = wcapi.get("products/categories", params={"per_page": 100, "page": page})
            if response.status_code == 200:
                batch = response.json()
                if not batch:
                    break
                categories.extend(batch)
                page += 1
                if len(batch) < 100:
                    break
            else:
                logger.error(f"Error fetching WooCommerce categories: {response.text[:200]}")
                break
    except Exception as e:
        logger.error(f"WooCommerce get_categories error: {e}")
    return categories


async def get_woocommerce_categories(config: dict) -> list:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, get_woocommerce_categories_sync, config)


def create_woocommerce_category_sync(config: dict, category_data: dict) -> dict:
    """Crea una categoria en WooCommerce"""
    wcapi = get_woocommerce_client(config)
    try:
        payload = {
            "name": category_data.get("name", ""),
            "parent": category_data.get("parent_id", 0),
            "description": category_data.get("description", "")
        }
        response = wcapi.post("products/categories", payload)
        if response.status_code in [200, 201]:
            cat = response.json()
            return {"status": "success", "category_id": cat.get("id"), "message": "Categoria creada"}
        else:
            return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}


async def create_woocommerce_category(config: dict, category_data: dict) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, create_woocommerce_category_sync, config, category_data)


async def find_or_create_woocommerce_category(config: dict, name: str, parent_id: int = 0, existing_categories: list = None) -> int:
    """Busca una categoria existente por nombre o la crea"""
    if existing_categories is None:
        existing_categories = await get_woocommerce_categories(config)
    for cat in existing_categories:
        if cat.get("name", "").lower() == name.lower() and cat.get("parent", 0) == parent_id:
            return cat.get("id")
    result = await create_woocommerce_category(config, {"name": name, "parent_id": parent_id})
    if result.get("status") == "success":
        return result.get("category_id")
    return None


async def export_catalog_categories_to_woocommerce(config: dict, catalog_id: str, user_id: str) -> dict:
    """Exporta categorias del catalogo a la tienda WooCommerce"""
    categories = await db.catalog_categories.find(
        {"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
    ).sort("position", 1).to_list(500)

    if not categories:
        return {"status": "warning", "created": 0, "message": "No hay categorias para exportar"}

    wc_categories = await get_woocommerce_categories(config)
    category_mapping = {}
    created = 0
    errors = []

    max_level = max(cat.get("level", 0) for cat in categories)
    for level in range(max_level + 1):
        level_cats = [c for c in categories if c.get("level", 0) == level]
        for cat in level_cats:
            try:
                wc_parent_id = 0
                if cat.get("parent_id") and cat["parent_id"] in category_mapping:
                    wc_parent_id = category_mapping[cat["parent_id"]]
                wc_id = await find_or_create_woocommerce_category(
                    config, cat["name"], wc_parent_id, wc_categories
                )
                if wc_id:
                    category_mapping[cat["id"]] = wc_id
                    was_existing = any(
                        wc.get("name", "").lower() == cat["name"].lower() and wc.get("parent", 0) == wc_parent_id
                        for wc in wc_categories
                    )
                    if not was_existing:
                        created += 1
                        wc_categories.append({"id": wc_id, "name": cat["name"], "parent": wc_parent_id})
                else:
                    errors.append(f"Error creando categoria: {cat['name']}")
            except Exception as e:
                errors.append(f"Error procesando {cat['name']}: {str(e)[:50]}")

    return {
        "status": "success" if not errors else "partial",
        "created": created,
        "total": len(categories),
        "mapped": len(category_mapping),
        "category_mapping": category_mapping,
        "errors": errors[:10]
    }


async def fetch_all_store_products(store_config: dict) -> list:
    """
    Obtiene TODOS los productos de una tienda con paginacion.
    Soporta WooCommerce, PrestaShop, Shopify, Magento y Wix.
    """
    from services.platforms import get_platform_client

    platform = store_config.get("platform", "woocommerce")
    store_products = []

    if platform == "woocommerce":
        wc = get_woocommerce_client(store_config)
        page = 1
        while True:
            batch = await asyncio.to_thread(
                wc.get, "products", params={"per_page": 100, "page": page}
            )
            if hasattr(batch, 'json'):
                try:
                    batch = batch.json()
                except Exception as e:
                    logger.warning(f"JSON decode error on page {page}: {type(e).__name__}: {str(e)[:150]}")
                    try:
                        if hasattr(batch, 'content'):
                            raw_bytes = batch.content
                            parsed_data = None
                            text = None
                            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']:
                                try:
                                    text = raw_bytes.decode(encoding)
                                    parsed_data = json.loads(text)
                                    batch = parsed_data
                                    break
                                except (json.JSONDecodeError, UnicodeDecodeError):
                                    if encoding == 'utf-8' and text is None:
                                        try:
                                            text = raw_bytes.decode('utf-8', errors='replace')
                                        except Exception:
                                            pass
                                    continue
                            if parsed_data is None and text:
                                try:
                                    sanitized = re.sub(r'\\([^"\\/bfnrtu])', r'\1', text)
                                    parsed_data = json.loads(sanitized)
                                    batch = parsed_data
                                except Exception:
                                    if text:
                                        text_replaced = raw_bytes.decode('utf-8', errors='replace')
                                        parsed_data = json.loads(text_replaced)
                                        batch = parsed_data
                            if parsed_data is None:
                                raise ValueError(f"Could not parse JSON response on page {page}")
                        else:
                            raise e
                    except Exception as fallback_error:
                        logger.error(f"Failed to parse WooCommerce response on page {page}: {fallback_error}")
                        raise

            if isinstance(batch, dict) and "body" in batch:
                batch = batch["body"]
            if not batch or not isinstance(batch, list):
                break
            store_products.extend(batch)
            if len(batch) < 100:
                break
            page += 1
    else:
        client = get_platform_client(store_config)
        if client and hasattr(client, 'get_all_products'):
            store_products = await asyncio.to_thread(client.get_all_products)
        elif client:
            store_products = await asyncio.to_thread(client.get_products, 100)

    return store_products


async def create_catalog_from_store_products(
    user_id: str,
    store_config_id: str,
    catalog_name: str | None = None,
    catalog_id: str | None = None,
    match_by: list[str] | None = None,
    skip_unmatched: bool = True
) -> dict:
    """
    Crea un catalogo con productos de una tienda cruzandolos con productos de proveedores.

    Solo se anaden productos que coincidan con productos de proveedor.
    El precio siempre proviene del producto de proveedor encontrado.
    """
    if match_by is None:
        match_by = ["sku", "ean", "name"]

    errors = []
    now = datetime.now(UTC).isoformat()
    created_products = 0
    catalog = None
    store_products = []

    try:
        store_config = await db.woocommerce_configs.find_one(
            {"id": store_config_id, "user_id": user_id}
        )
        if not store_config:
            raise Exception("Configuracion de tienda no encontrada")

        store_name = store_config.get("name", "Tienda")
        platform = store_config.get("platform", "woocommerce")

        await send_realtime_notification(user_id, {
            "id": str(uuid.uuid4()),
            "type": "sync_progress",
            "message": f"Obteniendo productos de '{store_name}'...",
            "progress": 5,
            "processed": 0,
            "total": 0,
        })

        try:
            store_products = await fetch_all_store_products(store_config)
        except Exception as e:
            logger.error(f"Error fetching store products: {e}")
            raise Exception(f"Error al obtener productos de la tienda: {str(e)[:100]}")

        if not store_products:
            raise Exception("No se encontraron productos en la tienda")

        total_store = len(store_products)

        await send_realtime_notification(user_id, {
            "id": str(uuid.uuid4()),
            "type": "sync_progress",
            "message": f"Se encontraron {total_store} productos en '{store_name}'. Preparando catalogo...",
            "progress": 15,
            "processed": 0,
            "total": total_store,
        })

        if catalog_id:
            catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user_id})
            if not catalog:
                raise Exception("Catalogo no encontrado")
        else:
            if not catalog_name:
                catalog_name = f"Catalogo {store_name}"
            catalog_id = str(uuid.uuid4())
            catalog = {
                "id": catalog_id,
                "user_id": user_id,
                "name": catalog_name,
                "description": f"Creado desde productos de {store_name}",
                "is_default": False,
                "created_at": now
            }
            await db.catalogs.insert_one(catalog)

        await send_realtime_notification(user_id, {
            "id": str(uuid.uuid4()),
            "type": "sync_progress",
            "message": "Cargando productos de proveedores para cruzar datos...",
            "progress": 20,
            "processed": 0,
            "total": total_store,
        })

        supplier_products = await db.products.find(
            {"user_id": user_id}, {"_id": 0}
        ).to_list(None)

        products_by_sku = {}
        products_by_ean = {}
        products_by_name = {}

        for prod in supplier_products:
            sku = (prod.get("sku") or "").lower().strip()
            ean = (prod.get("ean") or "").lower().strip()
            name = (prod.get("name") or "").lower().strip()
            if sku:
                products_by_sku[sku] = prod
            if ean:
                products_by_ean[ean] = prod
            if name and len(name) > 3:
                if name not in products_by_name:
                    products_by_name[name] = []
                products_by_name[name].append(prod)

        matched = 0
        unmatched = 0
        added_items = 0
        catalog_items = []

        for i, store_prod in enumerate(store_products):
            matched_product = None
            info = extract_store_product_info(store_prod, platform)
            store_sku = info["sku"].lower()
            store_ean = info["ean"].lower()
            store_product_name = info["name"].lower()

            if "sku" in match_by and store_sku and store_sku in products_by_sku:
                matched_product = products_by_sku[store_sku]
            if not matched_product and "ean" in match_by and store_ean and store_ean in products_by_ean:
                matched_product = products_by_ean[store_ean]
            if not matched_product and "name" in match_by and store_product_name and store_product_name in products_by_name:
                matched_product = products_by_name[store_product_name][0]

            if matched_product:
                matched += 1
                catalog_items.append({
                    "id": str(uuid.uuid4()),
                    "catalog_id": catalog_id,
                    "product_id": matched_product["id"],
                    "custom_price": None,
                    "custom_name": None,
                    "active": True,
                    "category_ids": [],
                    "created_at": now
                })
                added_items += 1
            else:
                unmatched += 1

            if (i + 1) % 50 == 0 or (i + 1) == total_store:
                pct = 20 + int(((i + 1) / total_store) * 70)
                await send_realtime_notification(user_id, {
                    "id": str(uuid.uuid4()),
                    "type": "sync_progress",
                    "message": f"Cruzando productos: {i + 1}/{total_store} ({matched} encontrados)",
                    "progress": pct,
                    "processed": i + 1,
                    "total": total_store,
                })

        if catalog_items:
            try:
                await db.catalog_items.insert_many(catalog_items, ordered=False)
            except Exception as e:
                if "duplicate" in str(e).lower() or "11000" in str(e):
                    logger.warning(f"Some catalog items have duplicate keys: {str(e)[:100]}")
                    inserted = 0
                    for item in catalog_items:
                        try:
                            await db.catalog_items.insert_one(item)
                            inserted += 1
                        except Exception as item_error:
                            if "duplicate" not in str(item_error).lower() and "11000" not in str(item_error):
                                logger.error(f"Error inserting catalog item {item['id']}: {item_error}")
                    logger.info(f"Inserted {inserted}/{len(catalog_items)} catalog items (skipped duplicates)")
                else:
                    raise

        await send_realtime_notification(user_id, {
            "id": str(uuid.uuid4()),
            "type": "sync_complete",
            "message": f"Catalogo '{catalog['name']}' creado: {matched} coincidencias, {unmatched} sin coincidencia, {added_items} anadidos al catalogo",
        })

        return {
            "status": "success",
            "catalog_id": catalog["id"],
            "catalog_name": catalog["name"],
            "total_products": total_store,
            "matched_products": matched,
            "unmatched_products": unmatched,
            "added_items": added_items,
            "created_products": created_products,
            "errors": errors,
            "created_at": now,
        }

    except Exception as e:
        logger.error(f"Error creating catalog from store: {e}")
        await send_realtime_notification(user_id, {
            "id": str(uuid.uuid4()),
            "type": "sync_error",
            "message": f"Error creando catalogo desde tienda: {str(e)[:100]}",
        })
        return {
            "status": "error",
            "catalog_id": catalog["id"] if catalog else (catalog_id if catalog_id else None),
            "catalog_name": catalog["name"] if catalog else (catalog_name or ""),
            "total_products": len(store_products),
            "matched_products": 0,
            "unmatched_products": 0,
            "added_items": 0,
            "created_products": 0,
            "errors": [str(e)],
            "created_at": now,
        }
