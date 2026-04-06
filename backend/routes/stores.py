import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from services.auth import check_user_limit, get_current_user
from services.database import db
from services.platforms import MagentoClient, PrestaShopClient, ShopifyClient, WixClient
from services.sync import calculate_final_price, get_woocommerce_client, mask_key, sync_woocommerce_store_price_stock

router = APIRouter()
logger = logging.getLogger(__name__)

# Supported platforms configuration
SUPPORTED_PLATFORMS = {
    "woocommerce": {
        "name": "WooCommerce",
        "required_fields": ["store_url", "consumer_key", "consumer_secret"],
        "credential_fields": ["consumer_key", "consumer_secret"]
    },
    "prestashop": {
        "name": "PrestaShop",
        "required_fields": ["store_url", "api_key"],
        "credential_fields": ["api_key"]
    },
    "shopify": {
        "name": "Shopify",
        "required_fields": ["store_url", "access_token"],
        "credential_fields": ["access_token"]
    },
    "wix": {
        "name": "Wix eCommerce",
        "required_fields": ["store_url", "api_key", "site_id"],
        "credential_fields": ["api_key"]
    },
    "magento": {
        "name": "Magento",
        "required_fields": ["store_url", "access_token"],
        "credential_fields": ["access_token"]
    }
}


def get_masked_credentials(config: dict) -> dict:
    """Mask sensitive credentials for API response"""
    platform = config.get("platform", "woocommerce")
    platform_config = SUPPORTED_PLATFORMS.get(platform, SUPPORTED_PLATFORMS["woocommerce"])

    masked = {}
    for field in platform_config.get("credential_fields", []):
        if config.get(field):
            masked[f"{field}_masked"] = mask_key(config[field])
    return masked


@router.post("/stores/configs")
async def create_store_config(config: dict, user: dict = Depends(get_current_user)):
    """Create a new store configuration for any supported platform"""
    # Check user limit
    can_create = await check_user_limit(user, "woocommerce_stores")
    if not can_create:
        raise HTTPException(
            status_code=403,
            detail=f"Has alcanzado el límite de tiendas. Máximo: {user.get('max_woocommerce_stores', 2)}"
        )

    platform = config.get("platform", "woocommerce")
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Plataforma no soportada: {platform}")

    platform_config = SUPPORTED_PLATFORMS[platform]

    # Validate required fields
    for field in platform_config["required_fields"]:
        if not config.get(field):
            raise HTTPException(status_code=400, detail=f"Campo requerido: {field}")

    config_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    # Get catalog name if provided
    catalog_name = None
    if config.get("catalog_id"):
        catalog = await db.catalogs.find_one({"id": config["catalog_id"], "user_id": user["id"]})
        if catalog:
            catalog_name = catalog.get("name")

    # Build config document
    config_doc = {
        "id": config_id,
        "user_id": user["id"],
        "platform": platform,
        "name": config.get("name") or f"Mi Tienda {platform_config['name']}",
        "store_url": config.get("store_url", "").rstrip('/'),
        "catalog_id": config.get("catalog_id"),
        "auto_sync_enabled": config.get("auto_sync_enabled", False),
        "is_connected": False,
        "last_sync": None,
        "products_synced": 0,
        "created_at": now
    }

    # Add platform-specific credentials
    for field in platform_config.get("credential_fields", []):
        if config.get(field):
            config_doc[field] = config[field]

    # Add optional platform-specific fields
    if platform == "shopify" and config.get("api_version"):
        config_doc["api_version"] = config["api_version"]
    if platform == "wix" and config.get("site_id"):
        config_doc["site_id"] = config["site_id"]
    if platform == "magento" and config.get("store_code"):
        config_doc["store_code"] = config.get("store_code", "default")

    await db.woocommerce_configs.insert_one(config_doc)

    # Build response
    response = {
        "id": config_id,
        "platform": platform,
        "name": config_doc["name"],
        "store_url": config_doc["store_url"],
        "is_connected": False,
        "last_sync": None,
        "products_synced": 0,
        "created_at": now,
        "catalog_id": config.get("catalog_id"),
        "catalog_name": catalog_name,
        "auto_sync_enabled": config.get("auto_sync_enabled", False),
        **get_masked_credentials(config_doc)
    }

    return response


