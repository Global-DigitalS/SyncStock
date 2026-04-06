"""
Dolibarr ERP/CRM API Client.
"""
import asyncio
import base64
import logging
import time
from datetime import UTC, datetime

import requests

from .base import _validate_crm_url

logger = logging.getLogger(__name__)


# ==================== RETRY LOGIC WITH EXPONENTIAL BACKOFF ====================

async def retry_async(
    func,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 16.0,
    retryable_errors: tuple = (ConnectionError, TimeoutError, requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    retryable_status_codes: tuple = (429, 500, 502, 503, 504),
    *args,
    **kwargs
):
    """Retry async function with exponential backoff - OPTIMIZATION

    Automatically retries on transient failures:
    - Network errors (ConnectionError, TimeoutError)
    - Rate limits (429)
    - Server errors (500, 502, 503, 504)

    Does NOT retry on permanent errors:
    - 400 Bad Request
    - 401 Unauthorized
    - 403 Forbidden
    - 404 Not Found

    Args:
        func: Async function to call
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds (cap exponential growth)
        retryable_errors: Exception types to retry on
        retryable_status_codes: HTTP status codes to retry on
        *args, **kwargs: Arguments to pass to func
    """
    attempt = 0
    delay = initial_delay

    while attempt < max_retries:
        try:
            return await func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            # Check HTTP status code
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else None

            if status_code and status_code not in retryable_status_codes:
                # Permanent error - don't retry
                logger.warning(f"Not retrying permanent HTTP error {status_code}: {e}")
                raise

            # Transient error - log and retry
            attempt += 1
            if attempt >= max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for HTTP {status_code}: {e}")
                raise

            logger.warning(f"HTTP {status_code} error (attempt {attempt}/{max_retries}), retrying in {delay}s: {e}")
            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)

        except retryable_errors as e:
            # Transient network error - log and retry
            attempt += 1
            if attempt >= max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for {type(e).__name__}: {e}")
                raise

            logger.warning(f"{type(e).__name__} (attempt {attempt}/{max_retries}), retrying in {delay}s: {e}")
            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)

        except Exception as e:
            # Unexpected error - don't retry
            logger.error(f"Unexpected error (not retryable): {type(e).__name__}: {e}")
            raise


def retry_sync(
    func,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 16.0,
    retryable_errors: tuple = (ConnectionError, TimeoutError, requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    retryable_status_codes: tuple = (429, 500, 502, 503, 504),
    *args,
    **kwargs
):
    """Retry synchronous function with exponential backoff - OPTIMIZATION

    Same as retry_async but for blocking/sync operations.
    """
    attempt = 0
    delay = initial_delay

    while attempt < max_retries:
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            # Check HTTP status code
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else None

            if status_code and status_code not in retryable_status_codes:
                # Permanent error - don't retry
                logger.warning(f"Not retrying permanent HTTP error {status_code}: {e}")
                raise

            # Transient error - log and retry
            attempt += 1
            if attempt >= max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for HTTP {status_code}: {e}")
                raise

            logger.warning(f"HTTP {status_code} error (attempt {attempt}/{max_retries}), retrying in {delay}s: {e}")
            time.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)

        except retryable_errors as e:
            # Transient network error - log and retry
            attempt += 1
            if attempt >= max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for {type(e).__name__}: {e}")
                raise

            logger.warning(f"{type(e).__name__} (attempt {attempt}/{max_retries}), retrying in {delay}s: {e}")
            time.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)

        except Exception as e:
            # Unexpected error - don't retry
            logger.error(f"Unexpected error (not retryable): {type(e).__name__}: {e}")
            raise


def _safe_json_parse(response, default=None):
    """Safely parse JSON response with error handling - MEDIUM #19

    Prevents JSONDecodeError from crashing the sync.
    """
    try:
        return response.json()
    except ValueError as json_err:
        logger.warning(f"Failed to parse JSON response: {json_err}. Response text: {response.text[:100]}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return default


def _sanitize_error_message(error_text: str, max_length: int = 100) -> str:
    """Sanitize error messages to prevent information leakage - MEDIUM #15

    Removes sensitive details like internal paths, database info, etc.
    Only shows safe, generic error information.
    """
    if not error_text:
        return "Error en operación CRM"

    # Remove potentially sensitive patterns
    sanitized = error_text
    sensitive_patterns = [
        r'/home/\S+',  # File paths
        r'/var/\S+',   # System paths
        r'localhost:\d+',  # Local IPs
        r'192\.168\.\S+',  # Private IPs
        r'SELECT \*.*FROM',  # SQL queries
        r'UPDATE.*SET',  # SQL queries
        r'INSERT INTO',  # SQL queries
    ]

    import re
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)

    # Truncate to safe length
    sanitized = sanitized[:max_length]

    # If result is empty or all redacted, return generic message
    if not sanitized.strip() or sanitized == '[REDACTED]':
        return "Error en operación CRM"

    return sanitized


