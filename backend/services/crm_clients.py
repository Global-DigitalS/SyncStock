"""
CRM Client implementations for all supported platforms.
Dolibarr, Odoo, HubSpot, Salesforce, Zoho, Pipedrive, Monday, Freshsales.
"""
import re
import logging
import requests
import base64
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

_PRIVATE_IP_RE = re.compile(
    r'^https?://(localhost|127\.|0\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)',
    re.IGNORECASE,
)
_VALID_URL_RE = re.compile(r'^https?://[a-zA-Z0-9._-]+(:\d+)?(/.*)?$')


def _validate_crm_url(url: str) -> str:
    """Validate a CRM API URL to prevent SSRF attacks."""
    url = url.strip()
    if not _VALID_URL_RE.match(url):
        raise ValueError(f"URL de CRM inválida: {url!r}")
    if _PRIVATE_IP_RE.match(url):
        raise ValueError("La URL de CRM no puede apuntar a direcciones IP privadas o localhost")
    return url


# ==================== DOLIBARR CLIENT ====================

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
        """Make a rate-limited request"""
        import time
        # Ensure minimum delay between requests
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
        """Test API connection"""
        try:
            response = self._rate_limited_request('GET', f"{self.base_url}/status", timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success", 
                    "message": "Conexión exitosa a Dolibarr",
                    "version": data.get("success", {}).get("dolibarr_version", "Unknown")
                }
            elif response.status_code == 401:
                return {"status": "error", "message": "API Key inválida"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Acceso denegado - verifica permisos del usuario API"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar al servidor. Verifica la URL."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"CRM connection error: {e}")
            return {"status": "error", "message": "Error de conexión al servidor CRM. Verifica la URL y las credenciales."}
    
    # ==================== PRODUCTS ====================
    
    def get_products(self, limit: int = 500) -> List[Dict]:
        """Get products from Dolibarr"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/products",
                params={'limit': limit, 'sortfield': 'rowid', 'sortorder': 'DESC'},
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Dolibarr get_products error: {e}")
            return []
    
    def get_product_by_ref(self, ref: str) -> Optional[Dict]:
        """Get a product by reference (SKU)"""
        try:
            response = self._rate_limited_request(
                'GET',
                f"{self.base_url}/products/ref/{ref}",
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Dolibarr get_product_by_ref error: {e}")
            return None
    
    def get_products_by_refs_batch(self, refs: List[str]) -> Dict[str, Dict]:
        """Get multiple products by reference in batch - returns dict of ref -> product"""
        result = {}
        for ref in refs:
            product = self.get_product_by_ref(ref)
            if product:
                result[ref] = product
        return result
    
    def create_product(self, product_data: Dict) -> Dict:
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
        except Exception as e:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
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
        except Exception as e:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}
    
    def upload_product_image(self, product_id: int, image_url: str, base_url: str = None) -> Dict:
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
            content_length = int(img_response.headers.get("Content-Length", 0))
            if content_length > 10 * 1024 * 1024:
                return {"status": "skip", "message": "Imagen demasiado grande (>10 MB)"}
            img_response = requests.get(image_url, timeout=15, headers=headers)
            if img_response.status_code != 200:
                logger.warning(f"Failed to download image: {img_response.status_code}")
                return {"status": "error", "message": f"No se pudo descargar la imagen: {img_response.status_code}"}
            
            # Encode to base64
            img_base64 = base64.b64encode(img_response.content).decode('utf-8')
            
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
    
    def update_stock(self, product_id: int, stock: int, warehouse_id: int = None) -> Dict:
        """Update product stock in Dolibarr"""
        try:
            # First get or create a warehouse
            if warehouse_id is None:
                warehouse_id = self.get_or_create_default_warehouse()
                if not warehouse_id:
                    logger.warning("No warehouse available, cannot update stock")
                    return {"status": "warning", "message": "No hay almacén configurado en Dolibarr"}
            
            # Get current stock
            product = self.get_product_by_id(product_id)
            if not product:
                return {"status": "error", "message": "Producto no encontrado"}
            
            current_stock = int(float(product.get("stock_reel") or 0))
            diff = stock - current_stock
            
            if diff == 0:
                return {"status": "success", "message": "Stock sin cambios"}
            
            # Dolibarr does not allow stock movements with qty = 0
            if abs(diff) == 0:
                return {"status": "success", "message": "Stock sin cambios"}
            
            # Create stock movement
            payload = {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "qty": abs(diff),
                "type": 0 if diff > 0 else 1,  # 0 = entrada, 1 = salida
                "label": "Sincronización desde catálogo"
            }
            
            logger.info(f"Creating stock movement for product {product_id}: {current_stock} -> {stock} (diff: {diff})")
            
            response = self._rate_limited_request(
                'POST',
                f"{self.base_url}/stockmovements",
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Stock updated successfully: {current_stock} → {stock}")
                return {"status": "success", "message": f"Stock actualizado: {current_stock} → {stock}"}
            else:
                logger.warning(f"Stock movement failed: {response.status_code} - {response.text[:200]}")
                # Fallback: try to update product directly (won't work if stock is managed)
                return {"status": "warning", "message": f"No se pudo crear movimiento: {response.text[:100]}"}
        except Exception as e:
            logger.error(f"update_stock error: {e}")
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}
    
    def get_warehouses(self) -> List[Dict]:
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
    
    def create_warehouse(self, label: str, location: str = "") -> Optional[int]:
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
    
    def get_or_create_default_warehouse(self) -> Optional[int]:
        """Get the first warehouse or create a default one"""
        warehouses = self.get_warehouses()
        if warehouses:
            return int(warehouses[0].get("id"))
        
        # No warehouses exist, create one
        logger.info("No warehouses found, creating default warehouse...")
        return self.create_warehouse("Almacén Principal", "Almacén predeterminado")
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
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
    
    def get_thirdparties(self, limit: int = 500, thirdparty_type: str = None) -> List[Dict]:
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
    
    def get_suppliers(self, limit: int = 500) -> List[Dict]:
        """Get suppliers from Dolibarr"""
        return self.get_thirdparties(limit=limit, thirdparty_type='supplier')
    
    def create_supplier(self, supplier_data: Dict) -> Dict:
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

    def update_supplier(self, supplier_id: int, supplier_data: Dict) -> Dict:
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
        except Exception as e:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}
    
    def get_supplier_by_name(self, name: str) -> Optional[Dict]:
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
                    params={'sqlfilters': f"(t.nom:=:'{name}')"},
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
    
    def link_product_to_supplier(self, product_ref: str, supplier_id: int, purchase_price: float, supplier_ref: str = None) -> Dict:
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
    
    def get_orders(self, limit: int = 100) -> List[Dict]:
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
    
    def get_supplier_orders(self, limit: int = 100) -> List[Dict]:
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
    
    def create_order(self, order_data: Dict) -> Dict:
        """Create a customer order in Dolibarr"""
        try:
            payload = {
                "socid": order_data.get("customer_id"),
                "date": order_data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
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
        except Exception as e:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}
    
    def create_supplier_order(self, order_data: Dict) -> Dict:
        """Create a supplier order in Dolibarr"""
        try:
            payload = {
                "socid": order_data.get("supplier_id"),
                "date": order_data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
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
        except Exception as e:
            return {"status": "error", "message": "Error en la operación CRM. Consulta los logs del servidor."}
    
    # ==================== STATS ====================
    
    def get_stats(self) -> Dict:
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


# ==================== ODOO CLIENT ====================

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
                    img_response = requests.get(product_data["image_url"], timeout=10)
                    if img_response.status_code == 200:
                        img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                        payload["image_1920"] = img_base64
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
            logger.error(f"Odoo get_orders error: {e}")
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


# ==================== HUBSPOT CLIENT ====================

class HubSpotClient:
    """HubSpot CRM API Client"""

    def __init__(self, api_token: str):
        self.base_url = "https://api.hubapi.com"
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
        self.session.mount('https://', adapter)
        self.min_delay = 0.1
        self.last_request_time = 0

    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        kwargs.setdefault('timeout', 30)
        response = self.session.request(method, url, **kwargs)
        self.last_request_time = time.time()
        return response

    def close(self):
        self.session.close()

    def test_connection(self) -> Dict:
        try:
            response = self._rate_limited_request('GET', f"{self.base_url}/crm/v3/objects/contacts", params={'limit': 1})
            if response.status_code == 200:
                return {"status": "success", "message": "Conexión exitosa a HubSpot"}
            elif response.status_code == 401:
                return {"status": "error", "message": "Token de acceso inválido"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Acceso denegado - verifica los scopes de la Private App"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar a HubSpot. Verifica tu conexión a internet."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"HubSpot connection error: {e}")
            return {"status": "error", "message": "Error de conexión a HubSpot."}

    def get_products(self, limit: int = 500) -> List[Dict]:
        try:
            products = []
            url = f"{self.base_url}/crm/v3/objects/line_items"
            params = {'limit': min(limit, 100), 'properties': 'name,hs_sku,price,quantity,description,hs_images'}
            while url and len(products) < limit:
                response = self._rate_limited_request('GET', url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    products.extend(data.get('results', []))
                    paging = data.get('paging', {}).get('next')
                    url = paging.get('link') if paging else None
                    params = None
                else:
                    break
            return products
        except Exception as e:
            logger.error(f"HubSpot get_products error: {e}")
            return []

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        try:
            response = self._rate_limited_request(
                'POST', f"{self.base_url}/crm/v3/objects/line_items/search",
                json={
                    'filterGroups': [{'filters': [{'propertyName': 'hs_sku', 'operator': 'EQ', 'value': sku}]}],
                    'properties': ['name', 'hs_sku', 'price', 'quantity', 'description'],
                    'limit': 1
                }
            )
            if response.status_code == 200:
                results = response.json().get('results', [])
                return results[0] if results else None
            return None
        except Exception as e:
            logger.error(f"HubSpot get_product_by_sku error: {e}")
            return None

    def create_product(self, product_data: Dict) -> Optional[Dict]:
        try:
            response = self._rate_limited_request(
                'POST', f"{self.base_url}/crm/v3/objects/products",
                json={'properties': product_data}
            )
            if response.status_code in [200, 201]:
                return response.json()
            logger.error(f"HubSpot create_product error: {response.status_code} - {response.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"HubSpot create_product error: {e}")
            return None

    def update_product(self, product_id: str, product_data: Dict) -> bool:
        try:
            response = self._rate_limited_request(
                'PATCH', f"{self.base_url}/crm/v3/objects/products/{product_id}",
                json={'properties': product_data}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HubSpot update_product error: {e}")
            return False

    def get_stats(self) -> Dict:
        stats = {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}
        try:
            for obj_type, stat_key in [('products', 'products'), ('contacts', 'suppliers'), ('companies', 'clients'), ('deals', 'orders')]:
                response = self._rate_limited_request('GET', f"{self.base_url}/crm/v3/objects/{obj_type}", params={'limit': 0})
                if response.status_code == 200:
                    stats[stat_key] = response.json().get('total', 0)
        except Exception as e:
            logger.error(f"HubSpot get_stats error: {e}")
        return stats


# ==================== SALESFORCE CLIENT ====================

class SalesforceClient:
    """Salesforce CRM API Client"""

    def __init__(self, api_url: str, client_id: str = "", client_secret: str = "", api_token: str = ""):
        self.base_url = _validate_crm_url(api_url).rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
        self.session.mount('https://', adapter)
        self.min_delay = 0.1
        self.last_request_time = 0

    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        kwargs.setdefault('timeout', 30)
        response = self.session.request(method, url, **kwargs)
        self.last_request_time = time.time()
        return response

    def close(self):
        self.session.close()

    def test_connection(self) -> Dict:
        try:
            response = self._rate_limited_request('GET', f"{self.base_url}/services/data/v59.0/sobjects")
            if response.status_code == 200:
                return {"status": "success", "message": "Conexión exitosa a Salesforce"}
            elif response.status_code == 401:
                return {"status": "error", "message": "Access Token inválido o expirado"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Acceso denegado - verifica permisos de la Connected App"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar a Salesforce. Verifica la URL."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Salesforce connection error: {e}")
            return {"status": "error", "message": "Error de conexión a Salesforce."}

    def get_products(self, limit: int = 500) -> List[Dict]:
        try:
            query = f"SELECT Id, Name, ProductCode, Description, IsActive FROM Product2 WHERE IsActive = true LIMIT {limit}"
            response = self._rate_limited_request('GET', f"{self.base_url}/services/data/v59.0/query", params={'q': query})
            if response.status_code == 200:
                return response.json().get('records', [])
            return []
        except Exception as e:
            logger.error(f"Salesforce get_products error: {e}")
            return []

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        try:
            query = f"SELECT Id, Name, ProductCode, Description FROM Product2 WHERE ProductCode = '{sku}' LIMIT 1"
            response = self._rate_limited_request('GET', f"{self.base_url}/services/data/v59.0/query", params={'q': query})
            if response.status_code == 200:
                records = response.json().get('records', [])
                return records[0] if records else None
            return None
        except Exception as e:
            logger.error(f"Salesforce get_product_by_sku error: {e}")
            return None

    def create_product(self, product_data: Dict) -> Optional[Dict]:
        try:
            response = self._rate_limited_request(
                'POST', f"{self.base_url}/services/data/v59.0/sobjects/Product2",
                json=product_data
            )
            if response.status_code in [200, 201]:
                return response.json()
            logger.error(f"Salesforce create_product: {response.status_code} - {response.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"Salesforce create_product error: {e}")
            return None

    def update_product(self, product_id: str, product_data: Dict) -> bool:
        try:
            response = self._rate_limited_request(
                'PATCH', f"{self.base_url}/services/data/v59.0/sobjects/Product2/{product_id}",
                json=product_data
            )
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Salesforce update_product error: {e}")
            return False

    def get_stats(self) -> Dict:
        stats = {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}
        try:
            queries = {
                'products': "SELECT COUNT() FROM Product2 WHERE IsActive = true",
                'suppliers': "SELECT COUNT() FROM Account WHERE Type = 'Vendor'",
                'clients': "SELECT COUNT() FROM Account WHERE Type = 'Customer'",
                'orders': "SELECT COUNT() FROM Opportunity WHERE IsClosed = false"
            }
            for key, query in queries.items():
                response = self._rate_limited_request('GET', f"{self.base_url}/services/data/v59.0/query", params={'q': query})
                if response.status_code == 200:
                    stats[key] = response.json().get('totalSize', 0)
        except Exception as e:
            logger.error(f"Salesforce get_stats error: {e}")
        return stats


# ==================== ZOHO CRM CLIENT ====================

class ZohoClient:
    """Zoho CRM API Client"""

    def __init__(self, api_url: str, client_id: str = "", client_secret: str = "", api_token: str = ""):
        self.base_url = _validate_crm_url(api_url).rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = api_token
        self.access_token = None
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
        self.session.mount('https://', adapter)
        self.min_delay = 0.1
        self.last_request_time = 0

    def _refresh_access_token(self) -> bool:
        try:
            # Determine accounts URL from API URL domain
            accounts_url = "https://accounts.zoho.eu"
            if "zohoapis.com" in self.base_url:
                accounts_url = "https://accounts.zoho.com"
            elif "zohoapis.in" in self.base_url:
                accounts_url = "https://accounts.zoho.in"

            response = self.session.post(f"{accounts_url}/oauth/v2/token", data={
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token'
            }, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.session.headers.update({'Authorization': f'Zoho-oauthtoken {self.access_token}'})
                return True
            return False
        except Exception as e:
            logger.error(f"Zoho token refresh error: {e}")
            return False

    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        kwargs.setdefault('timeout', 30)
        if not self.access_token:
            self._refresh_access_token()
        response = self.session.request(method, url, **kwargs)
        if response.status_code == 401:
            if self._refresh_access_token():
                response = self.session.request(method, url, **kwargs)
        self.last_request_time = time.time()
        return response

    def close(self):
        self.session.close()

    def test_connection(self) -> Dict:
        try:
            if not self._refresh_access_token():
                return {"status": "error", "message": "No se pudo obtener token de acceso. Verifica Client ID, Client Secret y Refresh Token."}
            response = self._rate_limited_request('GET', f"{self.base_url}/crm/v6/settings/modules")
            if response.status_code == 200:
                return {"status": "success", "message": "Conexión exitosa a Zoho CRM"}
            elif response.status_code == 401:
                return {"status": "error", "message": "Token inválido o expirado"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Acceso denegado - verifica los scopes del token"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar a Zoho CRM. Verifica la URL."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoho connection error: {e}")
            return {"status": "error", "message": "Error de conexión a Zoho CRM."}

    def get_products(self, limit: int = 500) -> List[Dict]:
        try:
            products = []
            page = 1
            while len(products) < limit:
                response = self._rate_limited_request(
                    'GET', f"{self.base_url}/crm/v6/Products",
                    params={'per_page': min(200, limit - len(products)), 'page': page}
                )
                if response.status_code == 200:
                    data = response.json().get('data', [])
                    if not data:
                        break
                    products.extend(data)
                    page += 1
                else:
                    break
            return products
        except Exception as e:
            logger.error(f"Zoho get_products error: {e}")
            return []

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        try:
            response = self._rate_limited_request(
                'GET', f"{self.base_url}/crm/v6/Products/search",
                params={'criteria': f'(Product_Code:equals:{sku})'}
            )
            if response.status_code == 200:
                data = response.json().get('data', [])
                return data[0] if data else None
            return None
        except Exception as e:
            logger.error(f"Zoho get_product_by_sku error: {e}")
            return None

    def create_product(self, product_data: Dict) -> Optional[Dict]:
        try:
            response = self._rate_limited_request(
                'POST', f"{self.base_url}/crm/v6/Products",
                json={'data': [product_data]}
            )
            if response.status_code in [200, 201]:
                results = response.json().get('data', [])
                return results[0] if results else None
            return None
        except Exception as e:
            logger.error(f"Zoho create_product error: {e}")
            return None

    def update_product(self, product_id: str, product_data: Dict) -> bool:
        try:
            response = self._rate_limited_request(
                'PUT', f"{self.base_url}/crm/v6/Products/{product_id}",
                json={'data': [product_data]}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Zoho update_product error: {e}")
            return False

    def get_stats(self) -> Dict:
        stats = {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}
        try:
            for module, key in [('Products', 'products'), ('Vendors', 'suppliers'), ('Contacts', 'clients'), ('Sales_Orders', 'orders')]:
                response = self._rate_limited_request('GET', f"{self.base_url}/crm/v6/{module}", params={'per_page': 1})
                if response.status_code == 200:
                    info = response.json().get('info', {})
                    stats[key] = info.get('count', 0)
        except Exception as e:
            logger.error(f"Zoho get_stats error: {e}")
        return stats


# ==================== PIPEDRIVE CLIENT ====================

class PipedriveClient:
    """Pipedrive CRM API Client"""

    def __init__(self, api_url: str, api_token: str):
        self.base_url = _validate_crm_url(api_url).rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json', 'Accept': 'application/json'})
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
        self.session.mount('https://', adapter)
        self.min_delay = 0.1
        self.last_request_time = 0

    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        kwargs.setdefault('timeout', 30)
        # Add API token to params
        params = kwargs.get('params', {}) or {}
        params['api_token'] = self.api_token
        kwargs['params'] = params
        response = self.session.request(method, url, **kwargs)
        self.last_request_time = time.time()
        return response

    def close(self):
        self.session.close()

    def test_connection(self) -> Dict:
        try:
            response = self._rate_limited_request('GET', f"{self.base_url}/api/v1/users/me")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {"status": "success", "message": "Conexión exitosa a Pipedrive"}
                return {"status": "error", "message": "API Token inválido"}
            elif response.status_code == 401:
                return {"status": "error", "message": "API Token inválido"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar a Pipedrive. Verifica la URL."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Pipedrive connection error: {e}")
            return {"status": "error", "message": "Error de conexión a Pipedrive."}

    def get_products(self, limit: int = 500) -> List[Dict]:
        try:
            products = []
            start = 0
            while len(products) < limit:
                response = self._rate_limited_request(
                    'GET', f"{self.base_url}/api/v1/products",
                    params={'start': start, 'limit': min(100, limit - len(products))}
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('data', [])
                    if not items:
                        break
                    products.extend(items)
                    if not data.get('additional_data', {}).get('pagination', {}).get('more_items_in_collection'):
                        break
                    start += len(items)
                else:
                    break
            return products
        except Exception as e:
            logger.error(f"Pipedrive get_products error: {e}")
            return []

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        try:
            response = self._rate_limited_request(
                'GET', f"{self.base_url}/api/v1/products/search",
                params={'term': sku, 'fields': 'code', 'limit': 1}
            )
            if response.status_code == 200:
                items = response.json().get('data', {}).get('items', [])
                return items[0].get('item') if items else None
            return None
        except Exception as e:
            logger.error(f"Pipedrive get_product_by_sku error: {e}")
            return None

    def create_product(self, product_data: Dict) -> Optional[Dict]:
        try:
            response = self._rate_limited_request('POST', f"{self.base_url}/api/v1/products", json=product_data)
            if response.status_code in [200, 201] and response.json().get('success'):
                return response.json().get('data')
            return None
        except Exception as e:
            logger.error(f"Pipedrive create_product error: {e}")
            return None

    def update_product(self, product_id: str, product_data: Dict) -> bool:
        try:
            response = self._rate_limited_request('PUT', f"{self.base_url}/api/v1/products/{product_id}", json=product_data)
            return response.status_code == 200 and response.json().get('success')
        except Exception as e:
            logger.error(f"Pipedrive update_product error: {e}")
            return False

    def get_stats(self) -> Dict:
        stats = {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}
        try:
            for endpoint, key in [('products', 'products'), ('organizations', 'suppliers'), ('persons', 'clients'), ('deals', 'orders')]:
                response = self._rate_limited_request('GET', f"{self.base_url}/api/v1/{endpoint}", params={'start': 0, 'limit': 1})
                if response.status_code == 200:
                    pagination = response.json().get('additional_data', {}).get('pagination', {})
                    stats[key] = pagination.get('count', 0)
        except Exception as e:
            logger.error(f"Pipedrive get_stats error: {e}")
        return stats


# ==================== MONDAY CRM CLIENT ====================

class MondayClient:
    """Monday.com CRM API Client (GraphQL)"""

    def __init__(self, api_token: str, board_id: str = ""):
        self.api_url = "https://api.monday.com/v2"
        self.api_token = api_token
        self.board_id = board_id
        self.headers = {
            'Authorization': api_token,
            'Content-Type': 'application/json',
            'API-Version': '2024-10'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
        self.session.mount('https://', adapter)
        self.min_delay = 0.1
        self.last_request_time = 0

    def _rate_limited_request(self, query: str, variables: Dict = None) -> Dict:
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        response = self.session.post(self.api_url, json=payload, timeout=30)
        self.last_request_time = time.time()
        if response.status_code == 200:
            return response.json()
        return {'errors': [{'message': f"HTTP {response.status_code}"}]}

    def close(self):
        self.session.close()

    def test_connection(self) -> Dict:
        try:
            result = self._rate_limited_request('{ me { id name } }')
            if result.get('data', {}).get('me', {}).get('id'):
                return {"status": "success", "message": "Conexión exitosa a Monday.com"}
            errors = result.get('errors', [])
            if errors:
                return {"status": "error", "message": errors[0].get('message', 'Error desconocido')}
            return {"status": "error", "message": "API Token inválido"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar a Monday.com."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Monday connection error: {e}")
            return {"status": "error", "message": "Error de conexión a Monday.com."}

    def get_products(self, limit: int = 500) -> List[Dict]:
        try:
            if not self.board_id:
                return []
            query = f'''{{ boards(ids: [{self.board_id}]) {{ items_page(limit: {min(limit, 500)}) {{ items {{ id name column_values {{ id text value }} }} }} }} }}'''
            result = self._rate_limited_request(query)
            boards = result.get('data', {}).get('boards', [])
            if boards:
                return boards[0].get('items_page', {}).get('items', [])
            return []
        except Exception as e:
            logger.error(f"Monday get_products error: {e}")
            return []

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        products = self.get_products(limit=500)
        for item in products:
            for col in item.get('column_values', []):
                if col.get('text') == sku:
                    return item
        return None

    def create_product(self, product_data: Dict) -> Optional[Dict]:
        try:
            if not self.board_id:
                return None
            name = product_data.get('name', 'Producto')
            columns = product_data.get('column_values', '{}')
            query = 'mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON) { create_item(board_id: $boardId, item_name: $itemName, column_values: $columnValues) { id name } }'
            result = self._rate_limited_request(query, {'boardId': self.board_id, 'itemName': name, 'columnValues': columns})
            return result.get('data', {}).get('create_item')
        except Exception as e:
            logger.error(f"Monday create_product error: {e}")
            return None

    def update_product(self, item_id: str, product_data: Dict) -> bool:
        try:
            columns = product_data.get('column_values', '{}')
            query = 'mutation ($boardId: ID!, $itemId: ID!, $columnValues: JSON) { change_multiple_column_values(board_id: $boardId, item_id: $itemId, column_values: $columnValues) { id } }'
            result = self._rate_limited_request(query, {'boardId': self.board_id, 'itemId': item_id, 'columnValues': columns})
            return bool(result.get('data', {}).get('change_multiple_column_values'))
        except Exception as e:
            logger.error(f"Monday update_product error: {e}")
            return False

    def get_stats(self) -> Dict:
        stats = {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}
        try:
            if self.board_id:
                query = f'{{ boards(ids: [{self.board_id}]) {{ items_count }} }}'
                result = self._rate_limited_request(query)
                boards = result.get('data', {}).get('boards', [])
                if boards:
                    stats['products'] = boards[0].get('items_count', 0)
        except Exception as e:
            logger.error(f"Monday get_stats error: {e}")
        return stats


# ==================== FRESHSALES CLIENT ====================

class FreshsalesClient:
    """Freshsales (Freshworks CRM) API Client"""

    def __init__(self, api_url: str, api_token: str):
        self.base_url = _validate_crm_url(api_url).rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Token token={api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
        self.session.mount('https://', adapter)
        self.min_delay = 0.1
        self.last_request_time = 0

    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        import time
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        kwargs.setdefault('timeout', 30)
        response = self.session.request(method, url, **kwargs)
        self.last_request_time = time.time()
        return response

    def close(self):
        self.session.close()

    def test_connection(self) -> Dict:
        try:
            response = self._rate_limited_request('GET', f"{self.base_url}/api/contacts/filters")
            if response.status_code == 200:
                return {"status": "success", "message": "Conexión exitosa a Freshsales"}
            elif response.status_code == 401:
                return {"status": "error", "message": "API Key inválida"}
            elif response.status_code == 403:
                return {"status": "error", "message": "Acceso denegado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "No se puede conectar a Freshsales. Verifica la URL."}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Tiempo de espera agotado"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Freshsales connection error: {e}")
            return {"status": "error", "message": "Error de conexión a Freshsales."}

    def get_products(self, limit: int = 500) -> List[Dict]:
        try:
            products = []
            page = 1
            while len(products) < limit:
                response = self._rate_limited_request(
                    'GET', f"{self.base_url}/api/cpq/products",
                    params={'page': page, 'per_page': min(100, limit - len(products))}
                )
                if response.status_code == 200:
                    data = response.json().get('products', [])
                    if not data:
                        break
                    products.extend(data)
                    page += 1
                else:
                    break
            return products
        except Exception as e:
            logger.error(f"Freshsales get_products error: {e}")
            return []

    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        try:
            response = self._rate_limited_request(
                'GET', f"{self.base_url}/api/cpq/products",
                params={'filter': 'all', 'per_page': 100}
            )
            if response.status_code == 200:
                for product in response.json().get('products', []):
                    if product.get('sku') == sku or product.get('product_code') == sku:
                        return product
            return None
        except Exception as e:
            logger.error(f"Freshsales get_product_by_sku error: {e}")
            return None

    def create_product(self, product_data: Dict) -> Optional[Dict]:
        try:
            response = self._rate_limited_request(
                'POST', f"{self.base_url}/api/cpq/products",
                json={'product': product_data}
            )
            if response.status_code in [200, 201]:
                return response.json().get('product')
            return None
        except Exception as e:
            logger.error(f"Freshsales create_product error: {e}")
            return None

    def update_product(self, product_id: str, product_data: Dict) -> bool:
        try:
            response = self._rate_limited_request(
                'PUT', f"{self.base_url}/api/cpq/products/{product_id}",
                json={'product': product_data}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Freshsales update_product error: {e}")
            return False

    def get_stats(self) -> Dict:
        stats = {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}
        try:
            for endpoint, key in [('cpq/products', 'products'), ('contacts', 'clients'), ('deals', 'orders')]:
                response = self._rate_limited_request('GET', f"{self.base_url}/api/{endpoint}", params={'per_page': 1})
                if response.status_code == 200:
                    data = response.json()
                    # Freshsales returns total in meta or headers
                    total = response.headers.get('x-total-count', 0)
                    stats[key] = int(total) if total else len(data.get(endpoint.split('/')[-1], []))
        except Exception as e:
            logger.error(f"Freshsales get_stats error: {e}")
        return stats


# ==================== CRM CLIENT FACTORY ====================

def create_crm_client(platform: str, config: dict):
    """Factory function to create the appropriate CRM client based on platform"""
    if platform == "dolibarr":
        return DolibarrClient(api_url=config.get("api_url", ""), api_key=config.get("api_key", ""))
    elif platform == "odoo":
        return OdooClient(api_url=config.get("api_url", ""), api_token=config.get("api_token", ""))
    elif platform == "hubspot":
        return HubSpotClient(api_token=config.get("api_token", ""))
    elif platform == "salesforce":
        return SalesforceClient(
            api_url=config.get("api_url", ""),
            client_id=config.get("client_id", ""),
            client_secret=config.get("client_secret", ""),
            api_token=config.get("api_token", "")
        )
    elif platform == "zoho":
        return ZohoClient(
            api_url=config.get("api_url", ""),
            client_id=config.get("client_id", ""),
            client_secret=config.get("client_secret", ""),
            api_token=config.get("api_token", "")
        )
    elif platform == "pipedrive":
        return PipedriveClient(api_url=config.get("api_url", ""), api_token=config.get("api_token", ""))
    elif platform == "monday":
        return MondayClient(api_token=config.get("api_token", ""), board_id=config.get("board_id", ""))
    elif platform == "freshsales":
        return FreshsalesClient(api_url=config.get("api_url", ""), api_token=config.get("api_token", ""))
    return None


# Platforms that support full sync (products, suppliers, orders)
FULL_SYNC_PLATFORMS = {"dolibarr", "odoo"}
# Platforms that support basic sync (products only via generic pattern)
BASIC_SYNC_PLATFORMS = {"hubspot", "salesforce", "zoho", "pipedrive", "monday", "freshsales"}