@router.get("/stores/configs")
async def get_store_configs(user: dict = Depends(get_current_user)):
    """Get all store configurations for the current user"""
    # Exclude sensitive credential fields from response
    projection = {"_id": 0}
    for platform_config in SUPPORTED_PLATFORMS.values():
        for field in platform_config.get("credential_fields", []):
            projection[field] = 0

    # We need to include credentials for masking, so don't exclude them in projection
    configs = await db.woocommerce_configs.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(100)

    # Get catalog names
    catalog_ids = [c.get("catalog_id") for c in configs if c.get("catalog_id")]
    catalogs = {}
    if catalog_ids:
        catalog_docs = await db.catalogs.find({"id": {"$in": catalog_ids}}).to_list(100)
        catalogs = {c["id"]: c.get("name") for c in catalog_docs}

    result = []
    for c in configs:
        platform = c.get("platform", "woocommerce")
        next_sync = None
        if c.get("auto_sync_enabled") and c.get("last_sync"):
            last_sync_dt = datetime.fromisoformat(c["last_sync"].replace('Z', '+00:00'))
            next_sync = (last_sync_dt + timedelta(hours=12)).isoformat()
        elif c.get("auto_sync_enabled"):
            next_sync = (datetime.now(UTC) + timedelta(hours=12)).isoformat()

        item = {
            "id": c["id"],
            "platform": platform,
            "name": c["name"],
            "store_url": c.get("store_url", ""),
            "is_connected": c.get("is_connected", False),
            "last_sync": c.get("last_sync"),
            "products_synced": c.get("products_synced", 0),
            "created_at": c.get("created_at"),
            "catalog_id": c.get("catalog_id"),
            "catalog_name": catalogs.get(c.get("catalog_id")),
            "auto_sync_enabled": c.get("auto_sync_enabled", False),
            "next_sync": next_sync,
            **get_masked_credentials(c)
        }

        # Add platform-specific non-sensitive fields
        if platform == "shopify":
            item["api_version"] = c.get("api_version", "2024-10")
        if platform == "wix":
            item["site_id"] = c.get("site_id")
        if platform == "magento":
            item["store_code"] = c.get("store_code", "default")

        result.append(item)

    return result