def _escape_sql_string(value: str) -> str:
    """Safely escape SQL string values to prevent SQL injection - MEDIUM #12

    Handles both standard SQL and MySQL comment sequences.
    """
    if not isinstance(value, str):
        return str(value)

    # 1. Escape single quotes by doubling them (SQL standard)
    escaped = value.replace("'", "''")

    # 2. Remove SQL comment sequences (multiple methods)
    # SQL Standard comments
    escaped = escaped.replace("--", "")
    # SQL Standard block comments
    escaped = escaped.replace("/*", "")
    escaped = escaped.replace("*/", "")
    # MySQL-specific comments
    escaped = escaped.replace("//", "")
    escaped = escaped.replace("#", "")  # MySQL single-line comment
    escaped = escaped.replace(";", "")  # Prevent statement termination

    # 3. Remove null bytes
    escaped = escaped.replace("\x00", "")

    # 4. Limit length to prevent buffer overflow
    escaped = escaped[:1000]

    return escaped.strip()


class DolibarrClient:
    """Dolibarr ERP/CRM API Client - Optimized with connection pooling and rate limiting"""

    def __init__(self, api_url: str, api_key: str):
        self.base_url = _validate_crm_url(api_url).rstrip('/')
        self.api_key = api_key
        self.headers = {
            'DOLAPIKEY': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        # Reusable session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        # Rate limiting: minimum delay between requests (seconds)
        self.min_delay = 0.1  # 100ms between requests
        self.last_request_time = 0

    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a rate-limited request with automatic retry on transient failures - OPTIMIZATION

        Retries on:
        - Network errors (timeouts, connection errors)
        - Rate limits (429)
        - Server errors (500, 502, 503, 504)

        Does NOT retry on:
        - 400 Bad Request
        - 401 Unauthorized
        - 403 Forbidden
        - 404 Not Found
        """
        # Ensure minimum delay between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)

        kwargs.setdefault('timeout', 30)

        # Use retry logic for the actual request (lambda to avoid positional/keyword arg mismatch)
        return retry_sync(
            lambda: self.session.request(method, url, **kwargs),
            max_retries=3,
            backoff_factor=2.0,
            initial_delay=1.0,
            max_delay=16.0
        )

    def close(self):
        """Close the session"""
        self.session.close()

    def test_connection(self) -> dict:
        """Test API connection"""
        try:
            response = self._rate_limited_request('GET', f"{self.base_url}/status", timeout=30)
            if response.status_code == 200:
                # MEDIUM #19: Safe JSON parsing
                data = _safe_json_parse(response, default={})
                if data:
                    return {
                        "status": "success",
                        "message": "Conexión exitosa a Dolibarr",
                        "version": data.get("success", {}).get("dolibarr_version", "Unknown")
                    }
                else:
                    return {"status": "error", "message": "Respuesta inválida del servidor"}
            elif response.status_code == 401:
                return {"status": "error", "message": "API Key inválida"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Acceso denegado - verifica permisos del usuario API"}
            else:
                # MEDIUM #15: Sanitize error message
                safe_msg = _sanitize_error_message(response.text)
                return {"status": "error", "message": f"Error de conexión ({response.status_code}): {safe_msg}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar al servidor. Verifica la URL."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"CRM connection error: {e}")
            return {"status": "error", "message": "Error de conexión al servidor CRM. Verifica la URL y las credenciales."}

    # ==================== PRODUCTS ====================

    def get_products(self, limit: int = 500) -> list[dict]:
        """Get products from Dolibarr"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/products",
                params={'limit': limit, 'sortfield': 'rowid', 'sortorder': 'DESC'},
                timeout=60
            )
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as json_err:
                    logger.error(f"Failed to parse JSON response from get_products: {json_err}")
                    return []
            # MEDIUM #13: Log non-200 responses instead of silently failing
            logger.warning(f"get_products failed with status {response.status_code}: {response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"Dolibarr get_products error: {e}")
            return []

    def get_product_by_ref(self, ref: str) -> dict | None:
        """Get a product by reference (SKU)

        Returns:
            Product dict if found
            None if not found (404)
            None if error (with logging)
        """
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/products/ref/{ref}",
                timeout=30
            )
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as json_err:
                    logger.error(f"Failed to parse JSON response for product {ref}: {json_err}")
                    return None
            elif response.status_code == 404:
                # Product not found - this is expected, return None
                logger.debug(f"Product with ref={ref} not found in Dolibarr (404)")
                return None
            else:
                # MEDIUM #13: Log unexpected status codes
                logger.warning(f"get_product_by_ref({ref}) failed with status {response.status_code}: {response.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"Dolibarr get_product_by_ref error for ref={ref}: {e}")
            return None

    def product_exists_by_ref(self, ref: str) -> bool:
        """Check if a product exists by reference (SKU) - simpler method"""
        return self.get_product_by_ref(ref) is not None

    def search_products_by_name(self, name: str, limit: int = 10) -> list[dict]:
        """Search for products by name (useful as fallback if SKU lookup fails)"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/products",
                params={
                    'limit': limit,
                    'sqlfilters': f"t.label like '%{_escape_sql_string(name)}%'"  # FIXED: SQL injection prevention
                },
                timeout=30
            )
            if response.status_code == 200:
                try:
                    results = response.json()
                    if isinstance(results, list):
                        return results
                    elif isinstance(results, dict):
                        # Some versions return {"data": [...]}
                        return results.get("data", [])
                except ValueError as json_err:
                    logger.error(f"Failed to parse JSON response for search_products_by_name: {json_err}")
                    return []
            # MEDIUM #13: Log non-200 responses
            logger.warning(f"search_products_by_name({name}) failed with status {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error searching products by name '{name}': {e}")
            return []

    def get_products_by_refs_batch(self, refs: list[str]) -> dict[str, dict]:
        """Get multiple products by reference in batch - returns dict of ref -> product"""
        result = {}
        for ref in refs:
            product = self.get_product_by_ref(ref)
            if product:
                result[ref] = product
        return result

    def create_product(self, product_data: dict) -> dict:
        """Create a new product in Dolibarr with full data including purchase price"""
        try:
            # Build description (combine short and long)
            description = product_data.get("long_description") or product_data.get("description", "")
            if product_data.get("short_description"):
                description = f"{product_data['short_description']}\n\n{description}"

            # Separate sale price from cost price
            sale_price = product_data.get("price", 0)  # This is the sale price
            cost_price = product_data.get("cost_price", 0)  # This is the purchase price

            payload = {
                "ref": product_data.get("sku", ""),
                "label": product_data.get("name", ""),
                "description": description,
                "price": sale_price,  # Sale price to customers
                "price_base_type": "HT",  # Price without tax
                "cost_price": cost_price,  # Purchase/cost price from supplier
                "status": 1,  # On sale
                "status_buy": 1,  # On purchase
                "type": 0,  # Product (not service)
                "barcode": product_data.get("ean", ""),
                "weight": product_data.get("weight", 0),
                # Note: stock_reel cannot be set directly, must use stock movements
            }

            # Add brand and supplier info as note
            notes = []
            if product_data.get("brand"):
                notes.append(f"Marca: {product_data['brand']}")
            if product_data.get("supplier_name"):
                notes.append(f"Proveedor: {product_data['supplier_name']}")
            if notes:
                payload["note_public"] = "\n".join(notes)

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/products",
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                product_id = response.json()

                # Upload image if available
                if product_data.get("image_url"):
                    self.upload_product_image(product_id, product_data["image_url"])

                # Set initial stock using stock movement
                stock = product_data.get("stock", 0)
                if stock > 0:
                    stock_result = self.update_stock(product_id, stock)
                    logger.info(f"Initial stock set for product {product_id}: {stock_result}")

                return {"status": "success", "product_id": product_id, "message": "Producto creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def update_product(self, product_id: int, product_data: dict) -> dict:
        """Update an existing product with full data including purchase price"""
        try:
            payload = {}

            if "name" in product_data:
                payload["label"] = product_data["name"]

            # Build description
            if "description" in product_data or "long_description" in product_data or "short_description" in product_data:
                description = product_data.get("long_description") or product_data.get("description", "")
                if product_data.get("short_description"):
                    description = f"{product_data['short_description']}\n\n{description}"
                payload["description"] = description

            if "price" in product_data:
                payload["price"] = product_data["price"]

            # Update cost/purchase price
            if "cost_price" in product_data:
                payload["cost_price"] = product_data["cost_price"]

            # Note: stock cannot be set directly via PUT, must use stock movements
            # Stock is updated separately via update_stock() method

            if "ean" in product_data:
                payload["barcode"] = product_data["ean"]
            if "weight" in product_data:
                payload["weight"] = product_data["weight"]

            # Build notes with brand and supplier
            notes = []
            if product_data.get("brand"):
                notes.append(f"Marca: {product_data['brand']}")
            if product_data.get("supplier_name"):
                notes.append(f"Proveedor: {product_data['supplier_name']}")
            if notes:
                payload["note_public"] = "\n".join(notes)

            response = self._rate_limited_request(
                'PUT',
                f"{self.base_url}/products/{product_id}",
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                # Update image if provided (handled separately for better error handling)
                return {"status": "success", "message": "Producto actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def upload_product_image(self, product_id: int, image_url: str, base_url: str = None) -> dict:
        """Upload image to a Dolibarr product

        Args:
            product_id: Dolibarr product ID
            image_url: URL of the image (can be relative like /api/uploads/... or full HTTP URL)
            base_url: Base URL for relative paths (e.g., https://app.example.com)
        """
        try:
            # Skip if no image URL
            if not image_url:
                return {"status": "skip", "message": "No image URL provided"}

            # Handle relative URLs (local uploads)
            if image_url.startswith('/api/') or image_url.startswith('/'):
                # This is a local relative URL - skip for now as we can't access it from here
                logger.info(f"Skipping local image URL: {image_url[:50]}...")
                return {"status": "skip", "message": "Local image URL - skipped"}

            # Validate it's a proper HTTP/HTTPS URL and not pointing to internal network (SSRF)
            if not image_url.startswith(('http://', 'https://')):
                return {"status": "skip", "message": "Invalid image URL format"}
            try:
                _validate_crm_url(image_url)  # Reuse SSRF guard: blocks private IPs
            except ValueError as _ve:
                logger.warning(f"SSRF blocked for image_url: {image_url[:80]!r} — {_ve}")
                return {"status": "skip", "message": "Image URL no permitida (SSRF)"}

            # Download image with user agent and strict size limit (10 MB)
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CatalogSync/1.0)"}
            img_response = requests.get(image_url, timeout=15, headers=headers, stream=True)
            try:
                # Check Content-Length BEFORE consuming response body
                content_length = int(img_response.headers.get("Content-Length", 0))
                if content_length > 10 * 1024 * 1024:
                    logger.warning(f"Image too large: {content_length} > 10MB - skipping")
                    return {"status": "skip", "message": "Imagen demasiado grande (>10 MB)"}

                # Validate status code
                if img_response.status_code != 200:
                    logger.warning(f"Failed to download image: {img_response.status_code}")
                    return {"status": "error", "message": f"No se pudo descargar la imagen: {img_response.status_code}"}

                # Encode to base64 - reuse the streamed response (no second download!)
                img_base64 = base64.b64encode(img_response.content).decode('utf-8')
            finally:
                # CRITICAL: Always close the response to prevent resource leak
                img_response.close()

            # Determine file extension from content type or URL
            content_type = img_response.headers.get('content-type', 'image/jpeg')
            if 'png' in content_type or image_url.lower().endswith('.png'):
                ext = 'png'
            elif 'gif' in content_type or image_url.lower().endswith('.gif'):
                ext = 'gif'
            elif 'webp' in content_type or image_url.lower().endswith('.webp'):
                ext = 'webp'
            else:
                ext = 'jpg'

            # Get product ref for the subdir
            product = self.get_product_by_id(product_id)
            product_ref = product.get('ref', str(product_id)) if product else str(product_id)

            # Upload to Dolibarr
            payload = {
                "filename": f"product_{product_id}.{ext}",
                "modulepart": "product",
                "ref": product_ref,
                "subdir": "",
                "filecontent": img_base64,
                "fileencoding": "base64",
                "overwriteifexists": 1
            }

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/documents/upload",
                json=payload,
                timeout=60
            )

            if response.status_code in [200, 201]:
                logger.info(f"Successfully uploaded image for product {product_id}")
                return {"status": "success", "message": "Imagen subida"}
            else:
                logger.warning(f"Dolibarr image upload failed: {response.status_code} - {response.text[:100]}")
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.Timeout:
            logger.error(f"Timeout downloading image from {image_url[:50]}...")
            return {"status": "error", "message": "Timeout descargando imagen"}
        except Exception as e:
            logger.error(f"Dolibarr upload_product_image error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def _get_warehouse_stock(self, product_id: int, warehouse_id: int) -> int | None:
        """
        Get the REAL stock of a product in a specific warehouse using the stock endpoint.
        This is more reliable than stock_reel from GET /products/{id} which can be stale/null.

        CRITICAL: Only returns stock for the SPECIFIC warehouse, not a sum of all warehouses.
        This prevents stock accumulation bugs.
        """
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/products/{product_id}/stock",
                timeout=30
            )
            if response.status_code == 200:
                stock_data = response.json()

                if isinstance(stock_data, dict):
                    # Get stock for the SPECIFIC warehouse only
                    warehouses = stock_data.get("stock_warehouses") or stock_data.get("stock_warehouse") or {}

                    # Dolibarr returns warehouse IDs as string keys
                    wh_key = str(warehouse_id)
                    if wh_key in warehouses:
                        wh_stock = warehouses[wh_key]
                        real_stock = wh_stock.get("real") if isinstance(wh_stock, dict) else wh_stock
                        if real_stock is not None:
                            result = int(float(real_stock))
                            logger.debug(f"[STOCK] Warehouse {warehouse_id} stock for product {product_id}: {result}")
                            return result

                    # CRITICAL FIX: Don't sum all warehouses - that causes accumulation!
                    # Instead, if the specific warehouse isn't found, return None to trigger fallback
                    logger.warning(
                        f"[STOCK] Warehouse {warehouse_id} not found in stock response for product {product_id}. "
                        f"Available warehouses: {list(warehouses.keys())}"
                    )
                    return None

            logger.debug(f"[STOCK] Could not get warehouse {warehouse_id} stock for product {product_id}, response: {response.status_code}")
            return None

        except Exception as e:
            logger.warning(f"[STOCK] Error getting warehouse stock for product {product_id}: {e}")
            return None

    def update_stock(self, product_id: int, stock: int, warehouse_id: int = None) -> dict:
        """Update product stock in Dolibarr using absolute stock value.

        IMPORTANT: This method sets stock to an absolute value by calculating
        the difference with current stock. To avoid accumulation bugs, it uses
        multiple methods to determine the REAL current stock before creating
        any stock movement.

        CRITICAL FIX: Only ever creates ONE movement per call, never sums across warehouses.
        """
        try:
            # Validate input
            if stock < 0:
                logger.error(f"[STOCK] Cannot set negative stock: {stock}")
                return {"status": "error", "message": "El stock no puede ser negativo"}

            # First get or create a warehouse
            if warehouse_id is None:
                warehouse_id = self.get_or_create_default_warehouse()
                if not warehouse_id:
                    logger.warning("[STOCK] No warehouse available, cannot update stock")
                    return {"status": "warning", "message": "No hay almacén configurado en Dolibarr"}

            logger.info(f"[STOCK] Starting stock update: product={product_id}, warehouse={warehouse_id}, desired_stock={stock}")

            # === CRITICAL: Get current stock reliably ===
            # Method 1: Use the dedicated stock endpoint (most reliable)
            current_stock = self._get_warehouse_stock(product_id, warehouse_id)

            # Method 2: Fallback to product's stock_reel field (ONLY if Method 1 fails)
            if current_stock is None:
                logger.debug(f"[STOCK] Falling back to stock_reel for product {product_id}")
                product = self.get_product_by_id(product_id)
                if not product:
                    return {"status": "error", "message": "Producto no encontrado"}

                stock_reel = product.get("stock_reel")

                # For NEW products, stock_reel might be null/empty - in that case, assume current_stock = 0
                if stock_reel is None or stock_reel == "" or stock_reel == "null":
                    logger.info(
                        f"[STOCK] Product {product_id}: stock_reel is null/empty. "
                        f"Assuming current stock = 0 for new product. "
                        f"Desired stock: {stock}"
                    )
                    current_stock = 0
                else:
                    try:
                        current_stock = int(float(stock_reel))
                        logger.info(f"[STOCK] Product {product_id}: using stock_reel={current_stock} (fallback)")
                    except (ValueError, TypeError):
                        logger.error(f"[STOCK] Invalid stock_reel value: {stock_reel}")
                        return {"status": "error", "message": "Valor de stock inválido en Dolibarr"}

            # Calculate difference
            diff = stock - current_stock

            if diff == 0:
                logger.info(f"[STOCK] Product {product_id}: stock unchanged ({current_stock})")
                return {"status": "success", "message": "Stock sin cambios"}

            # SAFETY: Log detailed info for debugging stock issues
            logger.info(
                f"[STOCK] Product {product_id}: "
                f"current={current_stock}, desired={stock}, diff={diff}, "
                f"movement={'ENTRADA' if diff > 0 else 'SALIDA'}"
            )

            # === CREATE STOCK MOVEMENT ===
            # This is the ONLY place where stock is updated for this product/warehouse
            payload = {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "qty": abs(diff),
                "type": 0 if diff > 0 else 1,  # 0 = entrada (entrada de stock), 1 = salida (salida de stock)
                "label": f"SyncStock: {current_stock} → {stock}",
                "date": datetime.now(UTC).isoformat()
            }

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/stockmovements",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                logger.info(f"[STOCK] Movement created successfully for product {product_id}: {current_stock} → {stock}")

                # VERIFICATION: After creating movement, verify the new stock
                new_stock = self._get_warehouse_stock(product_id, warehouse_id)
                if new_stock is not None:
                    if new_stock == stock:
                        logger.info(f"[STOCK] Verification OK: product {product_id} stock is now {new_stock}")
                    else:
                        logger.warning(
                            f"[STOCK] Verification FAILED for product {product_id}: "
                            f"expected={stock}, actual={new_stock}, diff={new_stock - stock}"
                        )
                        return {
                            "status": "warning",
                            "message": f"Movimiento creado pero stock verificación falló: esperado {stock}, actual {new_stock}"
                        }

                return {"status": "success", "message": f"Stock actualizado: {current_stock} → {stock}"}
            else:
                error_msg = response.text[:200] if response.text else f"HTTP {response.status_code}"
                logger.error(f"[STOCK] Stock movement failed for product {product_id}: {error_msg}")
                return {"status": "error", "message": f"Error al crear movimiento de stock: {error_msg}"}

        except Exception as e:
            logger.error(f"[STOCK] update_stock error for product {product_id}: {e}", exc_info=True)
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def get_warehouses(self) -> list[dict]:
        """Get all warehouses from Dolibarr"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/warehouses",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Dolibarr get_warehouses error: {e}")
            return []

    def create_warehouse(self, label: str, location: str = "") -> int | None:
        """Create a warehouse in Dolibarr"""
        try:
            payload = {
                "label": label,
                "lieu": location,
                "statut": 1  # Active
            }
            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/warehouses",
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                warehouse_id = response.json()
                logger.info(f"Created warehouse '{label}' with ID {warehouse_id}")
                return warehouse_id
            else:
                logger.warning(f"Failed to create warehouse: {response.status_code} - {response.text[:100]}")
                return None
        except Exception as e:
            logger.error(f"create_warehouse error: {e}")
            return None

    def get_or_create_default_warehouse(self) -> int | None:
        """Get the first warehouse or create a default one"""
        warehouses = self.get_warehouses()
        if warehouses:
            return int(warehouses[0].get("id"))

        # No warehouses exist, create one
        logger.info("No warehouses found, creating default warehouse...")
        return self.create_warehouse("Almacén Principal", "Almacén predeterminado")

    def get_product_by_id(self, product_id: int) -> dict | None:
        """Get product by ID"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/products/{product_id}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Dolibarr get_product_by_id error: {e}")
            return None

    # ==================== SUPPLIERS (Third Parties) ====================

    def get_thirdparties(self, limit: int = 500, thirdparty_type: str = None) -> list[dict]:
        """Get third parties (clients/suppliers) from Dolibarr
        thirdparty_type: 'supplier' or 'customer' or None for all
        """
        try:
            params = {'limit': limit}
            if thirdparty_type == 'supplier':
                params['mode'] = 4  # Suppliers only
            elif thirdparty_type == 'customer':
                params['mode'] = 1  # Customers only

            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/thirdparties",
                params=params,
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Dolibarr get_thirdparties returned {response.status_code}: {response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"Dolibarr get_thirdparties error: {e}")
            return []

    def get_suppliers(self, limit: int = 500) -> list[dict]:
        """Get suppliers from Dolibarr"""
        return self.get_thirdparties(limit=limit, thirdparty_type='supplier')

    def create_supplier(self, supplier_data: dict) -> dict:
        """Create a supplier in Dolibarr"""
        try:
            name = supplier_data.get("name", "").strip()
            if not name:
                return {"status": "error", "message": "Nombre de proveedor vacío"}

            payload = {
                "name": name,
                "name_alias": supplier_data.get("alias", ""),
                "email": supplier_data.get("email", ""),
                "phone": supplier_data.get("phone", ""),
                "address": supplier_data.get("address", ""),
                "zip": supplier_data.get("zip", ""),
                "town": supplier_data.get("city", ""),
                "country_code": supplier_data.get("country_code", "ES"),
                "fournisseur": 1,  # Mark as supplier
                "client": 0,  # Not a client
                "note_public": supplier_data.get("notes", ""),
                "status": 1  # Active
            }
            # Only include supplier_code if explicitly provided and non-empty
            supplier_code = supplier_data.get("supplier_code", "")
            if supplier_code:
                payload["code_fournisseur"] = supplier_code

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/thirdparties",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                supplier_id = response.json()
                return {"status": "success", "supplier_id": supplier_id, "message": "Proveedor creado"}
            else:
                error_detail = response.text[:300]
                logger.error(f"Dolibarr create_supplier failed for '{name}': {response.status_code} - {error_detail}")
                return {"status": "error", "message": f"Error: {response.status_code} - {error_detail}"}
        except Exception as e:
            logger.error(f"Dolibarr create_supplier exception for '{supplier_data.get('name', '')}': {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def update_supplier(self, supplier_id: int, supplier_data: dict) -> dict:
        """Update a supplier in Dolibarr"""
        try:
            payload = {}
            if "name" in supplier_data:
                payload["name"] = supplier_data["name"]
            if "email" in supplier_data:
                payload["email"] = supplier_data["email"]
            if "phone" in supplier_data:
                payload["phone"] = supplier_data["phone"]
            if "address" in supplier_data:
                payload["address"] = supplier_data["address"]

            response = self._rate_limited_request(
                'PUT',
                f"{self.base_url}/thirdparties/{supplier_id}",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return {"status": "success", "message": "Proveedor actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def get_supplier_by_name(self, name: str) -> dict | None:
        """Find supplier by name using direct API search"""
        if not name or not name.strip():
            return None
        try:
            # First try to get suppliers and search
            suppliers = self.get_suppliers(limit=500)
            for s in suppliers:
                if s.get("name", "").lower() == name.strip().lower():
                    return s

            # If not found in list, try direct search with SQL filter
            try:
                response = self._rate_limited_request(
                    'GET',
                    f"{self.base_url}/thirdparties",
                    params={'sqlfilters': f"(t.nom:=:'{_escape_sql_string(name)}')"},  # FIXED: SQL injection prevention
                    timeout=30
                )
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        return results[0]
            except Exception:
                pass

            return None
        except Exception as e:
            logger.error(f"Dolibarr get_supplier_by_name error: {e}")
            return None

    def link_product_to_supplier(self, product_ref: str, supplier_id: int, purchase_price: float, supplier_ref: str = None) -> dict:
        """Link a product to a supplier with purchase price in Dolibarr using purchase_prices API"""
        try:
            # First get the product by reference
            product = self.get_product_by_ref(product_ref)
            if not product:
                return {"status": "error", "message": f"Producto no encontrado: {product_ref}"}

            product_id = product.get("id")

            # Create supplier price entry using correct Dolibarr API parameters
            # According to Dolibarr API: POST /products/{id}/purchase_prices
            payload = {
                "fourn_id": supplier_id,           # Supplier ID
                "buyprice": purchase_price,         # Purchase price
                "qty": 1,                           # Minimum quantity
                "price_base_type": "HT",            # Price without tax
                "ref_fourn": supplier_ref or product_ref,  # Supplier's reference for this product
                "tva_tx": 0,                        # VAT rate
                "charges": 0,                       # Additional charges
                "availability": 1                   # Availability delay code (required by Dolibarr)
            }

            logger.info(f"Linking product {product_id} to supplier {supplier_id} with price {purchase_price}")

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/products/{product_id}/purchase_prices",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                logger.info(f"Successfully linked product {product_ref} to supplier {supplier_id}")
                return {"status": "success", "message": "Producto vinculado a proveedor"}
            elif response.status_code == 409:
                # Already exists
                logger.info(f"Product {product_ref} already linked to supplier {supplier_id}")
                return {"status": "success", "message": "Vínculo ya existe"}
            else:
                logger.warning(f"Failed to link product to supplier: {response.status_code} - {response.text[:200]}")
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:100]}"}
        except Exception as e:
            logger.error(f"Dolibarr link_product_to_supplier error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    # ==================== ORDERS ====================

    def get_orders(self, limit: int = 100) -> list[dict]:
        """Get customer orders from Dolibarr"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/orders",
                params={'limit': limit, 'sortfield': 'rowid', 'sortorder': 'DESC'},
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Dolibarr get_orders error: {e}")
            return []

    def search_orders_by_external_id(self, external_id: str) -> list[dict]:
        """Search for orders by external_id (ref_client field)

        HIGH #10: Check if order already exists in CRM to prevent duplicates
        """
        try:
            # ref_client is used to store external order IDs
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/orders",
                params={
                    'sqlfilters': f"t.ref_client = '{_escape_sql_string(external_id)}'",
                    'limit': 10
                },
                timeout=30
            )
            if response.status_code == 200:
                results = response.json()
                if isinstance(results, list):
                    return results
                elif isinstance(results, dict):
                    return results.get("data", [])
            logger.debug(f"search_orders_by_external_id({external_id}): no results or error {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error searching orders by external_id {external_id}: {e}")
            return []

    def get_supplier_orders(self, limit: int = 100) -> list[dict]:
        """Get supplier orders from Dolibarr"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/supplierorders",
                params={'limit': limit, 'sortfield': 'rowid', 'sortorder': 'DESC'},
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Dolibarr get_supplier_orders error: {e}")
            return []

    def create_order(self, order_data: dict) -> dict:
        """Create a customer order in Dolibarr"""
        try:
            payload = {
                "socid": order_data.get("customer_id"),
                "date": order_data.get("date", datetime.now(UTC).strftime("%Y-%m-%d")),
                "ref_client": order_data.get("external_ref", ""),
                "note_public": order_data.get("notes", ""),
                "lines": []
            }

            # Add order lines
            for line in order_data.get("lines", []):
                payload["lines"].append({
                    "fk_product": line.get("product_id"),
                    "qty": line.get("quantity", 1),
                    "subprice": line.get("price", 0),
                    "tva_tx": line.get("tax_rate", 21),
                    "desc": line.get("description", "")
                })

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/orders",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                order_id = response.json()
                return {"status": "success", "order_id": order_id, "message": "Pedido creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def create_supplier_order(self, order_data: dict) -> dict:
        """Create a supplier order in Dolibarr"""
        try:
            payload = {
                "socid": order_data.get("supplier_id"),
                "date": order_data.get("date", datetime.now(UTC).strftime("%Y-%m-%d")),
                "ref_supplier": order_data.get("external_ref", ""),
                "note_public": order_data.get("notes", ""),
                "lines": []
            }

            for line in order_data.get("lines", []):
                payload["lines"].append({
                    "fk_product": line.get("product_id"),
                    "qty": line.get("quantity", 1),
                    "subprice": line.get("price", 0),
                    "tva_tx": line.get("tax_rate", 21)
                })

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/supplierorders",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                order_id = response.json()
                return {"status": "success", "order_id": order_id, "message": "Pedido a proveedor creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    # ==================== STATS ====================

    def get_stats(self) -> dict:
        """Get basic stats from Dolibarr"""
        try:
            products_count = len(self.get_products(limit=10000))
            suppliers = self.get_thirdparties(limit=10000)
            suppliers_count = len([t for t in suppliers if t.get('fournisseur') == '1'])
            clients_count = len([t for t in suppliers if t.get('client') == '1'])
            orders_count = len(self.get_orders(limit=10000))

            return {
                "products": products_count,
                "suppliers": suppliers_count,
                "clients": clients_count,
                "orders": orders_count
            }
        except Exception as e:
            logger.error(f"Dolibarr get_stats error: {e}")
            return {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}

    # ==================== ASYNC METHODS (FASE 2) ====================

    async def create_product_async(self, product_data: dict) -> dict:
        """Async wrapper for create_product - runs in thread pool to avoid blocking"""
        loop = asyncio.get_running_loop()  # FIXED: Use get_running_loop() instead of deprecated get_event_loop()
        return await loop.run_in_executor(None, self.create_product, product_data)

    async def update_product_async(self, product_id: int, product_data: dict) -> dict:
        """Async wrapper for update_product - runs in thread pool to avoid blocking"""
        loop = asyncio.get_running_loop()  # FIXED: Use get_running_loop() instead of deprecated get_event_loop()
        return await loop.run_in_executor(None, self.update_product, product_id, product_data)

    async def update_stock_async(self, product_id: int, stock_value: int) -> dict:
        """Async wrapper for update_stock - runs in thread pool to avoid blocking"""
        loop = asyncio.get_running_loop()  # FIXED: Use get_running_loop() instead of deprecated get_event_loop()
        return await loop.run_in_executor(None, self.update_stock, product_id, stock_value)

    async def upload_product_image_async(self, product_id: int, image_url: str) -> dict:
        """Async wrapper for upload_product_image - runs in thread pool to avoid blocking"""
        loop = asyncio.get_running_loop()  # FIXED: Use get_running_loop() instead of deprecated get_event_loop()
        return await loop.run_in_executor(None, self.upload_product_image, product_id, image_url)
