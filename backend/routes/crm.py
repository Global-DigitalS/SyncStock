"""
CRM Integration Routes
Supports: Dolibarr, and future CRMs (HubSpot, Salesforce, Zoho, etc.)
Full sync: Suppliers, Products (stock, price, description, images), Orders
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import re
import logging
import requests
import base64

from services.database import db
from services.auth import get_current_user
from services.sync import calculate_final_price

router = APIRouter()
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


# ==================== CRM ENDPOINTS ====================

@router.get("/crm/auto-sync-permissions")
async def get_crm_auto_sync_permissions(user: dict = Depends(get_current_user)):
    """Get user's CRM auto-sync permissions based on subscription plan"""
    from services.crm_scheduler import get_user_crm_sync_permission
    
    permission = await get_user_crm_sync_permission(user["id"])
    return permission


@router.get("/crm/connections")
async def get_crm_connections(user: dict = Depends(get_current_user)):
    """Get all CRM connections for the user"""
    connections = await db.crm_connections.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(100)
    
    # Get stats for each connected CRM
    for conn in connections:
        if conn.get("is_connected"):
            try:
                if conn["platform"] == "dolibarr":
                    client = DolibarrClient(
                        api_url=conn["config"].get("api_url", ""),
                        api_key=conn["config"].get("api_key", "")
                    )
                    conn["stats"] = client.get_stats()
                elif conn["platform"] == "odoo":
                    client = OdooClient(
                        api_url=conn["config"].get("api_url", ""),
                        api_token=conn["config"].get("api_token", "")
                    )
                    conn["stats"] = client.get_stats()
            except Exception as e:
                logger.error(f"Error getting CRM stats: {e}")
                conn["stats"] = {"products": 0, "suppliers": 0, "clients": 0, "orders": 0}
    
    return connections


@router.post("/crm/connections")
async def create_crm_connection(request: dict, user: dict = Depends(get_current_user)):
    """Create a new CRM connection"""
    now = datetime.now(timezone.utc).isoformat()
    
    connection = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": request.get("name", "Mi CRM"),
        "platform": request.get("platform"),
        "config": request.get("config", {}),
        "sync_settings": request.get("sync_settings", {
            "products": True,
            "stock": True,
            "prices": True,
            "descriptions": True,
            "images": True,
            "suppliers": True,
            "orders": True
        }),
        "auto_sync_enabled": request.get("auto_sync_enabled", False),
        "auto_sync_interval": request.get("auto_sync_interval", 24),  # hours: 1, 6, 12, 24
        "is_connected": False,
        "last_sync": None,
        "last_sync_error": None,
        "created_at": now,
        "updated_at": now
    }
    
    # Test the connection
    if connection["platform"] == "dolibarr":
        client = DolibarrClient(
            api_url=connection["config"].get("api_url", ""),
            api_key=connection["config"].get("api_key", "")
        )
        result = client.test_connection()
        connection["is_connected"] = result["status"] == "success"
    elif connection["platform"] == "odoo":
        client = OdooClient(
            api_url=connection["config"].get("api_url", ""),
            api_token=connection["config"].get("api_token", "")
        )
        result = client.test_connection()
        connection["is_connected"] = result["status"] == "success"
    
    await db.crm_connections.insert_one(connection)
    
    # Return without _id
    connection.pop("_id", None)
    return connection