@router.get("/stores/configs/{config_id}")
async def get_store_config(config_id: str, user: dict = Depends(get_current_user)):
    """Get a specific store configuration"""
    config = await db.woocommerce_configs.find_one(
        {"id": config_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    platform = config.get("platform", "woocommerce")
    catalog_name = None
    if config.get("catalog_id"):
        catalog = await db.catalogs.find_one({"id": config["catalog_id"]})
        if catalog:
            catalog_name = catalog.get("name")

    next_sync = None
    if config.get("auto_sync_enabled") and config.get("last_sync"):
        last_sync_dt = datetime.fromisoformat(config["last_sync"].replace('Z', '+00:00'))
        next_sync = (last_sync_dt + timedelta(hours=12)).isoformat()
    elif config.get("auto_sync_enabled"):
        next_sync = (datetime.now(UTC) + timedelta(hours=12)).isoformat()

    return {
        "id": config["id"],
        "platform": platform,
        "name": config["name"],
        "store_url": config.get("store_url", ""),
        "is_connected": config.get("is_connected", False),
        "last_sync": config.get("last_sync"),
        "products_synced": config.get("products_synced", 0),
        "created_at": config.get("created_at"),
        "catalog_id": config.get("catalog_id"),
        "catalog_name": catalog_name,
        "auto_sync_enabled": config.get("auto_sync_enabled", False),
        "next_sync": next_sync,
        **get_masked_credentials(config)
    }


@router.put("/stores/configs/{config_id}")
async def update_store_config(config_id: str, update: dict, user: dict = Depends(get_current_user)):
    """Update a store configuration"""
    existing = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    platform = existing.get("platform", "woocommerce")

    # Build update data
    update_data = {}

    # Update basic fields
    for field in ["name", "store_url", "catalog_id", "auto_sync_enabled"]:
        if field in update and update[field] is not None:
            if field == "store_url":
                update_data[field] = update[field].rstrip('/')
            else:
                update_data[field] = update[field]

    # Update platform-specific credential fields (only if provided)
    platform_config = SUPPORTED_PLATFORMS.get(platform, SUPPORTED_PLATFORMS["woocommerce"])
    for field in platform_config.get("credential_fields", []):
        if update.get(field):  # Only update if non-empty value provided
            update_data[field] = update[field]

    # Update platform-specific optional fields
    if platform == "shopify" and update.get("api_version"):
        update_data["api_version"] = update["api_version"]
    if platform == "wix" and update.get("site_id"):
        update_data["site_id"] = update["site_id"]
    if platform == "magento" and update.get("store_code"):
        update_data["store_code"] = update["store_code"]

    if update_data:
        await db.woocommerce_configs.update_one({"id": config_id}, {"$set": update_data})

    # Return updated config
    updated = await db.woocommerce_configs.find_one({"id": config_id}, {"_id": 0})

    catalog_name = None
    if updated.get("catalog_id"):
        catalog = await db.catalogs.find_one({"id": updated["catalog_id"]})
        if catalog:
            catalog_name = catalog.get("name")

    next_sync = None
    if updated.get("auto_sync_enabled") and updated.get("last_sync"):
        last_sync_dt = datetime.fromisoformat(updated["last_sync"].replace('Z', '+00:00'))
        next_sync = (last_sync_dt + timedelta(hours=12)).isoformat()
    elif updated.get("auto_sync_enabled"):
        next_sync = (datetime.now(UTC) + timedelta(hours=12)).isoformat()

    return {
        "id": updated["id"],
        "platform": platform,
        "name": updated["name"],
        "store_url": updated.get("store_url", ""),
        "is_connected": updated.get("is_connected", False),
        "last_sync": updated.get("last_sync"),
        "products_synced": updated.get("products_synced", 0),
        "created_at": updated.get("created_at"),
        "catalog_id": updated.get("catalog_id"),
        "catalog_name": catalog_name,
        "auto_sync_enabled": updated.get("auto_sync_enabled", False),
        "next_sync": next_sync,
        **get_masked_credentials(updated)
    }


@router.delete("/stores/configs/{config_id}")
async def delete_store_config(config_id: str, user: dict = Depends(get_current_user)):
    """Delete a store configuration"""
    result = await db.woocommerce_configs.delete_one({"id": config_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return {"message": "Configuración eliminada"}


@router.post("/stores/configs/{config_id}/test")
async def test_store_connection(config_id: str, user: dict = Depends(get_current_user)):
    """Test connection to a store"""
    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    platform = config.get("platform", "woocommerce")

    try:
        if platform == "woocommerce":
            # WooCommerce connection test
            wcapi = get_woocommerce_client(config)
            response = await asyncio.to_thread(wcapi.get, "")
            if response.status_code == 200:
                await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": True}})
                store_info = response.json()
                return {"status": "success", "message": "Conexión exitosa", "store_name": store_info.get("name", config["name"])}
            else:
                await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": False}})
                return {"status": "error", "message": f"Error de conexión: {response.status_code}"}

        elif platform == "prestashop":
            # PrestaShop real connection test
            client = PrestaShopClient(
                store_url=config.get("store_url", ""),
                api_key=config.get("api_key", "")
            )
            result = await asyncio.to_thread(client.test_connection)
            is_connected = result.get("status") == "success"
            await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": is_connected}})
            result["store_name"] = config["name"]
            return result

        elif platform == "shopify":
            # Shopify real connection test
            client = ShopifyClient(
                store_url=config.get("store_url", ""),
                access_token=config.get("access_token", ""),
                api_version=config.get("api_version", "2024-10")
            )
            result = await asyncio.to_thread(client.test_connection)
            is_connected = result.get("status") == "success"
            await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": is_connected}})
            if not result.get("store_name"):
                result["store_name"] = config["name"]
            return result

        elif platform == "wix":
            # Wix real connection test
            client = WixClient(
                store_url=config.get("store_url", ""),
                api_key=config.get("api_key", ""),
                site_id=config.get("site_id", "")
            )
            result = await asyncio.to_thread(client.test_connection)
            is_connected = result.get("status") == "success"
            await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": is_connected}})
            result["store_name"] = config["name"]
            return result

        elif platform == "magento":
            # Magento real connection test
            client = MagentoClient(
                store_url=config.get("store_url", ""),
                access_token=config.get("access_token", ""),
                store_code=config.get("store_code", "default")
            )
            result = await asyncio.to_thread(client.test_connection)
            is_connected = result.get("status") == "success"
            await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": is_connected}})
            if not result.get("store_name"):
                result["store_name"] = config["name"]
            return result

        else:
            return {"status": "error", "message": f"Plataforma no soportada: {platform}"}

    except Exception:
        await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": False}})
        return {"status": "error", "message": "Error de conexión a la tienda. Verifica la URL y las credenciales."}


@router.post("/stores/configs/{config_id}/sync")
async def sync_store_price_stock(config_id: str, user: dict = Depends(get_current_user)):
    """Sync price and stock to a store"""
    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    if not config.get("catalog_id"):
        raise HTTPException(status_code=400, detail="No hay catálogo asociado a esta tienda. Configura un catálogo primero.")

    platform = config.get("platform", "woocommerce")

    try:
        if platform == "woocommerce":
            await sync_woocommerce_store_price_stock(config)
            updated = await db.woocommerce_configs.find_one({"id": config_id}, {"_id": 0})
            return {
                "status": "success",
                "message": f"Sincronización completada. {updated.get('products_synced', 0)} productos actualizados.",
                "products_synced": updated.get("products_synced", 0),
                "last_sync": updated.get("last_sync")
            }
        else:
            # For other platforms, simulate sync
            now = datetime.now(UTC).isoformat()
            await db.woocommerce_configs.update_one(
                {"id": config_id},
                {"$set": {"last_sync": now, "products_synced": 0}}
            )
            return {
                "status": "success",
                "message": f"Sincronización programada para {SUPPORTED_PLATFORMS.get(platform, {}).get('name', platform)}. La integración completa está en desarrollo.",
                "products_synced": 0,
                "last_sync": now
            }
    except Exception as e:
        logger.error(f"Error in store sync: {e}")
        return {"status": "error", "message": "Error en la sincronización con la tienda"}


async def _run_export_background(config: dict, catalog_items: list, catalog_id: str,
                                  update_existing: bool, platform: str, user: dict):
    """Background task: runs the full export and saves a notification with results."""
    config_id = config["id"]
    store_name = config.get("name", config_id)
    try:
        if platform == "woocommerce":
            from models.schemas import WooCommerceExportRequest
            from routes.woocommerce import export_to_woocommerce
            wc_request = WooCommerceExportRequest(
                config_id=config_id,
                catalog_id=catalog_id,
                update_existing=update_existing
            )
            result = await export_to_woocommerce(wc_request, user)
            summary = f"Exportación WooCommerce '{store_name}': {result.created} creados, {result.updated} actualizados, {result.failed} errores"
            errors_detail = "; ".join(result.errors[:5]) if result.errors else ""
        elif platform == "prestashop":
            result = await export_to_prestashop(config, catalog_items, catalog_id, user)
            summary = f"Exportación PrestaShop '{store_name}': {result['created']} creados, {result['updated']} actualizados, {result['failed']} errores"
            errors_detail = "; ".join(result.get("errors", [])[:5])
        elif platform == "shopify":
            result = await export_to_shopify(config, catalog_items, catalog_id, user)
            summary = f"Exportación Shopify '{store_name}': {result['created']} creados, {result['updated']} actualizados, {result['failed']} errores"
            errors_detail = "; ".join(result.get("errors", [])[:5])
        elif platform == "magento":
            result = await export_to_magento(config, catalog_items, catalog_id, user)
            summary = f"Exportación Magento '{store_name}': {result['created']} creados, {result['updated']} actualizados, {result['failed']} errores"
            errors_detail = "; ".join(result.get("errors", [])[:5])
        elif platform == "wix":
            result = await export_to_wix(config, catalog_items, catalog_id, user)
            summary = f"Exportación Wix '{store_name}': {result['created']} creados, {result['updated']} actualizados, {result['failed']} errores"
            errors_detail = "; ".join(result.get("errors", [])[:5])
        else:
            summary = f"Plataforma '{platform}' no soportada"
            errors_detail = ""

        if errors_detail:
            summary += f". Errores: {errors_detail}"
    except Exception as e:
        summary = f"Error en exportación de '{store_name}': {str(e)[:200]}"
        logger.error(f"Background export error for store {config_id}: {e}")

    now = datetime.now(UTC).isoformat()
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "type": "store_export",
        "message": summary,
        "product_id": None,
        "product_name": None,
        "user_id": user["id"],
        "read": False,
        "created_at": now
    })


@router.post("/stores/export")
async def export_to_store(request: dict, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """Export products to a store — runs in background to avoid gateway timeouts."""
    config_id = request.get("config_id")
    catalog_id = request.get("catalog_id")
    update_existing = request.get("update_existing", True)

    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de tienda no encontrada")

    platform = config.get("platform", "woocommerce")

    # Validate catalog and fetch items synchronously before returning
    if not catalog_id:
        raise HTTPException(status_code=400, detail="Catálogo no especificado")
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    catalog_items = await db.catalog_items.find({"catalog_id": catalog_id, "active": True}, {"_id": 0}).to_list(1000)
    if not catalog_items:
        return {"status": "warning", "created": 0, "updated": 0, "failed": 0,
                "errors": ["No hay productos activos para exportar"]}

    if platform not in SUPPORTED_PLATFORMS and platform != "woocommerce":
        return {"status": "error", "created": 0, "updated": 0, "failed": 0,
                "errors": [f"Plataforma {platform} no soportada para exportación"]}

    # Launch export in background — returns immediately to avoid 504 timeout
    background_tasks.add_task(
        _run_export_background, config, catalog_items, catalog_id, update_existing, platform, user
    )

    return {
        "status": "started",
        "message": f"Exportación iniciada en segundo plano ({len(catalog_items)} productos). Recibirás una notificación al finalizar.",
        "total_products": len(catalog_items)
    }


async def export_to_prestashop(config: dict, catalog_items: list, catalog_id: str, user: dict) -> dict:
    """Export products to PrestaShop with full product data"""

    client = PrestaShopClient(
        store_url=config.get("store_url", ""),
        api_key=config.get("api_key", "")
    )

    created = 0
    updated = 0
    failed = 0
    errors = []

    # Get products data
    product_ids = [item["product_id"] for item in catalog_items]
    products = await db.products.find({"id": {"$in": product_ids}}, {"_id": 0}).to_list(len(product_ids))
    products_map = {p["id"]: p for p in products}

    # Get existing products from PrestaShop by reference (SKU)
    existing_products = client.get_products(limit=5000)
    existing_refs = {}
    for p in existing_products:
        ref = p.get("reference", "")
        if ref:
            existing_refs[ref] = p.get("id")

    # Get margin rules for this catalog
    margin_rules = await db.catalog_margin_rules.find({"catalog_id": catalog_id}, {"_id": 0}).sort("priority", -1).to_list(100)

    for item in catalog_items:
        product = products_map.get(item["product_id"])
        if not product:
            failed += 1
            errors.append(f"Producto no encontrado: {item['product_id']}")
            continue

        try:
            base_price = item.get("custom_price") or product.get("price", 0)
            final_price = calculate_final_price(base_price, product, margin_rules)

            product_data = {
                "sku": product.get("sku", ""),
                "ean": product.get("ean", ""),
                "name": item.get("custom_name") or product.get("name", ""),
                "price": round(final_price, 2),
                "stock": product.get("stock", 0),
                "short_description": product.get("short_description", ""),
                "long_description": product.get("long_description") or product.get("description", ""),
                "brand": product.get("brand", ""),
                "weight": product.get("weight", 0),
                "image_url": product.get("image_url", ""),
                "gallery_images": product.get("gallery_images", []),
                "category": product.get("category", "")
            }

            # Check if product exists
            existing_id = existing_refs.get(product.get("sku", ""))

            if existing_id:
                result = client.update_product(int(existing_id), product_data)
                if result.get("status") == "success":
                    updated += 1
                else:
                    failed += 1
                    errors.append(f"{product.get('sku')}: {result.get('message')}")
            else:
                result = client.create_product(product_data)
                if result.get("status") == "success":
                    created += 1
                else:
                    failed += 1
                    errors.append(f"{product.get('sku')}: {result.get('message')}")
        except Exception as e:
            failed += 1
            errors.append(f"{product.get('sku', 'unknown')}: {str(e)}")

    # Update config
    now = datetime.now(UTC).isoformat()
    await db.woocommerce_configs.update_one(
        {"id": config["id"]},
        {"$set": {"last_sync": now, "products_synced": created + updated}}
    )

    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "type": "store_export",
        "message": f"Exportación a PrestaShop: {created} creados, {updated} actualizados, {failed} fallidos",
        "product_id": None,
        "product_name": None,
        "user_id": user["id"],
        "read": False,
        "created_at": now
    })

    return {
        "status": "success" if failed == 0 else "partial",
        "created": created,
        "updated": updated,
        "failed": failed,
        "errors": errors[:10]
    }


async def export_to_shopify(config: dict, catalog_items: list, catalog_id: str, user: dict) -> dict:
    """Export products to Shopify with full product data"""

    client = ShopifyClient(
        store_url=config.get("store_url", ""),
        access_token=config.get("access_token", "")
    )

    created = 0
    updated = 0
    failed = 0
    errors = []

    # Get products data
    product_ids = [item["product_id"] for item in catalog_items]
    products = await db.products.find({"id": {"$in": product_ids}}, {"_id": 0}).to_list(len(product_ids))
    products_map = {p["id"]: p for p in products}

    # Get existing products from Shopify by SKU
    existing_products = client.get_products(limit=250)
    existing_skus = {}
    for p in existing_products:
        for variant in p.get("variants", []):
            sku = variant.get("sku", "")
            if sku:
                existing_skus[sku] = p.get("id")

    # Get margin rules
    margin_rules = await db.catalog_margin_rules.find({"catalog_id": catalog_id}, {"_id": 0}).sort("priority", -1).to_list(100)

    for item in catalog_items:
        product = products_map.get(item["product_id"])
        if not product:
            failed += 1
            errors.append(f"Producto no encontrado: {item['product_id']}")
            continue

        try:
            base_price = item.get("custom_price") or product.get("price", 0)
            final_price = calculate_final_price(base_price, product, margin_rules)

            product_data = {
                "sku": product.get("sku", ""),
                "ean": product.get("ean", ""),
                "name": item.get("custom_name") or product.get("name", ""),
                "price": round(final_price, 2),
                "stock": product.get("stock", 0),
                "short_description": product.get("short_description", ""),
                "long_description": product.get("long_description") or product.get("description", ""),
                "brand": product.get("brand", ""),
                "weight": product.get("weight", 0),
                "image_url": product.get("image_url", ""),
                "gallery_images": product.get("gallery_images", []),
                "category": product.get("category", "")
            }

            # Check if product exists
            existing_id = existing_skus.get(product.get("sku", ""))

            if existing_id:
                result = client.update_product(int(existing_id), product_data)
                if result.get("status") == "success":
                    updated += 1
                else:
                    failed += 1
                    errors.append(f"{product.get('sku')}: {result.get('message')}")
            else:
                result = client.create_product(product_data)
                if result.get("status") == "success":
                    created += 1
                else:
                    failed += 1
                    errors.append(f"{product.get('sku')}: {result.get('message')}")
        except Exception as e:
            failed += 1
            errors.append(f"{product.get('sku', 'unknown')}: {str(e)}")

    # Update config
    now = datetime.now(UTC).isoformat()
    await db.woocommerce_configs.update_one(
        {"id": config["id"]},
        {"$set": {"last_sync": now, "products_synced": created + updated}}
    )

    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "type": "store_export",
        "message": f"Exportación a Shopify: {created} creados, {updated} actualizados, {failed} fallidos",
        "product_id": None,
        "product_name": None,
        "user_id": user["id"],
        "read": False,
        "created_at": now
    })

    return {
        "status": "success" if failed == 0 else "partial",
        "created": created,
        "updated": updated,
        "failed": failed,
        "errors": errors[:10]
    }


