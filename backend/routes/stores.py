from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging
import asyncio

from services.database import db
from services.auth import get_current_user, check_user_limit
from services.sync import (
    get_woocommerce_client, mask_key, calculate_final_price,
    sync_woocommerce_store_price_stock
)
from services.platforms import (
    get_platform_client, PrestaShopClient, ShopifyClient, 
    MagentoClient, WixClient
)

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
    now = datetime.now(timezone.utc).isoformat()
    
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
            next_sync = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        
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
        next_sync = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    
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
        next_sync = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    
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
            
    except Exception as e:
        await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": False}})
        return {"status": "error", "message": f"Error de conexión: {str(e)}"}


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
            now = datetime.now(timezone.utc).isoformat()
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
        return {"status": "error", "message": f"Error en la sincronización: {str(e)}"}


@router.post("/stores/export")
async def export_to_store(request: dict, user: dict = Depends(get_current_user)):
    """Export products to a store"""
    config_id = request.get("config_id")
    catalog_id = request.get("catalog_id")
    update_existing = request.get("update_existing", True)
    
    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de tienda no encontrada")
    
    platform = config.get("platform", "woocommerce")
    
    # Get catalog items
    catalog_items = []
    if catalog_id:
        catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
        if not catalog:
            raise HTTPException(status_code=404, detail="Catálogo no encontrado")
        catalog_items = await db.catalog_items.find({"catalog_id": catalog_id, "active": True}, {"_id": 0}).to_list(1000)
    
    if not catalog_items:
        return {"status": "warning", "created": 0, "updated": 0, "failed": 0, "errors": ["No hay productos activos para exportar"]}
    
    if platform == "woocommerce":
        # Use existing WooCommerce export logic
        from routes.woocommerce import export_to_woocommerce
        from models.schemas import WooCommerceExportRequest
        
        wc_request = WooCommerceExportRequest(
            config_id=config_id,
            catalog_id=catalog_id,
            update_existing=update_existing
        )
        result = await export_to_woocommerce(wc_request, user)
        return {
            "status": result.status,
            "created": result.created,
            "updated": result.updated,
            "failed": result.failed,
            "errors": result.errors
        }
    else:
        # Simulated export for other platforms
        now = datetime.now(timezone.utc).isoformat()
        product_count = len(catalog_items)
        
        await db.woocommerce_configs.update_one(
            {"id": config_id}, 
            {"$set": {"last_sync": now, "products_synced": product_count}}
        )
        
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "type": "store_export",
            "message": f"Exportación a {SUPPORTED_PLATFORMS.get(platform, {}).get('name', platform)}: {product_count} productos procesados (modo demo)",
            "product_id": None,
            "product_name": None,
            "user_id": user["id"],
            "read": False,
            "created_at": now
        })
        
        return {
            "status": "success",
            "created": product_count,
            "updated": 0,
            "failed": 0,
            "errors": [],
            "message": f"Exportación simulada para {SUPPORTED_PLATFORMS.get(platform, {}).get('name', platform)}. La integración completa está en desarrollo."
        }
