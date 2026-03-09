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
from models.schemas import (
    WooCommerceConfig, WooCommerceConfigUpdate, WooCommerceConfigResponse,
    WooCommerceExportRequest, WooCommerceExportResult
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/woocommerce/configs", response_model=WooCommerceConfigResponse)
async def create_woocommerce_config(config: WooCommerceConfig, user: dict = Depends(get_current_user)):
    # Check user limit
    can_create = await check_user_limit(user, "woocommerce_stores")
    if not can_create:
        raise HTTPException(
            status_code=403, 
            detail=f"Has alcanzado el límite de tiendas WooCommerce. Máximo: {user.get('max_woocommerce_stores', 2)}"
        )
    
    config_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    catalog_name = None
    if config.catalog_id:
        catalog = await db.catalogs.find_one({"id": config.catalog_id, "user_id": user["id"]})
        if catalog:
            catalog_name = catalog.get("name")
    config_doc = {
        "id": config_id, "user_id": user["id"],
        "name": config.name or "Mi Tienda WooCommerce",
        "store_url": config.store_url.rstrip('/'),
        "consumer_key": config.consumer_key, "consumer_secret": config.consumer_secret,
        "catalog_id": config.catalog_id, "auto_sync_enabled": config.auto_sync_enabled,
        "is_connected": False, "last_sync": None, "products_synced": 0, "created_at": now
    }
    await db.woocommerce_configs.insert_one(config_doc)
    next_sync = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat() if config.auto_sync_enabled else None
    return WooCommerceConfigResponse(
        id=config_id, name=config_doc["name"], store_url=config_doc["store_url"],
        consumer_key_masked=mask_key(config.consumer_key), is_connected=False,
        last_sync=None, products_synced=0, created_at=now,
        catalog_id=config.catalog_id, catalog_name=catalog_name,
        auto_sync_enabled=config.auto_sync_enabled, next_sync=next_sync
    )


@router.get("/woocommerce/configs", response_model=List[WooCommerceConfigResponse])
async def get_woocommerce_configs(user: dict = Depends(get_current_user)):
    configs = await db.woocommerce_configs.find({"user_id": user["id"]}, {"_id": 0, "consumer_secret": 0}).to_list(100)
    catalog_ids = [c.get("catalog_id") for c in configs if c.get("catalog_id")]
    catalogs = {}
    if catalog_ids:
        catalog_docs = await db.catalogs.find({"id": {"$in": catalog_ids}}).to_list(100)
        catalogs = {c["id"]: c.get("name") for c in catalog_docs}
    result = []
    for c in configs:
        next_sync = None
        if c.get("auto_sync_enabled") and c.get("last_sync"):
            last_sync_dt = datetime.fromisoformat(c["last_sync"].replace('Z', '+00:00'))
            next_sync = (last_sync_dt + timedelta(hours=12)).isoformat()
        elif c.get("auto_sync_enabled"):
            next_sync = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        result.append(WooCommerceConfigResponse(
            id=c["id"], name=c["name"], store_url=c["store_url"],
            consumer_key_masked=mask_key(c["consumer_key"]),
            is_connected=c.get("is_connected", False),
            last_sync=c.get("last_sync"), products_synced=c.get("products_synced", 0),
            created_at=c["created_at"], catalog_id=c.get("catalog_id"),
            catalog_name=catalogs.get(c.get("catalog_id")),
            auto_sync_enabled=c.get("auto_sync_enabled", False), next_sync=next_sync
        ))
    return result


@router.get("/woocommerce/configs/{config_id}", response_model=WooCommerceConfigResponse)
async def get_woocommerce_config(config_id: str, user: dict = Depends(get_current_user)):
    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]}, {"_id": 0, "consumer_secret": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
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
    return WooCommerceConfigResponse(
        id=config["id"], name=config["name"], store_url=config["store_url"],
        consumer_key_masked=mask_key(config["consumer_key"]),
        is_connected=config.get("is_connected", False),
        last_sync=config.get("last_sync"), products_synced=config.get("products_synced", 0),
        created_at=config["created_at"], catalog_id=config.get("catalog_id"),
        catalog_name=catalog_name, auto_sync_enabled=config.get("auto_sync_enabled", False),
        next_sync=next_sync
    )


@router.put("/woocommerce/configs/{config_id}", response_model=WooCommerceConfigResponse)
async def update_woocommerce_config(config_id: str, update: WooCommerceConfigUpdate, user: dict = Depends(get_current_user)):
    existing = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if "store_url" in update_data:
        update_data["store_url"] = update_data["store_url"].rstrip('/')
    if update_data:
        await db.woocommerce_configs.update_one({"id": config_id}, {"$set": update_data})
    updated = await db.woocommerce_configs.find_one({"id": config_id}, {"_id": 0, "consumer_secret": 0})
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
    return WooCommerceConfigResponse(
        id=updated["id"], name=updated["name"], store_url=updated["store_url"],
        consumer_key_masked=mask_key(updated["consumer_key"]),
        is_connected=updated.get("is_connected", False),
        last_sync=updated.get("last_sync"), products_synced=updated.get("products_synced", 0),
        created_at=updated["created_at"], catalog_id=updated.get("catalog_id"),
        catalog_name=catalog_name, auto_sync_enabled=updated.get("auto_sync_enabled", False),
        next_sync=next_sync
    )


@router.delete("/woocommerce/configs/{config_id}")
async def delete_woocommerce_config(config_id: str, user: dict = Depends(get_current_user)):
    result = await db.woocommerce_configs.delete_one({"id": config_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return {"message": "Configuración eliminada"}


@router.post("/woocommerce/configs/{config_id}/test")
async def test_woocommerce_connection(config_id: str, user: dict = Depends(get_current_user)):
    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    try:
        wcapi = get_woocommerce_client(config)
        response = await asyncio.to_thread(wcapi.get, "")
        if response.status_code == 200:
            await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": True}})
            store_info = response.json()
            return {"status": "success", "message": "Conexión exitosa", "store_name": store_info.get("name", "Tienda WooCommerce")}
        else:
            await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": False}})
            return {"status": "error", "message": f"Error de conexión: {response.status_code}"}
    except Exception as e:
        await db.woocommerce_configs.update_one({"id": config_id}, {"$set": {"is_connected": False}})
        return {"status": "error", "message": f"Error de conexión: {str(e)}"}


@router.post("/woocommerce/configs/{config_id}/sync")
async def sync_woocommerce_price_stock(config_id: str, user: dict = Depends(get_current_user)):
    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    if not config.get("catalog_id"):
        raise HTTPException(status_code=400, detail="No hay catálogo asociado a esta tienda. Configura un catálogo primero.")
    try:
        await sync_woocommerce_store_price_stock(config)
        updated = await db.woocommerce_configs.find_one({"id": config_id}, {"_id": 0})
        return {
            "status": "success",
            "message": f"Sincronización completada. {updated.get('products_synced', 0)} productos actualizados.",
            "products_synced": updated.get("products_synced", 0),
            "last_sync": updated.get("last_sync")
        }
    except Exception as e:
        logger.error(f"Error in manual WooCommerce sync: {e}")
        return {"status": "error", "message": f"Error en la sincronización: {str(e)}"}


@router.post("/woocommerce/export", response_model=WooCommerceExportResult)
async def export_to_woocommerce(request: WooCommerceExportRequest, user: dict = Depends(get_current_user)):
    config = await db.woocommerce_configs.find_one({"id": request.config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de WooCommerce no encontrada")
    catalog_items = []
    margin_rules = []
    catalog_id = request.catalog_id
    if request.catalog_id:
        catalog = await db.catalogs.find_one({"id": request.catalog_id, "user_id": user["id"]})
        if not catalog:
            raise HTTPException(status_code=404, detail="Catálogo no encontrado")
        catalog_items = await db.catalog_items.find({"catalog_id": request.catalog_id, "active": True}, {"_id": 0}).to_list(1000)
        margin_rules = await db.catalog_margin_rules.find({"catalog_id": request.catalog_id}, {"_id": 0}).sort("priority", -1).to_list(100)
    else:
        catalog = await db.catalogs.find_one({"user_id": user["id"], "is_default": True})
        if catalog:
            catalog_id = catalog["id"]
            catalog_items = await db.catalog_items.find({"catalog_id": catalog["id"], "active": True}, {"_id": 0}).to_list(1000)
            margin_rules = await db.catalog_margin_rules.find({"catalog_id": catalog["id"]}, {"_id": 0}).sort("priority", -1).to_list(100)
        else:
            catalog_items = await db.catalog.find({"user_id": user["id"], "active": True}, {"_id": 0}).to_list(1000)
            margin_rules = await db.margin_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("priority", -1).to_list(100)
    if not catalog_items:
        return WooCommerceExportResult(status="warning", errors=["No hay productos activos para exportar"])
    product_ids = [item["product_id"] for item in catalog_items]
    products = await db.products.find({"id": {"$in": product_ids}}, {"_id": 0}).to_list(1000)
    products_map = {p["id"]: p for p in products}
    wcapi = get_woocommerce_client(config)
    created = 0
    updated = 0
    failed = 0
    errors = []
    existing_eans = {}
    existing_skus = {}
    
    # ==================== STEP 1: CREATE/GET CATEGORIES ====================
    # Build category mapping: category_name -> wc_category_id
    wc_category_map = {}
    try:
        # Get all unique categories from products
        unique_categories = set()
        for item in catalog_items:
            product = products_map.get(item["product_id"])
            if product and product.get("category"):
                # Handle hierarchical categories (e.g., "Electronics > Phones > Smartphones")
                cat_parts = [c.strip() for c in product["category"].split(">")]
                for i in range(len(cat_parts)):
                    # Build full path for each level
                    full_path = " > ".join(cat_parts[:i+1])
                    unique_categories.add(full_path)
        
        if unique_categories:
            logger.info(f"Found {len(unique_categories)} unique categories to sync")
            
            # Get existing WooCommerce categories
            existing_wc_cats = []
            page = 1
            while True:
                response = await asyncio.to_thread(wcapi.get, "products/categories", params={"per_page": 100, "page": page})
                if response.status_code == 200:
                    batch = response.json()
                    if not batch:
                        break
                    existing_wc_cats.extend(batch)
                    page += 1
                    if len(batch) < 100:
                        break
                else:
                    break
            
            # Build map of existing categories by name and parent
            existing_cats_by_name = {}
            for cat in existing_wc_cats:
                key = f"{cat.get('name', '').lower()}:{cat.get('parent', 0)}"
                existing_cats_by_name[key] = cat["id"]
                # Also store by just name for simple lookup
                existing_cats_by_name[cat.get("name", "").lower()] = cat["id"]
            
            # Create categories that don't exist
            for full_cat_path in sorted(unique_categories):
                cat_parts = [c.strip() for c in full_cat_path.split(">")]
                parent_id = 0
                
                for i, cat_name in enumerate(cat_parts):
                    current_path = " > ".join(cat_parts[:i+1])
                    
                    # Check if already in our map
                    if current_path in wc_category_map:
                        parent_id = wc_category_map[current_path]
                        continue
                    
                    # Check if exists in WooCommerce
                    lookup_key = f"{cat_name.lower()}:{parent_id}"
                    if lookup_key in existing_cats_by_name:
                        wc_category_map[current_path] = existing_cats_by_name[lookup_key]
                        parent_id = existing_cats_by_name[lookup_key]
                        continue
                    
                    # Create new category
                    cat_payload = {
                        "name": cat_name,
                        "parent": parent_id
                    }
                    try:
                        response = await asyncio.to_thread(wcapi.post, "products/categories", cat_payload)
                        if response.status_code in [200, 201]:
                            new_cat = response.json()
                            wc_category_map[current_path] = new_cat["id"]
                            parent_id = new_cat["id"]
                            logger.info(f"Created WooCommerce category: {cat_name} (ID: {new_cat['id']})")
                        else:
                            logger.warning(f"Failed to create category {cat_name}: {response.text[:100]}")
                    except Exception as e:
                        logger.error(f"Error creating category {cat_name}: {e}")
            
            logger.info(f"Category mapping complete: {len(wc_category_map)} categories mapped")
    except Exception as e:
        logger.error(f"Error syncing categories: {e}")
    
    # ==================== STEP 2: GET EXISTING PRODUCTS ====================
    if request.update_existing:
        try:
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
                                    existing_eans[ean_value] = p["id"]
                                    break
                        if p.get("sku"):
                            existing_skus[p["sku"]] = p["id"]
                    page += 1
                    if len(products_batch) < 100:
                        break
                else:
                    break
        except Exception as e:
            logger.warning(f"Could not fetch existing products: {e}")
    
    # ==================== STEP 3: EXPORT PRODUCTS IN BATCHES ====================
    # WooCommerce batch API allows up to 100 items per request
    BATCH_SIZE = 50  # Use 50 for better reliability
    
    products_to_create = []
    products_to_update = []
    
    for catalog_item in catalog_items:
        product = products_map.get(catalog_item["product_id"])
        if not product:
            failed += 1
            errors.append(f"Producto no encontrado: {catalog_item['product_id']}")
            continue
        base_price = catalog_item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        try:
            ean = product.get("ean", "") or ""
            sku = product.get("sku", "")
            
            # Use long_description if available, fallback to description
            description = product.get("long_description") or product.get("description", "")
            short_desc = product.get("short_description", "")
            
            wc_product = {
                "name": catalog_item.get("custom_name") or product.get("name", "Producto sin nombre"),
                "type": "simple", "regular_price": str(round(final_price, 2)),
                "description": description,
                "short_description": short_desc,
                "sku": sku, "manage_stock": True,
                "stock_quantity": product.get("stock", 0),
                "categories": [], "images": [], "meta_data": []
            }
            
            # Add EAN meta data
            if ean:
                wc_product["meta_data"].extend([
                    {"key": "_global_unique_id", "value": ean},
                    {"key": "_gtin", "value": ean},
                    {"key": "gtin", "value": ean},
                    {"key": "_ean", "value": ean}
                ])
            
            # Add brand meta data
            if product.get("brand"):
                wc_product["meta_data"].append({"key": "_brand", "value": product["brand"]})
            
            # Add supplier name as custom field
            if product.get("supplier_name"):
                wc_product["meta_data"].append({"key": "_supplier_name", "value": product["supplier_name"]})
                wc_product["meta_data"].append({"key": "supplier_name", "value": product["supplier_name"]})
            
            # Assign categories by ID (created in step 1)
            if product.get("category"):
                cat_path = product["category"].strip()
                if cat_path in wc_category_map:
                    wc_product["categories"] = [{"id": wc_category_map[cat_path]}]
                else:
                    # Try to find the deepest matching category
                    cat_parts = [c.strip() for c in cat_path.split(">")]
                    for i in range(len(cat_parts), 0, -1):
                        partial_path = " > ".join(cat_parts[:i])
                        if partial_path in wc_category_map:
                            wc_product["categories"] = [{"id": wc_category_map[partial_path]}]
                            break
            
            # Add main image first
            if product.get("image_url"):
                wc_product["images"].append({"src": product["image_url"]})
            
            # Add gallery images
            gallery_images = product.get("gallery_images") or []
            for gallery_img in gallery_images:
                if gallery_img:
                    wc_product["images"].append({"src": gallery_img})
            
            # Legacy support for old image fields
            for img_field in ["image_url2", "image_url3"]:
                if product.get(img_field):
                    wc_product["images"].append({"src": product[img_field]})
            
            if product.get("weight"):
                wc_product["weight"] = str(product["weight"])
            
            # Determine if create or update
            existing_wc_id = existing_eans.get(ean) if ean else None
            if not existing_wc_id and sku:
                existing_wc_id = existing_skus.get(sku)
            
            if existing_wc_id and request.update_existing:
                wc_product["id"] = existing_wc_id
                products_to_update.append(wc_product)
            else:
                products_to_create.append({"product": wc_product, "ean": ean})
                
        except Exception as e:
            failed += 1
            errors.append(f"Error procesando {product.get('sku', '')}: {str(e)[:100]}")
    
    # Process creates in batches
    for i in range(0, len(products_to_create), BATCH_SIZE):
        batch = products_to_create[i:i + BATCH_SIZE]
        batch_data = {"create": [item["product"] for item in batch]}
        try:
            response = await asyncio.to_thread(wcapi.post, "products/batch", batch_data)
            if response.status_code in [200, 201]:
                result = response.json()
                created += len(result.get("create", []))
                # Update EAN mapping for created products
                for j, created_product in enumerate(result.get("create", [])):
                    if j < len(batch) and batch[j]["ean"]:
                        existing_eans[batch[j]["ean"]] = created_product.get("id")
            else:
                failed += len(batch)
                errors.append(f"Error en batch create: {response.text[:100]}")
        except Exception as e:
            failed += len(batch)
            errors.append(f"Error en batch create: {str(e)[:100]}")
        
        # Small delay between batches to avoid rate limiting
        await asyncio.sleep(0.5)
    
    # Process updates in batches
    for i in range(0, len(products_to_update), BATCH_SIZE):
        batch = products_to_update[i:i + BATCH_SIZE]
        batch_data = {"update": batch}
        try:
            response = await asyncio.to_thread(wcapi.post, "products/batch", batch_data)
            if response.status_code in [200, 201]:
                result = response.json()
                updated += len(result.get("update", []))
            else:
                failed += len(batch)
                errors.append(f"Error en batch update: {response.text[:100]}")
        except Exception as e:
            failed += len(batch)
            errors.append(f"Error en batch update: {str(e)[:100]}")
        
        # Small delay between batches
        await asyncio.sleep(0.5)
    
    now = datetime.now(timezone.utc).isoformat()
    await db.woocommerce_configs.update_one({"id": request.config_id}, {"$set": {"last_sync": now, "products_synced": created + updated}})
    
    # Store the category mapping for future use
    if wc_category_map and catalog_id:
        await db.woocommerce_configs.update_one(
            {"id": request.config_id},
            {"$set": {f"category_mapping_{catalog_id}": wc_category_map}}
        )
    
    await db.notifications.insert_one({
        "id": str(uuid.uuid4()), "type": "woocommerce_export",
        "message": f"Exportación WooCommerce: {created} creados, {updated} actualizados, {failed} errores, {len(wc_category_map)} categorías",
        "product_id": None, "product_name": None,
        "user_id": user["id"], "read": False, "created_at": now
    })
    return WooCommerceExportResult(
        status="success" if failed == 0 else "partial" if (created + updated) > 0 else "error",
        created=created, updated=updated, failed=failed, errors=errors[:10]
    )


@router.get("/woocommerce/configs/{config_id}/products")
async def get_woocommerce_products(config_id: str, page: int = 1, per_page: int = 20, user: dict = Depends(get_current_user)):
    config = await db.woocommerce_configs.find_one({"id": config_id, "user_id": user["id"]})
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    try:
        wcapi = get_woocommerce_client(config)
        response = await asyncio.to_thread(wcapi.get, "products", params={"page": page, "per_page": per_page})
        if response.status_code == 200:
            products = response.json()
            total = response.headers.get('X-WP-Total', 0)
            return {"products": products, "total": int(total), "page": page, "per_page": per_page}
        else:
            return {"status": "error", "message": f"Error: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
