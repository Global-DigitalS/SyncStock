"""
CRM sync functions for all supported platforms.
Handles product, supplier, and order synchronization with Dolibarr, Odoo, and generic CRMs.
"""
import logging
import asyncio
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List

from services.database import db
from services.sync import calculate_final_price
from services.crm_clients import (
    DolibarrClient, OdooClient,
    create_crm_client, FULL_SYNC_PLATFORMS, BASIC_SYNC_PLATFORMS,
)

logger = logging.getLogger(__name__)


# ==================== FASE 2-3: GLOBAL RATE LIMITER & CACHING ====================

class GlobalRateLimiter:
    """Global rate limiter for CRM API calls to prevent exceeding rate limits - DEADLOCK SAFE"""

    def __init__(self, max_concurrent: int = 5, min_delay: float = 0.1):
        """
        Initialize rate limiter.

        Args:
            max_concurrent: Maximum concurrent operations
            min_delay: Minimum delay between operations (seconds)
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.min_delay = min_delay
        self.last_call = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire the rate limiter - respects both concurrency and delay"""
        # FIXED: Don't hold lock inside semaphore to prevent deadlock
        # First acquire semaphore (concurrency control)
        async with self.semaphore:
            # Then acquire lock ONLY for reading/updating last_call
            async with self.lock:
                elapsed = time.time() - self.last_call
                if elapsed < self.min_delay:
                    sleep_time = self.min_delay - elapsed

            # Sleep OUTSIDE the lock to prevent blocking other tasks
            if elapsed < self.min_delay:
                await asyncio.sleep(sleep_time)

            # Update last_call under lock
            async with self.lock:
                self.last_call = time.time()


class SyncCache:
    """In-memory cache for CRM data with TTL support (FASE 3) - THREAD SAFE"""

    def __init__(self, ttl_seconds: int = 1800, max_size: int = 10000):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cached entries (default 30 minutes)
            max_size: Maximum number of entries before eviction (prevents OOM)
        """
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.lock = asyncio.Lock()  # Thread-safe access

    async def get(self, key: str):
        """Get value from cache if not expired - THREAD SAFE"""
        async with self.lock:
            if key not in self.cache:
                return None

            elapsed = time.time() - self.timestamps.get(key, 0)
            if elapsed > self.ttl:
                # Entry expired - safe to delete
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
                return None

            return self.cache[key]

    async def set(self, key: str, value):
        """Store value in cache with current timestamp - THREAD SAFE"""
        async with self.lock:
            # Evict if cache is full (simple LRU by removing oldest non-expired)
            if len(self.cache) >= self.max_size:
                # Find and remove oldest entry
                if self.timestamps:
                    oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
                    self.cache.pop(oldest_key, None)
                    self.timestamps.pop(oldest_key, None)

            self.cache[key] = value
            self.timestamps[key] = time.time()
            logger.debug(f"Cached {key}: TTL in {self.ttl}s (cache size: {len(self.cache)})")

    async def clear_expired(self):
        """Remove all expired entries - THREAD SAFE"""
        async with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, ts in self.timestamps.items()
                if current_time - ts > self.ttl
            ]
            for key in expired_keys:
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)

    async def size(self) -> int:
        """Get current cache size - THREAD SAFE"""
        async with self.lock:
            return len(self.cache)

    async def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry - MEDIUM #14

        Returns:
            True if entry was cached and removed, False otherwise
        """
        async with self.lock:
            if key in self.cache:
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
                logger.debug(f"Invalidated cache entry: {key}")
                return True
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching a pattern - MEDIUM #14

        Args:
            pattern: Simple prefix pattern (e.g., "sku:*" matches "sku:123")

        Returns:
            Number of entries invalidated
        """
        async with self.lock:
            import fnmatch
            prefix = pattern.replace('*', '')
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
            if keys_to_remove:
                logger.debug(f"Invalidated {len(keys_to_remove)} cache entries matching pattern: {pattern}")
            return len(keys_to_remove)

    async def clear_all(self):
        """Clear entire cache - MEDIUM #14"""
        async with self.lock:
            size = len(self.cache)
            self.cache.clear()
            self.timestamps.clear()
            logger.info(f"Cleared entire cache ({size} entries)")