async def export_to_magento(config: dict, catalog_items: list, catalog_id: str, user: dict) -> dict:
    """Export products to Magento with full product data"""

    client = MagentoClient(
        store_url=config.get("store_url", ""),
        access_token=config.get("access_token", "")
    )

    created = 0
    updated = 0
    failed = 0
    errors = []

    # Get products data
    product_ids = [item["product_id"] for item in catalog_items]
    products = await db.products.find({"id": {"$in": product_ids}}, {"_id": 0}).to_list(len(product_ids))
    products_map = {p["id"]: p for p in products}

    # Get existing products from Magento by SKU
    existing_products = client.get_products(limit=500)
    existing_skus = {p.get("sku", ""): True for p in existing_products}

    # Get margin rules
    margin_rules = await db.catalog_margin_rules.find({"catalog_id": catalog_id}, {"_id": 0}).sort("priority", -1).to_list(100)

    for item in catalog_items:
        product = products_map.get(item["product_id"])
        if not product:
            failed += 1
            errors.append(f"Producto no encontrado: {item['product_id']}")
            continue

        try:
            base_price = item.get("custom_price") or product.get("price", 0)
            final_price = calculate_final_price(base_price, product, margin_rules)

            product_data = {
                "sku": product.get("sku", ""),
                "ean": product.get("ean", ""),
                "name": item.get("custom_name") or product.get("name", ""),
                "price": round(final_price, 2),
                "stock": product.get("stock", 0),
                "short_description": product.get("short_description", ""),
                "long_description": product.get("long_description") or product.get("description", ""),
                "brand": product.get("brand", ""),
                "weight": product.get("weight", 0),
                "image_url": product.get("image_url", ""),
                "gallery_images": product.get("gallery_images", []),
                "category": product.get("category", "")
            }

            sku = product.get("sku", "")

            if sku in existing_skus:
                result = client.update_product(sku, product_data)
                if result.get("status") == "success":
                    updated += 1
                else:
                    failed += 1
                    errors.append(f"{sku}: {result.get('message')}")
            else:
                result = client.create_product(product_data)
                if result.get("status") == "success":
                    created += 1
                else:
                    failed += 1
                    errors.append(f"{sku}: {result.get('message')}")
        except Exception as e:
            failed += 1
            errors.append(f"{product.get('sku', 'unknown')}: {str(e)}")

    # Update config
    now = datetime.now(UTC).isoformat()
    await db.woocommerce_configs.update_one(
        {"id": config["id"]},
        {"$set": {"last_sync": now, "products_synced": created + updated}}
    )

    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "type": "store_export",
        "message": f"Exportación a Magento: {created} creados, {updated} actualizados, {failed} fallidos",
        "product_id": None,
        "product_name": None,
        "user_id": user["id"],
        "read": False,
        "created_at": now
    })

    return {
        "status": "success" if failed == 0 else "partial",
        "created": created,
        "updated": updated,
        "failed": failed,
        "errors": errors[:10]
    }


