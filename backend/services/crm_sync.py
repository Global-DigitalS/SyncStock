"""
CRM sync functions for all supported platforms.
Handles product, supplier, and order synchronization with Dolibarr, Odoo, and generic CRMs.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from services.database import db
from services.sync import calculate_final_price
from services.crm_clients import (
    DolibarrClient, OdooClient,
    create_crm_client, FULL_SYNC_PLATFORMS, BASIC_SYNC_PLATFORMS,
)

logger = logging.getLogger(__name__)

async def run_sync_in_background(
    sync_job_id: str,
    user_id: str,
    connection_id: str,
    platform: str,
    config: dict,
    sync_settings: dict,
    sync_type: str,
    catalog_id: str = None
):
    """Background task for CRM sync with progress updates"""
    results = {
        "products": None,
        "suppliers": None,
        "orders": None
    }
    
    try:
        client = create_crm_client(platform, config)
        if not client:
            await db.sync_jobs.update_one(
                {"id": sync_job_id},
                {"$set": {
                    "status": "error",
                    "current_step": f"Plataforma no soportada: {platform}",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return

        if platform == "dolibarr":
            # Sync products (stock, price, description, images)
            if sync_type in ["all", "products"]:
                results["products"] = await sync_products_to_dolibarr(client, user_id, sync_settings, catalog_id, sync_job_id)

            # Sync suppliers
            if sync_type in ["all", "suppliers"]:
                await db.sync_jobs.update_one(
                    {"id": sync_job_id},
                    {"$set": {"current_step": "Sincronizando proveedores..."}}
                )
                results["suppliers"] = await sync_suppliers_to_dolibarr(client, user_id)

            # Import orders from stores to CRM
            if sync_type in ["all", "orders"]:
                await db.sync_jobs.update_one(
                    {"id": sync_job_id},
                    {"$set": {"current_step": "Importando pedidos..."}}
                )
                results["orders"] = await sync_orders_to_dolibarr(client, user_id)

        elif platform == "odoo":
            # Sync products (stock, price, description, images)
            if sync_type in ["all", "products"]:
                results["products"] = await sync_products_to_odoo(client, user_id, sync_settings, catalog_id, sync_job_id)

            # Sync suppliers
            if sync_type in ["all", "suppliers"]:
                await db.sync_jobs.update_one(
                    {"id": sync_job_id},
                    {"$set": {"current_step": "Sincronizando proveedores..."}}
                )
                results["suppliers"] = await sync_suppliers_to_odoo(client, user_id)

            # Import orders from stores to CRM
            if sync_type in ["all", "orders"]:
                await db.sync_jobs.update_one(
                    {"id": sync_job_id},
                    {"$set": {"current_step": "Importando pedidos..."}}
                )
                results["orders"] = await sync_orders_to_odoo(client, user_id)

        elif platform in BASIC_SYNC_PLATFORMS:
            # Generic sync for new CRM platforms (HubSpot, Salesforce, Zoho, Pipedrive, Monday, Freshsales)
            if sync_type in ["all", "products"]:
                results["products"] = await sync_products_generic(client, platform, user_id, sync_settings, catalog_id, sync_job_id)

        # Update last sync time
        await db.crm_connections.update_one(
            {"id": connection_id},
            {"$set": {"last_sync": datetime.now(timezone.utc).isoformat()}}
        )

        # Build summary message
        messages = []
        for key, result in results.items():
            if result:
                messages.append(f"{key}: {result.get('message', 'OK')}")

        # Mark job as completed
        await db.sync_jobs.update_one(
            {"id": sync_job_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "current_step": " | ".join(messages) if messages else "Sincronización completada",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "results": results
            }}
        )

        client.close()

    except Exception as e:
        logger.error(f"Sync error: {e}")
        # Mark job as failed
        await db.sync_jobs.update_one(
            {"id": sync_job_id},
            {"$set": {
                "status": "error",
                "current_step": f"Error: {str(e)[:100]}",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )


async def sync_products_to_dolibarr(client: DolibarrClient, user_id: str, sync_settings: dict = None, catalog_id: str = None, sync_job_id: str = None) -> Dict:
    """Sync products from our catalog to Dolibarr with full data including purchase price, stock and images"""
    if sync_settings is None:
        sync_settings = {"products": True, "stock": True, "prices": True, "descriptions": True, "images": True}
    
    # Build query filter
    query = {"user_id": user_id, "is_selected": True}
    catalog_items_map = {}  # product_id -> catalog_item data
    margin_rules = []  # Margin rules for price calculation
    
    # If catalog_id is provided, get only products from that catalog
    if catalog_id:
        catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user_id})
        if not catalog:
            return {"status": "error", "message": "Catálogo no encontrado", "created": 0, "updated": 0}
        
        # Get catalog_items with custom prices
        catalog_items = await db.catalog_items.find(
            {"catalog_id": catalog_id},
            {"_id": 0}
        ).to_list(10000)
        
        if not catalog_items:
            return {"status": "warning", "message": "El catálogo no tiene productos", "created": 0, "updated": 0}
        
        product_ids = [item.get("product_id") for item in catalog_items if item.get("product_id")]
        if not product_ids:
            return {"status": "warning", "message": "El catálogo no tiene productos válidos", "created": 0, "updated": 0}

        # Remove duplicates - a catalog can have multiple items pointing to same product
        # We want to sync each unique product only ONCE
        product_ids = list(set(product_ids))
        
        # Get margin rules for this catalog (sorted by priority descending)
        margin_rules = await db.catalog_margin_rules.find(
            {"catalog_id": catalog_id},
            {"_id": 0}
        ).sort("priority", -1).to_list(100)
        
        logger.info(f"Found {len(margin_rules)} margin rules for catalog {catalog_id}")
        
        # Change query to filter by product IDs instead of is_selected
        query = {"user_id": user_id, "id": {"$in": product_ids}}
    
    # Get products based on query
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    
    if not products:
        return {"status": "warning", "message": "No hay productos para sincronizar", "created": 0, "updated": 0}
    
    # Update sync job with total items
    total_products = len(products)
    if sync_job_id:
        await db.sync_jobs.update_one(
            {"id": sync_job_id},
            {"$set": {
                "total_items": total_products,
                "current_step": f"Sincronizando {total_products} productos..."
            }}
        )
    
    # Get all suppliers for this user to map supplier names
    suppliers = await db.suppliers.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    suppliers_map = {s["id"]: s for s in suppliers}
    
    created = 0
    updated = 0
    errors = 0
    images_synced = 0
    stock_synced = 0
    processed = 0
    
    for product in products:
        try:
            processed += 1
            sku = product.get("sku", "")
            
            # Update progress every 5 products or on first/last
            if sync_job_id and (processed % 5 == 0 or processed == 1 or processed == total_products):
                progress = int((processed / total_products) * 90)  # Reserve 10% for final steps
                await db.sync_jobs.update_one(
                    {"id": sync_job_id},
                    {"$set": {
                        "progress": progress,
                        "processed_items": processed,
                        "created": created,
                        "updated": updated,
                        "errors": errors,
                        "current_step": f"Procesando {processed}/{total_products}: {product.get('name', sku)[:30]}..."
                    }}
                )
            
            if not sku:
                errors += 1
                continue

            # Check if product exists in Dolibarr by SKU
            # Try up to 2 times in case of temporary API issues
            existing = None
            for attempt in range(2):
                try:
                    existing = client.get_product_by_ref(sku)
                    if existing is not None:
                        # Found it, break out of retry loop
                        logger.debug(f"Product {sku} found in Dolibarr on attempt {attempt + 1}")
                        break
                    else:
                        # Not found (404), no need to retry
                        logger.debug(f"Product {sku} not found in Dolibarr")
                        break
                except Exception as e:
                    if attempt < 1:
                        logger.warning(f"Attempt {attempt + 1} to check if product {sku} exists failed: {e}. Retrying...")
                        continue
                    else:
                        logger.error(f"Failed to check if product {sku} exists after 2 attempts: {e}")
                        errors += 1
                        break
            
            product_data = {
                "sku": sku,
                "name": product.get("name", ""),
            }
            
            # Add prices - differentiate between purchase price and sale price
            if sync_settings.get("prices", True):
                # Purchase/cost price = price from supplier
                purchase_price = float(product.get("price", 0) or 0)
                product_data["cost_price"] = purchase_price
                
                # Get catalog item if syncing from a catalog (may have custom price)
                catalog_item = catalog_items_map.get(product.get("id"))
                
                # Sale price calculation:
                # 1. If custom_price exists in catalog_item, use it
                # 2. Otherwise, calculate using margin rules from catalog
                # 3. Fallback to product's pvp/final_price
                # 4. Last resort: use purchase price
                sale_price = None
                
                if catalog_item and catalog_item.get("custom_price"):
                    # Custom price set manually in catalog
                    sale_price = float(catalog_item.get("custom_price"))
                    logger.debug(f"Using custom_price for {sku}: {sale_price}")
                elif margin_rules and purchase_price > 0:
                    # Calculate price using catalog margin rules
                    sale_price = calculate_final_price(purchase_price, product, margin_rules)
                    logger.debug(f"Calculated sale_price for {sku}: {purchase_price} -> {sale_price} (margin rules applied)")
                
                # Fallback to product's own final_price or pvp
                if not sale_price:
                    sale_price = product.get("final_price") or product.get("pvp") or product.get("custom_price")
                
                # Last fallback: use purchase price
                if not sale_price and purchase_price:
                    sale_price = purchase_price
                
                product_data["price"] = round(float(sale_price or 0), 2)
            
            # Sync stock
            if sync_settings.get("stock", True):
                stock_value = product.get("stock", 0)
                # Validate stock value - prevent absurdly large numbers (likely corruption)
                # Stock shouldn't exceed 1 million units per product
                if isinstance(stock_value, (int, float)) and stock_value > 1000000:
                    logger.warning(f"Stock value suspiciously large for {sku}: {stock_value}. Capping at 1000000.")
                    stock_value = 1000000
                product_data["stock"] = max(0, int(stock_value) if isinstance(stock_value, (int, float)) else 0)
            
            # Sync descriptions
            if sync_settings.get("descriptions", True):
                product_data["description"] = product.get("description", "")
                product_data["short_description"] = product.get("short_description", "")
                product_data["long_description"] = product.get("long_description", "")
                product_data["brand"] = product.get("brand", "")
                
                # Add supplier name to notes
                supplier = suppliers_map.get(product.get("supplier_id"))
                if supplier:
                    product_data["supplier_name"] = supplier.get("name", "")
            
            product_data["ean"] = product.get("ean", "")
            product_data["weight"] = product.get("weight", 0)
            
            # Handle image URL
            image_url = product.get("image_url", "") if sync_settings.get("images", True) else ""
            if image_url:
                product_data["image_url"] = image_url
            
            if existing:
                product_id = int(existing.get("id"))
                result = client.update_product(product_id, product_data)
                if result["status"] == "success":
                    updated += 1
                    
                    # Sync stock using stock movements for accurate tracking
                    if sync_settings.get("stock", True):
                        # Use the validated stock value from product_data, NOT raw product data
                        validated_stock = product_data.get("stock", 0)
                        stock_result = client.update_stock(product_id, validated_stock)
                        if stock_result.get("status") == "success":
                            stock_synced += 1
                        elif stock_result.get("status") == "warning":
                            logger.warning(f"Stock warning for {sku}: {stock_result.get('message')}")
                    
                    # Upload image separately for better handling
                    if image_url and sync_settings.get("images", True):
                        img_result = client.upload_product_image(product_id, image_url)
                        if img_result.get("status") == "success":
                            images_synced += 1
                else:
                    errors += 1
            else:
                result = client.create_product(product_data)
                if result["status"] == "success":
                    created += 1
                    # Image is uploaded in create_product if image_url is provided
                    if image_url:
                        images_synced += 1
                else:
                    errors += 1
        except Exception as e:
            logger.error(f"Error syncing product {product.get('sku', 'unknown')} to Dolibarr: {e}")
            errors += 1
    
    # Final progress update
    if sync_job_id:
        await db.sync_jobs.update_one(
            {"id": sync_job_id},
            {"$set": {
                "progress": 95,
                "processed_items": processed,
                "created": created,
                "updated": updated,
                "errors": errors,
                "current_step": "Finalizando sincronización de productos..."
            }}
        )
    
    return {
        "status": "success" if errors == 0 else "partial",
        "message": f"{created} creados, {updated} actualizados, {errors} errores, {images_synced} imágenes, {stock_synced} stocks",
        "created": created,
        "updated": updated,
        "errors": errors,
        "images_synced": images_synced,
        "stock_synced": stock_synced
    }


async def sync_suppliers_to_dolibarr(client: DolibarrClient, user_id: str) -> Dict:
    """Sync suppliers from our system to Dolibarr and link products to suppliers"""
    # Get user's suppliers
    suppliers = await db.suppliers.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(1000)
    
    if not suppliers:
        return {"status": "warning", "message": "No hay proveedores para sincronizar", "created": 0, "updated": 0}
    
    created = 0
    updated = 0
    errors = 0
    supplier_mapping = {}  # our_id -> dolibarr_id
    
    for supplier in suppliers:
        try:
            # Check if supplier exists in Dolibarr by name
            existing = client.get_supplier_by_name(supplier.get("name", ""))
            
            supplier_data = {
                "name": supplier.get("name", ""),
                "email": supplier.get("email", ""),
                "phone": supplier.get("phone", ""),
                "address": supplier.get("address", ""),
                "city": supplier.get("city", ""),
                "zip": supplier.get("zip", ""),
                "country_code": supplier.get("country_code", "ES"),
                "notes": f"Tipo conexión: {supplier.get('connection_type', 'N/A')}. Productos: {supplier.get('product_count', 0)}"
            }
            
            if existing:
                dolibarr_id = int(existing.get("id"))
                result = client.update_supplier(dolibarr_id, supplier_data)
                if result["status"] == "success":
                    updated += 1
                    supplier_mapping[supplier["id"]] = dolibarr_id
                else:
                    logger.warning(f"Failed to update supplier '{supplier.get('name', '')}' in Dolibarr: {result.get('message', '')}")
                    errors += 1
            else:
                result = client.create_supplier(supplier_data)
                if result["status"] == "success":
                    created += 1
                    dolibarr_id = result.get("supplier_id")
                    supplier_mapping[supplier["id"]] = dolibarr_id
                    # Store Dolibarr ID in our supplier record
                    await db.suppliers.update_one(
                        {"id": supplier["id"]},
                        {"$set": {"dolibarr_id": dolibarr_id}}
                    )
                else:
                    logger.warning(f"Failed to create supplier '{supplier.get('name', '')}' in Dolibarr: {result.get('message', '')}")
                    errors += 1
        except Exception as e:
            logger.error(f"Error syncing supplier {supplier.get('name', 'unknown')} to Dolibarr: {e}")
            errors += 1
    
    # Now link products to their suppliers in Dolibarr
    products_linked = 0
    if supplier_mapping:
        try:
            # Get selected products for this user
            products = await db.products.find(
                {"user_id": user_id, "is_selected": True},
                {"_id": 0, "sku": 1, "supplier_id": 1, "price": 1}
            ).to_list(10000)
            
            for product in products:
                supplier_id = product.get("supplier_id")
                if supplier_id and supplier_id in supplier_mapping:
                    dolibarr_supplier_id = supplier_mapping[supplier_id]
                    sku = product.get("sku", "")
                    purchase_price = product.get("price", 0)
                    
                    if sku and dolibarr_supplier_id:
                        # Try to link product to supplier in Dolibarr
                        result = client.link_product_to_supplier(sku, dolibarr_supplier_id, purchase_price)
                        if result.get("status") == "success":
                            products_linked += 1
        except Exception as e:
            logger.error(f"Error linking products to suppliers: {e}")
    
    return {
        "status": "success" if errors == 0 else "partial",
        "message": f"{created} proveedores creados, {updated} actualizados, {errors} errores, {products_linked} productos vinculados",
        "created": created,
        "updated": updated,
        "errors": errors,
        "products_linked": products_linked
    }


async def sync_orders_to_dolibarr(client: DolibarrClient, user_id: str) -> Dict:
    """Import orders from WooCommerce stores to Dolibarr"""
    # Get user's WooCommerce stores
    stores = await db.woocommerce_configs.find(
        {"user_id": user_id, "platform": "woocommerce"},
        {"_id": 0}
    ).to_list(100)
    
    if not stores:
        return {"status": "info", "message": "No hay tiendas configuradas para importar pedidos", "imported": 0}
    
    imported = 0
    errors = 0
    
    for store in stores:
        try:
            # Get orders from WooCommerce
            from woocommerce import API as WooCommerceAPI
            
            wcapi = WooCommerceAPI(
                url=store.get("store_url", ""),
                consumer_key=store.get("consumer_key", ""),
                consumer_secret=store.get("consumer_secret", ""),
                version="wc/v3",
                timeout=30
            )
            
            # Get recent orders (last 30 days, pending/processing)
            response = wcapi.get("orders", params={
                "per_page": 100,
                "status": "processing,pending",
                "orderby": "date",
                "order": "desc"
            })
            
            if response.status_code != 200:
                continue
            
            wc_orders = response.json()
            
            for wc_order in wc_orders:
                try:
                    # Check if order already synced
                    existing = await db.crm_synced_orders.find_one({
                        "user_id": user_id,
                        "external_id": str(wc_order.get("id")),
                        "source": "woocommerce"
                    })
                    
                    if existing:
                        continue
                    
                    # Get or create customer in Dolibarr
                    customer_email = wc_order.get("billing", {}).get("email", "")
                    customer_name = f"{wc_order.get('billing', {}).get('first_name', '')} {wc_order.get('billing', {}).get('last_name', '')}".strip()
                    
                    # Build order lines
                    lines = []
                    for item in wc_order.get("line_items", []):
                        # Try to find product by SKU in Dolibarr
                        dolibarr_product = client.get_product_by_ref(item.get("sku", ""))
                        
                        lines.append({
                            "product_id": int(dolibarr_product.get("id")) if dolibarr_product else None,
                            "quantity": item.get("quantity", 1),
                            "price": float(item.get("price", 0)),
                            "description": item.get("name", "")
                        })
                    
                    # For now, we'll log the order - creating requires customer mapping
                    # Store synced order record
                    await db.crm_synced_orders.insert_one({
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "external_id": str(wc_order.get("id")),
                        "source": "woocommerce",
                        "store_id": store.get("id"),
                        "order_data": {
                            "customer_name": customer_name,
                            "customer_email": customer_email,
                            "total": wc_order.get("total"),
                            "status": wc_order.get("status"),
                            "date": wc_order.get("date_created"),
                            "lines_count": len(lines)
                        },
                        "synced_at": datetime.now(timezone.utc).isoformat()
                    })
                    
                    imported += 1
                except Exception as e:
                    logger.error(f"Error importing order {wc_order.get('id')}: {e}")
                    errors += 1
        except Exception as e:
            logger.error(f"Error fetching orders from store {store.get('id')}: {e}")
            errors += 1
    
    return {
        "status": "success" if errors == 0 else "partial",
        "message": f"{imported} pedidos importados, {errors} errores",
        "imported": imported,
        "errors": errors
    }


# ==================== ODOO SYNC FUNCTIONS ====================

async def sync_products_to_odoo(client: OdooClient, user_id: str, sync_settings: dict = None, catalog_id: str = None, sync_job_id: str = None) -> Dict:
    """Sync products from our catalog to Odoo with full data including purchase price, stock and images"""
    if sync_settings is None:
        sync_settings = {"products": True, "stock": True, "prices": True, "descriptions": True, "images": True}
    
    # Build query filter
    query = {"user_id": user_id, "is_selected": True}
    catalog_items_map = {}
    margin_rules = []
    
    # If catalog_id is provided, get only products from that catalog
    if catalog_id:
        catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user_id})
        if not catalog:
            return {"status": "error", "message": "Catálogo no encontrado", "created": 0, "updated": 0}
        
        catalog_items = await db.catalog_items.find(
            {"catalog_id": catalog_id},
            {"_id": 0}
        ).to_list(10000)
        
        if not catalog_items:
            return {"status": "warning", "message": "El catálogo no tiene productos", "created": 0, "updated": 0}
        
        product_ids = [item.get("product_id") for item in catalog_items if item.get("product_id")]
        if not product_ids:
            return {"status": "warning", "message": "El catálogo no tiene productos válidos", "created": 0, "updated": 0}
        
        catalog_items_map = {item.get("product_id"): item for item in catalog_items}
        
        margin_rules = await db.catalog_margin_rules.find(
            {"catalog_id": catalog_id},
            {"_id": 0}
        ).sort("priority", -1).to_list(100)
        
        query["_id"] = {"$in": product_ids}
    
    # Get products
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    
    if not products:
        return {"status": "warning", "message": "No hay productos para sincronizar", "created": 0, "updated": 0}
    
    created = 0
    updated = 0
    errors = 0
    
    for product in products:
        try:
            # Prepare product data for Odoo
            product_sku = product.get("sku", "")
            if not product_sku:
                logger.warning(f"Producto sin SKU: {product.get('name')}")
                errors += 1
                continue
            
            # Check if product exists in Odoo
            existing_product = client.get_product_by_sku(product_sku)
            
            product_data = {
                "name": product.get("name", ""),
                "sku": product_sku,
                "ean": product.get("ean", ""),
                "price": float(product.get("price", 0)),
                "cost_price": float(product.get("cost_price", 0)),
                "description": product.get("description", ""),
            }
            
            # Add image if available
            if sync_settings.get("images") and product.get("image_url"):
                product_data["image_url"] = product.get("image_url")
            
            if existing_product:
                # Update existing product
                result = client.update_product(existing_product.get("id"), product_data)
                if result.get("status") == "success":
                    updated += 1
                else:
                    errors += 1
            else:
                # Create new product
                result = client.create_product(product_data)
                if result.get("status") == "success":
                    created += 1
                    product_id = result.get("product_id")
                    
                    # Update stock if enabled
                    if sync_settings.get("stock") and product.get("stock"):
                        client.update_stock(product_id, int(product.get("stock", 0)))
                else:
                    errors += 1
        
        except Exception as e:
            logger.error(f"Error syncing product {product.get('sku', 'Unknown')}: {e}")
            errors += 1
    
    return {
        "status": "success" if errors == 0 else "partial",
        "message": f"{created} creados, {updated} actualizados, {errors} errores",
        "created": created,
        "updated": updated,
        "errors": errors
    }


async def sync_suppliers_to_odoo(client: OdooClient, user_id: str) -> Dict:
    """Sync suppliers from our database to Odoo"""
    suppliers = await db.suppliers.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(10000)
    
    if not suppliers:
        return {"status": "info", "message": "No hay proveedores para sincronizar", "created": 0, "updated": 0}
    
    created = 0
    updated = 0
    errors = 0
    
    for supplier in suppliers:
        try:
            # Find supplier in Odoo by name
            odoo_suppliers = client.get_suppliers()
            existing = None
            for s in odoo_suppliers:
                if s.get("name") == supplier.get("name"):
                    existing = s
                    break
            
            supplier_data = {
                "name": supplier.get("name", ""),
                "email": supplier.get("email", ""),
                "phone": supplier.get("phone", ""),
                "address": supplier.get("address", ""),
                "city": supplier.get("city", "")
            }
            
            if existing:
                result = client.update_supplier(existing.get("id"), supplier_data)
                if result.get("status") == "success":
                    updated += 1
                else:
                    errors += 1
            else:
                result = client.create_supplier(supplier_data)
                if result.get("status") == "success":
                    created += 1
                else:
                    errors += 1
        
        except Exception as e:
            logger.error(f"Error syncing supplier {supplier.get('name', 'Unknown')}: {e}")
            errors += 1
    
    return {
        "status": "success" if errors == 0 else "partial",
        "message": f"{created} creados, {updated} actualizados, {errors} errores",
        "created": created,
        "updated": updated,
        "errors": errors
    }


async def sync_orders_to_odoo(client: OdooClient, user_id: str) -> Dict:
    """Import orders from WooCommerce stores to Odoo"""
    stores = await db.woocommerce_configs.find(
        {"user_id": user_id, "platform": "woocommerce"},
        {"_id": 0}
    ).to_list(100)
    
    if not stores:
        return {"status": "info", "message": "No hay tiendas configuradas para importar pedidos", "imported": 0}
    
    imported = 0
    errors = 0
    
    for store in stores:
        try:
            from woocommerce import API as WooCommerceAPI
            
            wcapi = WooCommerceAPI(
                url=store.get("store_url", ""),
                consumer_key=store.get("consumer_key", ""),
                consumer_secret=store.get("consumer_secret", ""),
                version="wc/v3",
                timeout=30
            )
            
            # Get recent orders (pending/processing)
            response = wcapi.get("orders", params={
                "per_page": 100,
                "status": "processing,pending",
                "orderby": "date",
                "order": "desc"
            })
            
            if response.status_code != 200:
                continue
            
            wc_orders = response.json()
            
            for wc_order in wc_orders:
                try:
                    # Check if order already synced
                    existing = await db.crm_synced_orders.find_one({
                        "user_id": user_id,
                        "external_id": str(wc_order.get("id")),
                        "source": "woocommerce"
                    })
                    
                    if existing:
                        continue
                    
                    customer_email = wc_order.get("billing", {}).get("email", "")
                    customer_name = f"{wc_order.get('billing', {}).get('first_name', '')} {wc_order.get('billing', {}).get('last_name', '')}".strip()
                    
                    # Store synced order record
                    await db.crm_synced_orders.insert_one({
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "external_id": str(wc_order.get("id")),
                        "source": "woocommerce",
                        "store_id": store.get("id"),
                        "order_data": {
                            "customer_name": customer_name,
                            "customer_email": customer_email,
                            "total": wc_order.get("total"),
                            "status": wc_order.get("status"),
                            "date": wc_order.get("date_created"),
                            "lines_count": len(wc_order.get("line_items", []))
                        },
                        "synced_at": datetime.now(timezone.utc).isoformat()
                    })
                    
                    imported += 1
                except Exception as e:
                    logger.error(f"Error importing order {wc_order.get('id')}: {e}")
                    errors += 1
        except Exception as e:
            logger.error(f"Error fetching orders from store {store.get('id')}: {e}")
            errors += 1
    
    return {
        "status": "success" if errors == 0 else "partial",
        "message": f"{imported} pedidos importados, {errors} errores",
        "imported": imported,
        "errors": errors
    }


# ==================== GENERIC SYNC FOR NEW CRM PLATFORMS ====================

async def sync_products_generic(client, platform: str, user_id: str, sync_settings: dict = None, catalog_id: str = None, sync_job_id: str = None) -> Dict:
    """Generic product sync for HubSpot, Salesforce, Zoho, Pipedrive, Monday, Freshsales"""
    if sync_settings is None:
        sync_settings = {"products": True, "stock": True, "prices": True, "descriptions": True, "images": True}

    # Build query filter
    query = {"user_id": user_id, "is_selected": True}
    if catalog_id:
        catalog_items = await db.catalog_items.find(
            {"catalog_id": catalog_id},
            {"product_id": 1}
        ).to_list(10000)
        product_ids = [item["product_id"] for item in catalog_items]
        if not product_ids:
            if sync_job_id:
                await db.sync_jobs.update_one(
                    {"id": sync_job_id},
                    {"$set": {"status": "completed", "progress": 100, "current_step": "No hay productos en el catálogo seleccionado"}}
                )
            return {"status": "success", "message": "No hay productos en el catálogo", "created": 0, "updated": 0, "errors": 0}
        query["id"] = {"$in": product_ids}

    products = await db.products.find(query).to_list(10000)

    if not products:
        if sync_job_id:
            await db.sync_jobs.update_one(
                {"id": sync_job_id},
                {"$set": {"status": "completed", "progress": 100, "current_step": "No hay productos seleccionados para sincronizar"}}
            )
        return {"status": "success", "message": "No hay productos seleccionados", "created": 0, "updated": 0, "errors": 0}

    # Build catalog items map for pricing
    catalog_items_map = {}
    if catalog_id:
        cat_items = await db.catalog_items.find({"catalog_id": catalog_id}).to_list(10000)
        for ci in cat_items:
            catalog_items_map[ci["product_id"]] = ci

    total = len(products)
    created = 0
    updated = 0
    errors = 0

    if sync_job_id:
        await db.sync_jobs.update_one(
            {"id": sync_job_id},
            {"$set": {"current_step": f"Sincronizando {total} productos con {platform.capitalize()}...", "total_items": total}}
        )

    platform_name_map = {
        "hubspot": "HubSpot", "salesforce": "Salesforce", "zoho": "Zoho CRM",
        "pipedrive": "Pipedrive", "monday": "Monday CRM", "freshsales": "Freshsales"
    }

    for i, product in enumerate(products):
        try:
            sku = product.get("sku") or product.get("reference") or ""
            name = product.get("name", "Sin nombre")
            price = product.get("price", 0)
            stock_qty = product.get("stock", 0)

            # Apply catalog pricing if available
            cat_item = catalog_items_map.get(product["id"])
            if cat_item and cat_item.get("final_price"):
                price = cat_item["final_price"]
            elif cat_item:
                price = await calculate_final_price(product, catalog_id)

            # Build platform-specific product data
            product_data = _build_product_data(platform, product, name, sku, price, stock_qty, sync_settings)

            # Try to find existing product by SKU
            existing = client.get_product_by_sku(sku) if sku else None

            if existing:
                # Update existing product
                product_id = _get_product_id(platform, existing)
                if product_id and client.update_product(product_id, product_data):
                    updated += 1
                else:
                    errors += 1
            else:
                # Create new product
                result = client.create_product(product_data)
                if result:
                    created += 1
                else:
                    errors += 1

            # Update progress
            if sync_job_id and (i + 1) % 5 == 0:
                progress = int(((i + 1) / total) * 100)
                await db.sync_jobs.update_one(
                    {"id": sync_job_id},
                    {"$set": {
                        "progress": progress,
                        "processed_items": i + 1,
                        "created": created,
                        "updated": updated,
                        "errors": errors,
                        "current_step": f"Procesando producto {i + 1}/{total}..."
                    }}
                )
        except Exception as e:
            logger.error(f"Error syncing product {product.get('name', '?')} to {platform}: {e}")
            errors += 1

    pname = platform_name_map.get(platform, platform)
    return {
        "status": "success" if errors == 0 else "partial",
        "message": f"{created} creados, {updated} actualizados, {errors} errores en {pname}",
        "created": created,
        "updated": updated,
        "errors": errors
    }


def _build_product_data(platform: str, product: dict, name: str, sku: str, price: float, stock_qty: int, sync_settings: dict) -> Dict:
    """Build platform-specific product data dict"""
    description = product.get("description", "") if sync_settings.get("descriptions") else ""

    if platform == "hubspot":
        data = {"name": name, "hs_sku": sku, "price": str(price)}
        if description:
            data["description"] = description
        if sync_settings.get("stock"):
            data["hs_cost_of_goods_sold"] = str(stock_qty)
        return data

    elif platform == "salesforce":
        data = {"Name": name, "ProductCode": sku, "IsActive": True}
        if description:
            data["Description"] = description
        return data

    elif platform == "zoho":
        data = {"Product_Name": name, "Product_Code": sku, "Unit_Price": price}
        if description:
            data["Description"] = description
        if sync_settings.get("stock"):
            data["Qty_in_Stock"] = stock_qty
        return data

    elif platform == "pipedrive":
        data = {"name": name, "code": sku}
        if sync_settings.get("prices"):
            data["prices"] = [{"price": price, "currency": "EUR"}]
        if description:
            data["description"] = description
        return data

    elif platform == "monday":
        import json
        columns = {}
        if sku:
            columns["sku"] = sku
        if sync_settings.get("prices"):
            columns["numbers"] = price
        if description:
            columns["text"] = description
        return {"name": name, "column_values": json.dumps(columns)}

    elif platform == "freshsales":
        data = {"name": name, "sku": sku, "unit_price": price}
        if description:
            data["description"] = description
        return data

    return {"name": name}


def _get_product_id(platform: str, existing: dict) -> Optional[str]:
    """Extract product ID from platform-specific response"""
    if platform == "hubspot":
        return existing.get("id")
    elif platform == "salesforce":
        return existing.get("Id")
    elif platform == "zoho":
        return existing.get("id")
    elif platform == "pipedrive":
        return str(existing.get("id", ""))
    elif platform == "monday":
        return existing.get("id")
    elif platform == "freshsales":
        return str(existing.get("id", ""))
    return existing.get("id")