def build_differential_update_payload(local_product: Dict, crm_product: Dict, fields_to_check: List[str] = None) -> Dict:
    """
    Build update payload with only changed fields (FASE 3: Differential Updates) - SAFE TYPE HANDLING.

    This reduces bandwidth and API calls by only sending fields that actually changed.

    Args:
        local_product: Product data from our system
        crm_product: Product data from CRM system
        fields_to_check: List of fields to compare (if None, uses predefined list)

    Returns:
        Dict with only changed fields, or empty dict if no changes
    """
    if fields_to_check is None:
        fields_to_check = ["name", "price", "cost_price", "description", "short_description", "stock", "ean", "weight"]

    if not isinstance(local_product, dict) or not isinstance(crm_product, dict):
        logger.error(f"build_differential_update_payload: Invalid input types - local={type(local_product)}, crm={type(crm_product)}")
        return {}

    payload = {}

    for field in fields_to_check:
        try:
            local_val = local_product.get(field)
            crm_val = crm_product.get(field)

            # For numeric fields, compare as floats
            if field in ["price", "cost_price", "weight", "stock"]:
                try:
                    local_num = float(local_val) if local_val else 0
                    crm_num = float(crm_val) if crm_val else 0
                    if abs(local_num - crm_num) > 0.01:  # Allow small floating point differences
                        payload[field] = local_val
                except (ValueError, TypeError):
                    # Fallback to string comparison if conversion fails
                    local_str = _safe_to_string(local_val)
                    crm_str = _safe_to_string(crm_val)
                    if local_str != crm_str:
                        payload[field] = local_val
            else:
                # String comparison - SAFE conversion
                local_str = _safe_to_string(local_val)
                crm_str = _safe_to_string(crm_val)
                if local_str != crm_str:
                    payload[field] = local_val

        except Exception as e:
            logger.error(f"Error comparing field {field}: {e}")
            # Include field in payload to be safe (data loss prevention)
            payload[field] = local_val

    return payload


def _safe_to_string(value) -> str:
    """Safely convert value to string for comparison - PREVENTS TYPE ERRORS"""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    # For complex types (dict, list), don't include in update
    logger.debug(f"Skipping complex type comparison: {type(value)}")
    return ""