async def export_to_wix(config: dict, catalog_items: list, catalog_id: str, user: dict) -> dict:
    """Export products to Wix with full product data"""

    client = WixClient(
        store_url=config.get("store_url", ""),
        api_key=config.get("api_key", ""),
        site_id=config.get("site_id", "")
    )

    created = 0
    updated = 0
    failed = 0
    errors = []

    # Get products data
    product_ids = [item["product_id"] for item in catalog_items]
    products = await db.products.find({"id": {"$in": product_ids}}, {"_id": 0}).to_list(len(product_ids))
    products_map = {p["id"]: p for p in products}

    # Get existing products from Wix by SKU
    existing_products = client.get_products(limit=500)
    existing_skus = {p.get("sku", ""): p.get("id") for p in existing_products if p.get("sku")}

    # Get margin rules
    margin_rules = await db.catalog_margin_rules.find({"catalog_id": catalog_id}, {"_id": 0}).sort("priority", -1).to_list(100)

    for item in catalog_items:
        product = products_map.get(item["product_id"])
        if not product:
            failed += 1
            errors.append(f"Producto no encontrado: {item['product_id']}")
            continue

        try:
            base_price = item.get("custom_price") or product.get("price", 0)
            final_price = calculate_final_price(base_price, product, margin_rules)

            product_data = {
                "sku": product.get("sku", ""),
                "ean": product.get("ean", ""),
                "name": item.get("custom_name") or product.get("name", ""),
                "price": round(final_price, 2),
                "stock": product.get("stock", 0),
                "short_description": product.get("short_description", ""),
                "long_description": product.get("long_description") or product.get("description", ""),
                "brand": product.get("brand", ""),
                "weight": product.get("weight", 0),
                "image_url": product.get("image_url", ""),
                "gallery_images": product.get("gallery_images", []),
                "category": product.get("category", "")
            }

            sku = product.get("sku", "")
            existing_id = existing_skus.get(sku)

            if existing_id:
                result = client.update_product(existing_id, product_data)
                if result.get("status") == "success":
                    updated += 1
                else:
                    failed += 1
                    errors.append(f"{sku}: {result.get('message')}")
            else:
                result = client.create_product(product_data)
                if result.get("status") == "success":
                    created += 1
                else:
                    failed += 1
                    errors.append(f"{sku}: {result.get('message')}")
        except Exception as e:
            failed += 1
            errors.append(f"{product.get('sku', 'unknown')}: {str(e)}")

    # Update config
    now = datetime.now(UTC).isoformat()
    await db.woocommerce_configs.update_one(
        {"id": config["id"]},
        {"$set": {"last_sync": now, "products_synced": created + updated}}
    )

    await db.notifications.insert_one({
        "id": str(uuid.uuid4()),
        "type": "store_export",
        "message": f"Exportación a Wix: {created} creados, {updated} actualizados, {failed} fallidos",
        "product_id": None,
        "product_name": None,
        "user_id": user["id"],
        "read": False,
        "created_at": now
    })

    return {
        "status": "success" if failed == 0 else "partial",
        "created": created,
        "updated": updated,
        "failed": failed,
        "errors": errors[:10]
    }


