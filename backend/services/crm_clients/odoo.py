"""
Odoo ERP/CRM API Client.
"""
import logging
import requests
import base64
import asyncio
from typing import Dict, List, Optional

from .base import _validate_crm_url

logger = logging.getLogger(__name__)


class OdooClient:
    """Odoo 17 ERP/CRM API Client - Using REST API with token authentication"""

    def __init__(self, api_url: str, api_token: str):
        """Initialize Odoo client

        Args:
            api_url: Base URL of Odoo instance (e.g., https://odoo.example.com)
            api_token: API token for authentication
        """
        self.base_url = _validate_crm_url(api_url).rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
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
        # Rate limiting
        self.min_delay = 0.1  # 100ms between requests
        self.last_request_time = 0

    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make a rate-limited request"""
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)

        kwargs.setdefault('timeout', 30)
        response = self.session.request(method, url, **kwargs)
        self.last_request_time = time.time()
        return response

    def close(self):
        """Close the session"""
        self.session.close()

    def test_connection(self) -> Dict:
        """Test API connection to Odoo"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/ir.config_parameter/search_read",
                params={'domain': [['key', '=', 'web.base.url']], 'fields': []},
                timeout=30
            )
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Conexión exitosa a Odoo",
                    "version": "Odoo 17"
                }
            elif response.status_code == 401:
                return {"status": "error", "message": "API Token inválido"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Acceso denegado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar al servidor. Verifica la URL."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"CRM connection error: {e}")
            return {"status": "error", "message": "Error de conexión al servidor CRM. Verifica la URL y las credenciales."}

    # ==================== PRODUCTS ====================

    def get_products(self, limit: int = 500) -> List[Dict]:
        """Get products from Odoo"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/product.product/search_read",
                params={
                    'domain': [['sale_ok', '=', True]],
                    'fields': ['id', 'name', 'default_code', 'barcode', 'list_price', 'standard_price', 'description_sale', 'image_1920', 'qty_available'],
                    'limit': limit
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Odoo get_products error: {e}")
            return []

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Get a product by SKU (default_code)"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/product.product/search_read",
                params={
                    'domain': [['default_code', '=', sku]],
                    'fields': ['id', 'name', 'default_code', 'barcode', 'list_price', 'standard_price', 'qty_available'],
                    'limit': 1
                },
                timeout=30
            )
            if response.status_code == 200:
                results = response.json()
                return results[0] if results else None
            return None
        except Exception as e:
            logger.error(f"Odoo get_product_by_sku error: {e}")
            return None

    def get_products_by_skus_batch(self, skus: List[str]) -> Dict[str, Dict]:
        """Get multiple products by SKU in batch - returns dict of sku -> product"""
        result = {}
        for sku in skus:
            product = self.get_product_by_sku(sku)
            if product:
                result[sku] = product
        return result

    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product in Odoo"""
        try:
            # Prepare product data for Odoo
            name = product_data.get("name", "")
            sku = product_data.get("sku", "")

            payload = {
                "name": name,
                "default_code": sku,
                "barcode": product_data.get("ean", ""),
                "list_price": float(product_data.get("price", 0)),
                "standard_price": float(product_data.get("cost_price", 0)),
                "description_sale": product_data.get("description") or "",
                "sale_ok": True,
                "purchase_ok": True,
                "type": "product",  # Stored product
            }

            # Add image if available
            if product_data.get("image_url"):
                try:
                    img_response = requests.get(product_data["image_url"], timeout=10, stream=True)
                    try:
                        # FIXED: Check Content-Length BEFORE downloading to prevent DoS
                        content_length = int(img_response.headers.get("Content-Length", 0))
                        MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB limit

                        if content_length > MAX_IMAGE_SIZE:
                            logger.warning(f"Image too large: {content_length} > {MAX_IMAGE_SIZE}")
                        elif img_response.status_code == 200:
                            img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                            payload["image_1920"] = img_base64
                    finally:
                        img_response.close()  # FIXED: Always close to prevent resource leak
                except Exception as img_err:
                    logger.warning(f"Failed to download product image: {img_err}")

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/api/product.product",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                result = response.json()
                product_id = result.get("id") if isinstance(result, dict) else result
                return {
                    "status": "success",
                    "product_id": product_id,
                    "message": "Producto creado"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Error: {response.status_code} - {response.text[:200]}"
                }
        except Exception as e:
            logger.error(f"Odoo create_product error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """Update an existing product in Odoo"""
        try:
            payload = {}

            if "name" in product_data:
                payload["name"] = product_data["name"]
            if "sku" in product_data:
                payload["default_code"] = product_data["sku"]
            if "ean" in product_data:
                payload["barcode"] = product_data["ean"]
            if "price" in product_data:
                payload["list_price"] = float(product_data["price"])
            if "cost_price" in product_data:
                payload["standard_price"] = float(product_data["cost_price"])
            if "description" in product_data:
                payload["description_sale"] = product_data["description"]

            response = self._rate_limited_request(
                'PUT',
                f"{self.base_url}/api/product.product/{product_id}",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return {"status": "success", "message": "Producto actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Odoo update_product error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def update_stock(self, product_id: int, stock: int, warehouse_id: int = None) -> Dict:
        """Update product stock in Odoo"""
        try:
            # Get or use default warehouse
            if warehouse_id is None:
                warehouse_id = self.get_or_create_default_warehouse()
                if not warehouse_id:
                    return {"status": "warning", "message": "No hay almacén configurado en Odoo"}

            # Get current stock
            product = self.get_product_by_id(product_id)
            if not product:
                return {"status": "error", "message": "Producto no encontrado"}

            current_stock = int(float(product.get("qty_available", 0)))
            diff = stock - current_stock

            if diff == 0:
                return {"status": "success", "message": "Stock sin cambios"}

            # Create stock movement
            move_type = "in_refund" if diff > 0 else "out_refund"

            payload = {
                "product_id": product_id,
                "product_qty": abs(diff),
                "location_id": warehouse_id,
                "location_dest_id": warehouse_id,
            }

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/api/stock.move",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                logger.info(f"Stock updated: {current_stock} → {stock}")
                return {"status": "success", "message": f"Stock actualizado: {current_stock} → {stock}"}
            else:
                return {"status": "warning", "message": f"No se pudo actualizar stock: {response.text[:100]}"}
        except Exception as e:
            logger.error(f"Odoo update_stock error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def get_or_create_default_warehouse(self) -> Optional[int]:
        """Get the first warehouse or create a default one"""
        try:
            warehouses = self.get_warehouses()
            if warehouses:
                return warehouses[0].get("id")

            # Create default warehouse
            payload = {
                "name": "Almacén Principal",
                "code": "MAIN",
                "company_id": 1,  # Default company
            }
            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/api/stock.warehouse",
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                result = response.json()
                return result.get("id") if isinstance(result, dict) else result
            return None
        except Exception as e:
            logger.error(f"Odoo get_or_create_default_warehouse error: {e}")
            return None

    def get_warehouses(self) -> List[Dict]:
        """Get all warehouses from Odoo"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/stock.warehouse/search_read",
                params={'fields': ['id', 'name', 'code']},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Odoo get_warehouses error: {e}")
            return []

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get product by ID"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/product.product/{product_id}",
                params={'fields': ['id', 'name', 'qty_available', 'list_price']},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Odoo get_product_by_id error: {e}")
            return None

    # ==================== SUPPLIERS (Partners) ====================

    def get_suppliers(self, limit: int = 500) -> List[Dict]:
        """Get suppliers (vendors) from Odoo"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/res.partner/search_read",
                params={
                    'domain': [['supplier_rank', '>', 0]],
                    'fields': ['id', 'name', 'email', 'phone', 'street', 'city', 'country_id'],
                    'limit': limit
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Odoo get_suppliers error: {e}")
            return []

    def create_supplier(self, supplier_data: Dict) -> Dict:
        """Create a supplier in Odoo"""
        try:
            payload = {
                "name": supplier_data.get("name", ""),
                "email": supplier_data.get("email", ""),
                "phone": supplier_data.get("phone", ""),
                "street": supplier_data.get("address", ""),
                "city": supplier_data.get("city", ""),
                "supplier_rank": 1,  # Mark as supplier
                "customer_rank": 0,  # Not a customer
            }

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/api/res.partner",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                result = response.json()
                supplier_id = result.get("id") if isinstance(result, dict) else result
                return {
                    "status": "success",
                    "supplier_id": supplier_id,
                    "message": "Proveedor creado"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Error: {response.status_code} - {response.text[:200]}"
                }
        except Exception as e:
            logger.error(f"Odoo create_supplier error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def update_supplier(self, supplier_id: int, supplier_data: Dict) -> Dict:
        """Update a supplier in Odoo"""
        try:
            payload = {}
            if "name" in supplier_data:
                payload["name"] = supplier_data["name"]
            if "email" in supplier_data:
                payload["email"] = supplier_data["email"]
            if "phone" in supplier_data:
                payload["phone"] = supplier_data["phone"]
            if "address" in supplier_data:
                payload["street"] = supplier_data["address"]
            if "city" in supplier_data:
                payload["city"] = supplier_data["city"]

            response = self._rate_limited_request(
                'PUT',
                f"{self.base_url}/api/res.partner/{supplier_id}",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return {"status": "success", "message": "Proveedor actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Odoo update_supplier error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    def link_product_to_supplier(self, product_sku: str, supplier_id: int, purchase_price: float, supplier_sku: str = None) -> Dict:
        """Link a product to a supplier with purchase price in Odoo"""
        try:
            # Get the product
            product = self.get_product_by_sku(product_sku)
            if not product:
                return {"status": "error", "message": f"Producto no encontrado: {product_sku}"}

            product_id = product.get("id")

            # Create vendor info
            payload = {
                "product_id": product_id,
                "partner_id": supplier_id,
                "price": purchase_price,
                "product_code": supplier_sku or product_sku,
                "product_name": product.get("name", ""),
            }

            logger.info(f"Linking product {product_sku} to supplier {supplier_id}")

            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/api/product.supplierinfo",
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                logger.info(f"Successfully linked product {product_sku} to supplier {supplier_id}")
                return {"status": "success", "message": "Producto vinculado a proveedor"}
            elif response.status_code == 409:
                return {"status": "success", "message": "Vínculo ya existe"}
            else:
                logger.warning(f"Failed to link product: {response.status_code} - {response.text[:200]}")
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            logger.error(f"Odoo link_product_to_supplier error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}

    # ==================== ORDERS ====================

    def get_orders(self, limit: int = 100) -> List[Dict]:
        """Get sales orders from Odoo"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/sale.order/search_read",
                params={
                    'domain': [['state', 'in', ['draft', 'sent', 'sale']]],
                    'fields': ['id', 'name', 'partner_id', 'amount_total', 'date_order', 'client_order_ref'],
                    'limit': limit,
                    'order': 'date_order desc'
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Odoo get_orders error: {e}")
            return []

    def search_orders_by_external_id(self, external_id: str) -> List[Dict]:
        """Search for orders by external_id (client_order_ref field)

        HIGH #10: Check if order already exists in CRM to prevent duplicates
        """
        try:
            # client_order_ref is used to store external order IDs
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/sale.order/search_read",
                params={
                    'domain': [['client_order_ref', '=', external_id]],
                    'fields': ['id', 'name', 'partner_id', 'amount_total', 'date_order', 'client_order_ref'],
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

    def get_purchase_orders(self, limit: int = 100) -> List[Dict]:
        """Get purchase orders from Odoo"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/api/purchase.order/search_read",
                params={
                    'domain': [['state', 'in', ['draft', 'sent', 'purchase']]],
                    'fields': ['id', 'name', 'partner_id', 'amount_total', 'date_order'],
                    'limit': limit,
                    'order': 'date_order desc'
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Odoo get_purchase_orders error: {e}")
            return []

    # ==================== STATS ====================

    def get_stats(self) -> Dict:
        """Get basic stats from Odoo"""
        try:
            products = self.get_products(limit=10000)
            suppliers = self.get_suppliers(limit=10000)
            orders = self.get_orders(limit=10000)
            purchase_orders = self.get_purchase_orders(limit=10000)

            return {
                "products": len(products) if isinstance(products, list) else 0,
                "suppliers": len(suppliers) if isinstance(suppliers, list) else 0,
                "clients": 0,  # Not standard in Odoo clients count
                "orders": len(orders) + len(purchase_orders) if isinstance(orders, list) and isinstance(purchase_orders, list) else 0
            }
        except Exception as e:
            logger.error(f"Odoo get_stats error: {e}")
            return {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}

    # ==================== ASYNC METHODS (FASE 2) ====================

    async def create_product_async(self, product_data: Dict) -> Dict:
        """Async wrapper for create_product - runs in thread pool to avoid blocking"""
        loop = asyncio.get_running_loop()  # FIXED: Use get_running_loop() instead of deprecated get_event_loop()
        return await loop.run_in_executor(None, self.create_product, product_data)

    async def update_product_async(self, product_id: int, product_data: Dict) -> Dict:
        """Async wrapper for update_product - runs in thread pool to avoid blocking"""
        loop = asyncio.get_running_loop()  # FIXED: Use get_running_loop() instead of deprecated get_event_loop()
        return await loop.run_in_executor(None, self.update_product, product_id, product_data)

    async def update_stock_async(self, product_id: int, stock_value: int) -> Dict:
        """Async wrapper for update_stock - runs in thread pool to avoid blocking"""
        loop = asyncio.get_running_loop()  # FIXED: Use get_running_loop() instead of deprecated get_event_loop()
        return await loop.run_in_executor(None, self.update_stock, product_id, stock_value)