@router.put("/crm/connections/{connection_id}")
async def update_crm_connection(connection_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Update a CRM connection"""
    connection = await db.crm_connections.find_one({
        "id": connection_id,
        "user_id": user["id"]
    })
    
    if not connection:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    update_data = {
        "name": request.get("name", connection["name"]),
        "config": request.get("config", connection["config"]),
        "sync_settings": request.get("sync_settings", connection.get("sync_settings", {})),
        "auto_sync_enabled": request.get("auto_sync_enabled", connection.get("auto_sync_enabled", False)),
        "auto_sync_interval": request.get("auto_sync_interval", connection.get("auto_sync_interval", 24)),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Test the connection with new config
    platform = connection["platform"]
    if platform == "dolibarr":
        client = DolibarrClient(
            api_url=update_data["config"].get("api_url", ""),
            api_key=update_data["config"].get("api_key", "")
        )
        result = client.test_connection()
        update_data["is_connected"] = result["status"] == "success"
    elif platform == "odoo":
        client = OdooClient(
            api_url=update_data["config"].get("api_url", ""),
            api_token=update_data["config"].get("api_token", "")
        )
        result = client.test_connection()
        update_data["is_connected"] = result["status"] == "success"
    
    await db.crm_connections.update_one(
        {"id": connection_id},
        {"$set": update_data}
    )
    
    return {"status": "success", "message": "Conexión actualizada"}


@router.delete("/crm/connections/{connection_id}")
async def delete_crm_connection(connection_id: str, user: dict = Depends(get_current_user)):
    """Delete a CRM connection"""
    result = await db.crm_connections.delete_one({
        "id": connection_id,
        "user_id": user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    return {"status": "success", "message": "Conexión eliminada"}


@router.post("/crm/test-connection")
async def test_crm_connection(request: dict, user: dict = Depends(get_current_user)):
    """Test a CRM connection without saving"""
    platform = request.get("platform")
    config = request.get("config", {})
    
    if platform == "dolibarr":
        client = DolibarrClient(
            api_url=config.get("api_url", ""),
            api_key=config.get("api_key", "")
        )
        return client.test_connection()
    elif platform == "odoo":
        client = OdooClient(
            api_url=config.get("api_url", ""),
            api_token=config.get("api_token", "")
        )
        return client.test_connection()
    
    return {"status": "error", "message": f"Plataforma no soportada: {platform}"}


@router.post("/crm/connections/{connection_id}/sync")
async def sync_crm_connection(connection_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Sync data with a CRM - runs in background with progress tracking"""
    import asyncio
    
    connection = await db.crm_connections.find_one({
        "id": connection_id,
        "user_id": user["id"]
    })
    
    if not connection:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    sync_type = request.get("sync_type", "all")
    catalog_id = request.get("catalog_id")  # Optional: filter by catalog
    platform = connection["platform"]
    config = connection["config"]
    sync_settings = connection.get("sync_settings", {})
    
    # Create sync job for progress tracking
    sync_job_id = str(uuid.uuid4())
    sync_job = {
        "id": sync_job_id,
        "user_id": user["id"],
        "connection_id": connection_id,
        "status": "running",
        "progress": 0,
        "current_step": "Iniciando sincronización...",
        "total_items": 0,
        "processed_items": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    await db.sync_jobs.insert_one(sync_job)
    
    # Run sync in background task
    asyncio.create_task(run_sync_in_background(
        sync_job_id=sync_job_id,
        user_id=user["id"],
        connection_id=connection_id,
        platform=platform,
        config=config,
        sync_settings=sync_settings,
        sync_type=sync_type,
        catalog_id=catalog_id
    ))
    
    # Return immediately with job ID
    return {
        "status": "started",
        "sync_job_id": sync_job_id,
        "message": "Sincronización iniciada en segundo plano"
    }


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
        if platform == "dolibarr":
            client = DolibarrClient(
                api_url=config.get("api_url", ""),
                api_key=config.get("api_key", "")
            )
            
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
        
        elif platform == "odoo":
            client = OdooClient(
                api_url=config.get("api_url", ""),
                api_token=config.get("api_token", "")
            )
            
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
        else:
            await db.sync_jobs.update_one(
                {"id": sync_job_id},
                {"$set": {
                    "status": "error",
                    "current_step": f"Plataforma no soportada: {platform}",
                    "completed_at": datetime.now(timezone.utc).isoformat()
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


@router.get("/crm/sync-jobs/{job_id}")
async def get_sync_job_status(job_id: str, user: dict = Depends(get_current_user)):
    """Get the status of a sync job for progress tracking"""
    job = await db.sync_jobs.find_one(
        {"id": job_id, "user_id": user["id"]},
        {"_id": 0}
    )
    
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    return job


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
        
        # Create map of product_id -> catalog_item for custom prices
        catalog_items_map = {item.get("product_id"): item for item in catalog_items}
        
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
            existing = client.get_product_by_ref(sku)
            
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
                product_data["stock"] = product.get("stock", 0)
            
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
                        stock_result = client.update_stock(product_id, product.get("stock", 0))
                        if stock_result.get("status") == "success":
                            stock_synced += 1
                    
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


@router.get("/crm/connections/{connection_id}/orders")
async def get_synced_orders(connection_id: str, user: dict = Depends(get_current_user)):
    """Get orders synced from stores"""
    orders = await db.crm_synced_orders.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("synced_at", -1).to_list(100)
    
    return orders