async def validate_and_cleanup_sync_jobs(user_id: str, max_age_days: int = 30):
    """Validate sync job timestamps and cleanup old jobs - MEDIUM #22

    Ensures:
    - completed_at > started_at
    - Removes sync jobs older than max_age_days
    - Logs validation errors
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        cutoff_iso = cutoff_date.isoformat()

        # Find old or invalid jobs
        invalid_jobs = await db.sync_jobs.find({
            "user_id": user_id,
            "$or": [
                {"started_at": {"$lt": cutoff_iso}},  # Older than max_age_days
                {
                    "status": "completed",
                    "$expr": {
                        "$lte": ["$completed_at", "$started_at"]  # completed_at <= started_at (invalid)
                    }
                }
            ]
        }).to_list(1000)

        if invalid_jobs:
            logger.info(f"Found {len(invalid_jobs)} invalid or expired sync jobs for user {user_id}")
            for job in invalid_jobs:
                if job.get("started_at") and job.get("completed_at"):
                    try:
                        started = datetime.fromisoformat(job["started_at"].replace('Z', '+00:00'))
                        completed = datetime.fromisoformat(job["completed_at"].replace('Z', '+00:00'))
                        if completed <= started:
                            logger.warning(
                                f"Invalid sync job {job['id']}: "
                                f"completed_at ({completed}) <= started_at ({started})"
                            )
                    except Exception as e:
                        logger.warning(f"Error validating job {job['id']}: {e}")

            # Delete old jobs (keep last 30 days)
            result = await db.sync_jobs.delete_many({
                "user_id": user_id,
                "started_at": {"$lt": cutoff_iso}
            })

            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old sync jobs")

    except Exception as e:
        logger.error(f"Error in validate_and_cleanup_sync_jobs: {e}")


def validate_margin_rules(rules: List[Dict]) -> List[Dict]:
    """Validate margin rules before use - MEDIUM #20

    Filters out invalid rules that would cause calculation errors.

    Returns:
        List of valid margin rules
    """
    if not rules:
        return []

    valid_rules = []
    for i, rule in enumerate(rules):
        try:
            if not isinstance(rule, dict):
                logger.warning(f"Margin rule {i}: not a dict, skipping")
                continue

            # Validate required fields
            if "type" not in rule or "value" not in rule:
                logger.warning(f"Margin rule {i}: missing type or value, skipping")
                continue

            rule_type = rule.get("type", "").lower()
            rule_value = rule.get("value")

            # Validate type
            if rule_type not in ["percentage", "fixed", "multiplier"]:
                logger.warning(f"Margin rule {i}: invalid type '{rule_type}', skipping")
                continue

            # Validate value is numeric
            try:
                float_value = float(rule_value)
            except (ValueError, TypeError):
                logger.warning(f"Margin rule {i}: value '{rule_value}' is not numeric, skipping")
                continue

            # Validate value range
            if rule_type == "percentage" and (float_value < -100 or float_value > 1000):
                logger.warning(f"Margin rule {i}: percentage {float_value} is out of reasonable range, skipping")
                continue

            if rule_type == "multiplier" and (float_value <= 0 or float_value > 100):
                logger.warning(f"Margin rule {i}: multiplier {float_value} must be > 0, skipping")
                continue

            valid_rules.append(rule)
        except Exception as e:
            logger.error(f"Error validating margin rule {i}: {e}")
            continue

    if len(valid_rules) < len(rules):
        logger.info(f"Margin rules validation: {len(valid_rules)}/{len(rules)} rules are valid")

    return valid_rules

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

    client = None
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
    finally:
        # ALWAYS close client - even if exception occurs (prevents resource leak)
        if client:
            try:
                client.close()
            except Exception as e:
                logger.error(f"Error closing CRM client: {e}")


# ==================== HELPER FUNCTIONS FOR FASE 2 (PARALLELISM) ====================

async def _sync_product_create_dolibarr(
    client: DolibarrClient,
    product: Dict,
    product_data: Dict,
    image_url: str,
    sync_settings: Dict,
    limiter: GlobalRateLimiter,
    cache: SyncCache = None
) -> Dict:
    """Create a single product with rate limiting"""
    try:
        await limiter.acquire()
        result = await client.create_product_async(product_data)

        if result.get("status") == "success":
            sku = product.get("sku")
            product_id = result.get("product_id")

            # Cache the new product data if cache is available
            if cache:
                await cache.set(sku, product_data)

            # Sync stock using stock movements for accurate tracking
            if sync_settings.get("stock", True):
                stock_value = product_data.get("stock", 0)
                await limiter.acquire()
                stock_result = await client.update_stock_async(product_id, stock_value)
                if stock_result.get("status") != "success":
                    logger.warning(f"Stock warning for new product {sku}: {stock_result.get('message')}")

            # Image is uploaded in create_product if image_url is provided
            if image_url and sync_settings.get("images", True):
                await limiter.acquire()
                await client.upload_product_image_async(product_id, image_url)

            return {"status": "success", "sku": sku}
        else:
            return {"status": "error", "sku": product.get("sku"), "message": result.get("message")}
    except Exception as e:
        logger.error(f"Error creating product {product.get('sku')}: {e}")
        return {"status": "error", "sku": product.get("sku"), "message": str(e)}


async def _sync_product_update_dolibarr(
    client: DolibarrClient,
    product: Dict,
    existing: Dict,
    product_data: Dict,
    image_url: str,
    sync_settings: Dict,
    limiter: GlobalRateLimiter,
    cache: SyncCache = None
) -> Dict:
    """Update a single product with rate limiting and differential updates"""
    try:
        sku = product.get("sku")
        product_id = int(existing.get("id"))

        # ========== FASE 3: Differential Updates ==========
        # Only send fields that actually changed
        update_payload = build_differential_update_payload(product_data, existing)

        if not update_payload and not image_url:
            # No changes needed
            logger.debug(f"Producto {sku} sin cambios, omitiendo actualización")
            return {"status": "success", "sku": sku}

        # Only update if there are actual changes
        if update_payload:
            await limiter.acquire()
            result = await client.update_product_async(product_id, update_payload)

            if result.get("status") != "success":
                return {"status": "error", "sku": sku, "message": result.get("message")}

            # Cache the updated product data if cache is available
            if cache:
                await cache.set(sku, {**existing, **update_payload})

        # Sync stock using stock movements for accurate tracking
        if sync_settings.get("stock", True) and "stock" in update_payload:
            validated_stock = product_data.get("stock", 0)
            await limiter.acquire()
            stock_result = await client.update_stock_async(product_id, validated_stock)
            if stock_result.get("status") != "success":
                logger.warning(f"Stock warning for {sku}: {stock_result.get('message')}")

        # Upload image separately for better handling
        if image_url and sync_settings.get("images", True):
            await limiter.acquire()
            await client.upload_product_image_async(product_id, image_url)

        return {"status": "success", "sku": sku}
    except Exception as e:
        logger.error(f"Error updating product {product.get('sku')}: {e}")
        return {"status": "error", "sku": product.get("sku"), "message": str(e)}


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

        # MEDIUM #20: Validate margin rules before using them
        margin_rules = validate_margin_rules(margin_rules)
        logger.info(f"Found {len(margin_rules)} valid margin rules for catalog {catalog_id}")

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

    # ========== FASE 1 OPTIMIZATION: Batch detection ==========
    # Extract all SKUs and do BATCH detection in ONE call instead of N calls in the loop
    skus = [p.get("sku") for p in products if p.get("sku")]
    if skus:
        logger.info(f"Fase 1: Batch detection de {len(skus)} productos (1 API call en lugar de {len(skus)})")
        existing_products_batch = client.get_products_by_refs_batch(skus)  # Single batch call
    else:
        existing_products_batch = {}

    created = 0
    updated = 0
    errors = 0
    error_details = {}  # NEW: Track error details {sku: "error message"}

    # ========== FASE 2 OPTIMIZATION: Parallelism with chunking ==========
    # Phase 2A: Prepare all product data without making API calls
    logger.info(f"Fase 2: Preparando {len(products)} productos para sincronización paralela...")

    to_create = []  # Products without existing CRM entry
    to_update = []  # Products with existing CRM entry

    for product in products:
        sku = product.get("sku", "")
        if not sku:
            errors += 1
            error_details[f"producto_{len(error_details)}"] = "Producto sin SKU"
            continue

        # HIGH #7: Sanitize SKU for safe use as dict key
        # Remove special characters that could cause issues in JSON/DB
        safe_sku = sku.replace('"', '').replace("'", '').replace('\x00', '')[:100]

        # Use batch result to check if product exists
        existing = existing_products_batch.get(sku)

        # CRITICAL: Double-check before creating to prevent race condition
        # Between batch lookup and actual creation, another user/job might create the product
        if not existing:
            # Make one final check to catch concurrent creations
            final_check = client.get_product_by_ref(sku)
            if final_check:
                logger.debug(f"Race condition prevented: {sku} was created by another sync job")
                existing = final_check

        # Build product_data
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

            # Sale price calculation
            sale_price = None

            if catalog_item and catalog_item.get("custom_price"):
                sale_price = float(catalog_item.get("custom_price"))
                logger.debug(f"Using custom_price for {sku}: {sale_price}")
            elif margin_rules and purchase_price > 0:
                sale_price = calculate_final_price(purchase_price, product, margin_rules)
                logger.debug(f"Calculated sale_price for {sku}: {purchase_price} -> {sale_price}")

            if not sale_price:
                sale_price = product.get("final_price") or product.get("pvp") or product.get("custom_price")

            if not sale_price and purchase_price:
                sale_price = purchase_price

            product_data["price"] = round(float(sale_price or 0), 2)

        # Sync stock - HIGH #9 & MEDIUM #21: Enhanced validation
        if sync_settings.get("stock", True):
            stock_value = product.get("stock", 0)

            # Convert to number if possible
            if isinstance(stock_value, str):
                try:
                    stock_value = float(stock_value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid stock value (non-numeric string) for {sku}: {stock_value}. Using 0.")
                    stock_value = 0

            # Validate numeric value
            if isinstance(stock_value, (int, float)):
                # Check for negative values (invalid)
                if stock_value < 0:
                    logger.warning(f"Negative stock value for {sku}: {stock_value}. Using 0.")
                    stock_value = 0
                # Check for suspiciously large values
                elif stock_value > 1000000:
                    logger.warning(f"Stock value suspiciously large for {sku}: {stock_value}. Capping at 1000000.")
                    stock_value = 1000000
                # Round down floats with proper rounding
                elif isinstance(stock_value, float):
                    stock_value = int(stock_value + 0.0)  # Round down
                    if stock_value != float(product.get("stock", 0)):
                        logger.debug(f"Rounded stock for {sku}: {product.get('stock')} → {stock_value}")
            else:
                # Non-numeric value
                logger.warning(f"Non-numeric stock value for {sku}: {stock_value}. Using 0.")
                stock_value = 0

            product_data["stock"] = max(0, int(stock_value))

        # Sync descriptions
        if sync_settings.get("descriptions", True):
            product_data["description"] = product.get("description", "")
            product_data["short_description"] = product.get("short_description", "")
            product_data["long_description"] = product.get("long_description", "")
            product_data["brand"] = product.get("brand", "")

            supplier = suppliers_map.get(product.get("supplier_id"))
            if supplier:
                product_data["supplier_name"] = supplier.get("name", "")

        product_data["ean"] = product.get("ean", "")
        product_data["weight"] = product.get("weight", 0)

        # Handle image URL
        image_url = product.get("image_url", "") if sync_settings.get("images", True) else ""

        # Separate into create/update groups
        if existing:
            to_update.append({"product": product, "existing": existing, "product_data": product_data, "image_url": image_url})
        else:
            to_create.append({"product": product, "product_data": product_data, "image_url": image_url})

    # Phase 2B: Process creates and updates in parallel with memory optimization
    logger.info(f"Fase 2: Procesando en paralelo: {len(to_create)} creaciones, {len(to_update)} actualizaciones")

    # ========== FASE 3 OPTIMIZATION: In-memory cache with TTL ==========
    # Cache products for repeated lookups during sync or future syncs
    cache = SyncCache(ttl_seconds=1800)  # 30 minutes TTL
    logger.info(f"Fase 3: Caché de productos inicializada (TTL: 30 min)")

    limiter = GlobalRateLimiter(max_concurrent=5, min_delay=0.1)

    # MEDIUM #18: Chunk tasks to prevent memory exhaustion with large product counts
    # Create all items first, but process in chunks to control memory usage
    all_tasks_items = []
    for item in to_create:
        all_tasks_items.append({
            "type": "create",
            "item": item,
            "client": client,
            "sync_settings": sync_settings,
            "limiter": limiter,
            "cache": cache
        })

    for item in to_update:
        all_tasks_items.append({
            "type": "update",
            "item": item,
            "client": client,
            "sync_settings": sync_settings,
            "limiter": limiter,
            "cache": cache
        })

    # Process in chunks to prevent OS limits on concurrent tasks
    CHUNK_SIZE = 100  # Process 100 products at a time
    results = []
    total_chunks = (len(all_tasks_items) + CHUNK_SIZE - 1) // CHUNK_SIZE

    for chunk_num in range(total_chunks):
        start_idx = chunk_num * CHUNK_SIZE
        end_idx = min((chunk_num + 1) * CHUNK_SIZE, len(all_tasks_items))
        chunk = all_tasks_items[start_idx:end_idx]

        logger.info(f"Procesando chunk {chunk_num + 1}/{total_chunks} ({len(chunk)} items)")

        # Create tasks for this chunk only
        chunk_tasks = []
        for task_config in chunk:
            if task_config["type"] == "create":
                task = _sync_product_create_dolibarr(
                    task_config["client"],
                    task_config["item"]["product"],
                    task_config["item"]["product_data"],
                    task_config["item"]["image_url"],
                    task_config["sync_settings"],
                    task_config["limiter"],
                    task_config["cache"]
                )
            else:  # update
                task = _sync_product_update_dolibarr(
                    task_config["client"],
                    task_config["item"]["product"],
                    task_config["item"]["existing"],
                    task_config["item"]["product_data"],
                    task_config["item"]["image_url"],
                    task_config["sync_settings"],
                    task_config["limiter"],
                    task_config["cache"]
                )
            chunk_tasks.append(task)

        # Execute chunk in parallel
        chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
        results.extend(chunk_results)

        # Update sync job progress
        if sync_job_id:
            progress = int(((start_idx + len(chunk)) / len(all_tasks_items)) * 90)
            await db.sync_jobs.update_one(
                {"id": sync_job_id},
                {"$set": {
                    "progress": progress,
                    "current_step": f"Procesando chunk {chunk_num + 1}/{total_chunks}..."
                }}
            )

    # Process results and collect error details
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Task failed with exception: {result}")
            errors += 1
            error_details[f"exception_{errors}"] = str(result)
        elif isinstance(result, dict):
            if result.get("status") == "success":
                if result.get("sku") in [p.get("sku") for p in [item["product"] for item in to_create]]:
                    created += 1
                else:
                    updated += 1
            else:
                errors += 1
                # NEW: Store detailed error message for this product
                sku = result.get("sku", f"unknown_{errors}")
                error_msg = result.get("message", "Error desconocido")
                # HIGH #7: Sanitize SKU for safe database storage
                safe_sku = sku.replace('"', '').replace("'", '').replace('\x00', '')[:100]
                error_details[safe_sku] = error_msg
                logger.error(f"Product {sku} sync error: {error_msg}")
    
    # Final progress update
    if sync_job_id:
        processed_items = len(to_create) + len(to_update)
        await db.sync_jobs.update_one(
            {"id": sync_job_id},
            {"$set": {
                "progress": 95,
                "processed_items": processed_items,
                "created": created,
                "updated": updated,
                "errors": errors,
                "error_details": error_details,  # NEW: Store detailed error information
                "current_step": "Finalizando sincronización de productos..."
            }}
        )

    return {
        "status": "success" if errors == 0 else "partial",
        "message": f"{created} creados, {updated} actualizados, {errors} errores",
        "created": created,
        "updated": updated,
        "errors": errors
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

            # HIGH #5 FIX: Batch lookup all SKUs from all orders BEFORE processing individual orders
            # Prevents N+1 query problem: collect all unique SKUs, lookup in one batch call
            all_skus = set()
            for wc_order in wc_orders:
                for item in wc_order.get("line_items", []):
                    sku = item.get("sku", "")
                    if sku:
                        all_skus.add(sku)

            # Single batch lookup for all products
            products_batch = {}
            if all_skus:
                products_batch = client.get_products_by_refs_batch(list(all_skus))
                logger.info(f"Batch lookup: {len(all_skus)} SKUs → {len(products_batch)} products found")

            for wc_order in wc_orders:
                try:
                    order_external_id = str(wc_order.get("id"))

                    # HIGH #10: Check BOTH local DB AND CRM for idempotency
                    # 1. Check local sync record
                    existing = await db.crm_synced_orders.find_one({
                        "user_id": user_id,
                        "external_id": order_external_id,
                        "source": "woocommerce"
                    })

                    if existing:
                        logger.debug(f"Order {order_external_id} already synced locally")
                        continue

                    # 2. Check if order already exists in Dolibarr (by external_id field)
                    # This prevents duplicates if local record was deleted
                    try:
                        crm_orders = client.search_orders_by_external_id(order_external_id)
                        if crm_orders:
                            logger.info(f"Order {order_external_id} already exists in Dolibarr, skipping")
                            # Update local record to reflect this
                            await db.crm_synced_orders.insert_one({
                                "id": str(uuid.uuid4()),
                                "user_id": user_id,
                                "external_id": order_external_id,
                                "source": "woocommerce",
                                "store_id": store.get("id"),
                                "order_data": {"status": "already_synced"},
                                "synced_at": datetime.now(timezone.utc).isoformat()
                            })
                            continue
                    except Exception as check_err:
                        logger.warning(f"Could not check CRM for existing order {order_external_id}: {check_err}")
                        # Continue anyway - will be caught by unique constraint if duplicate

                    # Get or create customer in Dolibarr
                    customer_email = wc_order.get("billing", {}).get("email", "")
                    customer_name = f"{wc_order.get('billing', {}).get('first_name', '')} {wc_order.get('billing', {}).get('last_name', '')}".strip()

                    # Build order lines - use pre-fetched products from batch
                    lines = []
                    for item in wc_order.get("line_items", []):
                        sku = item.get("sku", "")
                        # Look up in batch result instead of making individual API call
                        dolibarr_product = products_batch.get(sku)

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


# ==================== HELPER FUNCTIONS FOR ODOO PARALLELISM ====================

async def _sync_product_create_odoo(
    client: OdooClient,
    product: Dict,
    product_data: Dict,
    sync_settings: Dict,
    limiter: GlobalRateLimiter,
    cache: SyncCache = None
) -> Dict:
    """Create a single Odoo product with rate limiting"""
    try:
        await limiter.acquire()
        result = await client.create_product_async(product_data)

        if result.get("status") == "success":
            sku = product.get("sku")
            product_id = result.get("product_id")

            # Cache the new product data if cache is available
            if cache:
                await cache.set(sku, product_data)

            # Update stock if enabled - CRITICAL: Always sync stock (not just if > 0)
            if sync_settings.get("stock", True):
                stock_value = product_data.get("stock", 0)
                await limiter.acquire()
                stock_result = await client.update_stock_async(product_id, int(stock_value))
                if stock_result.get("status") != "success":
                    logger.warning(f"Stock warning for new Odoo product {sku}: {stock_result.get('message')}")

            return {"status": "success", "sku": sku}
        else:
            return {"status": "error", "sku": product.get("sku"), "message": result.get("message")}
    except Exception as e:
        logger.error(f"Error creating Odoo product {product.get('sku')}: {e}")
        return {"status": "error", "sku": product.get("sku"), "message": str(e)}


async def _sync_product_update_odoo(
    client: OdooClient,
    product: Dict,
    existing_product: Dict,
    product_data: Dict,
    sync_settings: Dict,
    limiter: GlobalRateLimiter,
    cache: SyncCache = None
) -> Dict:
    """Update a single Odoo product with rate limiting and differential updates"""
    try:
        sku = product.get("sku")

        # ========== FASE 3: Differential Updates ==========
        update_payload = build_differential_update_payload(product_data, existing_product)

        if not update_payload:
            # No changes needed
            logger.debug(f"Producto Odoo {sku} sin cambios, omitiendo actualización")
            return {"status": "success", "sku": sku}

        await limiter.acquire()
        result = await client.update_product_async(product.get("id"), update_payload)

        if result.get("status") == "success":
            # Cache the updated product data if cache is available
            if cache:
                cache.set(sku, {**existing_product, **update_payload})
            return {"status": "success", "sku": sku}
        else:
            return {"status": "error", "sku": sku, "message": result.get("message")}
    except Exception as e:
        logger.error(f"Error updating Odoo product {product.get('sku')}: {e}")
        return {"status": "error", "sku": product.get("sku"), "message": str(e)}


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

    # ========== FASE 1 OPTIMIZATION: Batch detection ==========
    # Extract all SKUs and do BATCH detection in ONE call instead of N calls in the loop
    skus = [p.get("sku") for p in products if p.get("sku")]
    if skus:
        logger.info(f"Fase 1: Batch detection de {len(skus)} productos en Odoo (1 API call en lugar de {len(skus)})")
        existing_products_batch = client.get_products_by_skus_batch(skus)  # Single batch call
    else:
        existing_products_batch = {}

    created = 0
    updated = 0
    errors = 0
    error_details = {}  # NEW: Track error details {sku: "error message"}

    # ========== FASE 2 OPTIMIZATION: Parallelism with chunking for Odoo ==========
    logger.info(f"Fase 2: Preparando {len(products)} productos en Odoo para sincronización paralela...")

    to_create = []
    to_update = []

    for product in products:
        product_sku = product.get("sku", "")
        if not product_sku:
            logger.warning(f"Producto sin SKU: {product.get('name')}")
            errors += 1
            error_details[f"producto_{len(error_details)}"] = "Producto sin SKU"
            continue

        existing_product = existing_products_batch.get(product_sku)

        product_data = {
            "name": product.get("name", ""),
            "sku": product_sku,
            "ean": product.get("ean", ""),
            "price": float(product.get("price", 0)),
            "cost_price": float(product.get("cost_price", 0)),
            "description": product.get("description", ""),
        }

        # Sync stock - HIGH #9 & MEDIUM #21: Enhanced validation (Odoo)
        if sync_settings.get("stock", True):
            stock_value = product.get("stock", 0)

            # Convert to number if possible
            if isinstance(stock_value, str):
                try:
                    stock_value = float(stock_value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid stock value (non-numeric string) for {product_sku}: {stock_value}. Using 0.")
                    stock_value = 0

            # Validate numeric value
            if isinstance(stock_value, (int, float)):
                if stock_value < 0:
                    logger.warning(f"Negative stock value for {product_sku}: {stock_value}. Using 0.")
                    stock_value = 0
                elif stock_value > 1000000:
                    logger.warning(f"Stock value suspiciously large for {product_sku}: {stock_value}. Capping at 1000000.")
                    stock_value = 1000000
                elif isinstance(stock_value, float):
                    stock_value = int(stock_value + 0.0)
                    if stock_value != float(product.get("stock", 0)):
                        logger.debug(f"Rounded stock for {product_sku}: {product.get('stock')} → {stock_value}")
            else:
                logger.warning(f"Non-numeric stock value for {product_sku}: {stock_value}. Using 0.")
                stock_value = 0

            product_data["stock"] = max(0, int(stock_value))

        if sync_settings.get("images") and product.get("image_url"):
            product_data["image_url"] = product.get("image_url")

        if existing_product:
            to_update.append({"product": product, "existing_product": existing_product, "product_data": product_data})
        else:
            to_create.append({"product": product, "product_data": product_data})

    # Phase 2B: Process in parallel with memory optimization
    logger.info(f"Fase 2: Procesando en paralelo Odoo: {len(to_create)} creaciones, {len(to_update)} actualizaciones")

    # ========== FASE 3 OPTIMIZATION: In-memory cache with TTL ==========
    cache = SyncCache(ttl_seconds=1800)  # 30 minutes TTL
    logger.info(f"Fase 3: Caché de productos Odoo inicializado (TTL: 30 min)")

    limiter = GlobalRateLimiter(max_concurrent=5, min_delay=0.1)

    # MEDIUM #18: Chunk tasks to prevent memory exhaustion (Odoo)
    all_tasks_items = []
    for item in to_create:
        all_tasks_items.append({
            "type": "create",
            "item": item,
            "client": client,
            "sync_settings": sync_settings,
            "limiter": limiter,
            "cache": cache
        })

    for item in to_update:
        all_tasks_items.append({
            "type": "update",
            "item": item,
            "client": client,
            "sync_settings": sync_settings,
            "limiter": limiter,
            "cache": cache
        })

    # Process in chunks
    CHUNK_SIZE = 100
    results = []
    total_chunks = (len(all_tasks_items) + CHUNK_SIZE - 1) // CHUNK_SIZE

    for chunk_num in range(total_chunks):
        start_idx = chunk_num * CHUNK_SIZE
        end_idx = min((chunk_num + 1) * CHUNK_SIZE, len(all_tasks_items))
        chunk = all_tasks_items[start_idx:end_idx]

        logger.info(f"Procesando chunk {chunk_num + 1}/{total_chunks} ({len(chunk)} items) - Odoo")

        chunk_tasks = []
        for task_config in chunk:
            if task_config["type"] == "create":
                task = _sync_product_create_odoo(
                    task_config["client"],
                    task_config["item"]["product"],
                    task_config["item"]["product_data"],
                    task_config["sync_settings"],
                    task_config["limiter"],
                    task_config["cache"]
                )
            else:  # update
                task = _sync_product_update_odoo(
                    task_config["client"],
                    task_config["item"]["product"],
                    task_config["item"]["existing_product"],
                    task_config["item"]["product_data"],
                    task_config["sync_settings"],
                    task_config["limiter"],
                    task_config["cache"]
                )
            chunk_tasks.append(task)

        chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
        results.extend(chunk_results)

        # Update progress
        if sync_job_id:
            progress = int(((start_idx + len(chunk)) / len(all_tasks_items)) * 90)
            await db.sync_jobs.update_one(
                {"id": sync_job_id},
                {"$set": {
                    "progress": progress,
                    "current_step": f"Procesando chunk {chunk_num + 1}/{total_chunks} (Odoo)..."
                }}
            )

    # Process results and collect error details
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Odoo task failed with exception: {result}")
            errors += 1
            error_details[f"exception_{errors}"] = str(result)
        elif isinstance(result, dict):
            if result.get("status") == "success":
                if result.get("sku") in [p.get("sku") for p in [item["product"] for item in to_create]]:
                    created += 1
                else:
                    updated += 1
            else:
                errors += 1
                # NEW: Store detailed error message for this product
                sku = result.get("sku", f"unknown_{errors}")
                error_msg = result.get("message", "Error desconocido")
                # HIGH #7: Sanitize SKU for safe database storage
                safe_sku = sku.replace('"', '').replace("'", '').replace('\x00', '')[:100]
                error_details[safe_sku] = error_msg
                logger.error(f"Product {sku} sync error: {error_msg}")

    # Final progress update
    if sync_job_id:
        processed_items = len(to_create) + len(to_update)
        await db.sync_jobs.update_one(
            {"id": sync_job_id},
            {"$set": {
                "progress": 95,
                "processed_items": processed_items,
                "created": created,
                "updated": updated,
                "errors": errors,
                "error_details": error_details,  # NEW: Store detailed error information
                "current_step": "Finalizando sincronización de productos..."
            }}
        )

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
                    order_external_id = str(wc_order.get("id"))

                    # HIGH #10: Check BOTH local DB AND CRM for idempotency (Odoo version)
                    # 1. Check local sync record
                    existing = await db.crm_synced_orders.find_one({
                        "user_id": user_id,
                        "external_id": order_external_id,
                        "source": "woocommerce"
                    })

                    if existing:
                        logger.debug(f"Order {order_external_id} already synced locally (Odoo)")
                        continue

                    # 2. Check if order already exists in Odoo (by client_order_ref field)
                    try:
                        crm_orders = client.search_orders_by_external_id(order_external_id)
                        if crm_orders:
                            logger.info(f"Order {order_external_id} already exists in Odoo, skipping")
                            # Update local record
                            await db.crm_synced_orders.insert_one({
                                "id": str(uuid.uuid4()),
                                "user_id": user_id,
                                "external_id": order_external_id,
                                "source": "woocommerce",
                                "store_id": store.get("id"),
                                "order_data": {"status": "already_synced"},
                                "synced_at": datetime.now(timezone.utc).isoformat()
                            })
                            continue
                    except Exception as check_err:
                        logger.warning(f"Could not check Odoo for existing order {order_external_id}: {check_err}")
                        # Continue anyway

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