@router.post("/stores/configs/{config_id}/export-categories")
async def export_categories_to_store(config_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Export catalog categories to a store"""
    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de tienda no encontrada")

    catalog_id = request.get("catalog_id") or config.get("catalog_id")
    if not catalog_id:
        raise HTTPException(status_code=400, detail="No hay catálogo especificado")

    # Verify catalog exists
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    platform = config.get("platform", "woocommerce")

    if platform == "woocommerce":
        from services.sync import export_catalog_categories_to_woocommerce
        result = await export_catalog_categories_to_woocommerce(config, catalog_id, user["id"])

        # Store the category mapping for future product exports
        if result.get("category_mapping"):
            await db.woocommerce_configs.update_one(
                {"id": config_id},
                {"$set": {f"category_mapping_{catalog_id}": result["category_mapping"]}}
            )

        now = datetime.now(UTC).isoformat()
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "type": "categories_export",
            "message": f"Exportación de categorías a WooCommerce: {result.get('created', 0)} creadas, {result.get('total', 0)} total",
            "product_id": None,
            "product_name": None,
            "user_id": user["id"],
            "read": False,
            "created_at": now
        })

        return result

    elif platform == "prestashop":
        # PrestaShop category export
        client = PrestaShopClient(
            store_url=config.get("store_url", ""),
            api_key=config.get("api_key", "")
        )

        categories = await db.catalog_categories.find(
            {"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
        ).sort([("level", 1), ("position", 1)]).to_list(500)

        if not categories:
            return {"status": "warning", "created": 0, "message": "No hay categorías para exportar"}

        category_mapping = {}
        created = 0
        errors = []

        for cat in categories:
            try:
                parent_id = 2  # Default PrestaShop home category
                if cat.get("parent_id") and cat["parent_id"] in category_mapping:
                    parent_id = category_mapping[cat["parent_id"]]

                ps_id = await asyncio.to_thread(client.find_or_create_category, cat["name"], parent_id)
                if ps_id:
                    category_mapping[cat["id"]] = ps_id
                    created += 1
                else:
                    errors.append(f"Error creando: {cat['name']}")
            except Exception as e:
                errors.append(f"Error: {str(e)[:50]}")

        return {
            "status": "success" if not errors else "partial",
            "created": created,
            "total": len(categories),
            "category_mapping": category_mapping,
            "errors": errors[:10]
        }

    elif platform == "shopify":
        # Shopify uses collections instead of categories
        client = ShopifyClient(
            store_url=config.get("store_url", ""),
            access_token=config.get("access_token", ""),
            api_version=config.get("api_version", "2024-10")
        )

        categories = await db.catalog_categories.find(
            {"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
        ).sort([("level", 1), ("position", 1)]).to_list(500)

        if not categories:
            return {"status": "warning", "created": 0, "message": "No hay categorías para exportar"}

        # Shopify doesn't support hierarchical categories, so we flatten them
        collection_mapping = {}
        created = 0
        errors = []

        for cat in categories:
            try:
                # Build full path name for hierarchy indication
                full_name = cat["name"]
                if cat.get("parent_id"):
                    parent = next((c for c in categories if c["id"] == cat["parent_id"]), None)
                    if parent:
                        full_name = f"{parent['name']} > {cat['name']}"

                coll_id = await asyncio.to_thread(client.find_or_create_collection, full_name)
                if coll_id:
                    collection_mapping[cat["id"]] = coll_id
                    created += 1
                else:
                    errors.append(f"Error creando: {full_name}")
            except Exception as e:
                errors.append(f"Error: {str(e)[:50]}")

        return {
            "status": "success" if not errors else "partial",
            "created": created,
            "total": len(categories),
            "collection_mapping": collection_mapping,
            "errors": errors[:10],
            "note": "Shopify usa 'Colecciones' en lugar de categorías jerárquicas"
        }

    else:
        return {
            "status": "info",
            "message": f"Exportación de categorías para {SUPPORTED_PLATFORMS.get(platform, {}).get('name', platform)} no está implementada todavía"
        }


# ==================== CREATE CATALOG FROM STORE PRODUCTS ====================

async def _run_create_catalog_from_store(
    user_id: str,
    store_config_id: str,
    catalog_name: str,
    catalog_id: str,
    match_by: list,
    skip_unmatched: bool,
):
    """Background wrapper that runs the catalog creation task."""
    from services.sync import create_catalog_from_store_products
    await create_catalog_from_store_products(
        user_id=user_id,
        store_config_id=store_config_id,
        catalog_name=catalog_name,
        catalog_id=catalog_id,
        match_by=match_by,
        skip_unmatched=skip_unmatched,
    )


@router.post("/stores/{store_config_id}/create-catalog")
async def create_catalog_from_store(
    store_config_id: str,
    request: dict,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """
    Create a catalog with products from a store by matching them with supplier products.
    Runs as a background task — progress is sent via WebSocket.

    Request body:
    {
        "catalog_name": "Mi Catálogo desde Tienda" (optional),
        "catalog_id": "existing-catalog-id" (optional, use instead of catalog_name),
        "match_by": ["sku", "ean", "name"] (optional, default: all),
        "skip_unmatched": true (optional, default: true)
    }
    """
    # Validate store config exists
    store_config = await db.woocommerce_configs.find_one(
        {"id": store_config_id, "user_id": user["id"]}
    )
    if not store_config:
        raise HTTPException(
            status_code=404,
            detail="Configuración de tienda no encontrada"
        )

    # Validate catalog limits when creating a new catalog
    if not request.get("catalog_id"):
        can_create = await check_user_limit(user, "catalogs")
        if not can_create:
            raise HTTPException(
                status_code=403,
                detail=f"Has alcanzado el límite de catálogos. Máximo: {user.get('max_catalogs', 5)}"
            )

    skip_unmatched = request.get("skip_unmatched", True)

    # Only require suppliers when skipping unmatched (matching mode)
    if skip_unmatched:
        supplier_count = await db.suppliers.count_documents({"user_id": user["id"]})
        product_count = await db.products.count_documents({"user_id": user["id"]})
        if supplier_count == 0 and product_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Debes tener al menos un proveedor con productos para buscar coincidencias"
            )

    # Schedule as background task — returns immediately
    background_tasks.add_task(
        _run_create_catalog_from_store,
        user_id=user["id"],
        store_config_id=store_config_id,
        catalog_name=request.get("catalog_name"),
        catalog_id=request.get("catalog_id"),
        match_by=request.get("match_by", ["sku", "ean", "name"]),
        skip_unmatched=skip_unmatched,
    )

    return {
        "status": "started",
        "message": f"Creación de catálogo desde '{store_config.get('name', 'tienda')}' iniciada en segundo plano. Recibirás notificaciones de progreso."
    }
