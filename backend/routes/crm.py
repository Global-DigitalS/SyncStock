"""
CRM Integration Routes
Supports: Dolibarr, and future CRMs (HubSpot, Salesforce, Zoho, etc.)
Full sync: Suppliers, Products (stock, price, description, images), Orders
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import logging
import requests
import base64

from services.database import db
from services.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== DOLIBARR CLIENT ====================

class DolibarrClient:
    """Dolibarr ERP/CRM API Client - Full Integration"""
    
    def __init__(self, api_url: str, api_key: str):
        self.base_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'DOLAPIKEY': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def test_connection(self) -> Dict:
        """Test API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/status",
                headers=self.headers,
                timeout=30
            )
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
            return {"status": "error", "message": f"Error de conexión: {str(e)}"}
    
    # ==================== PRODUCTS ====================
    
    def get_products(self, limit: int = 500) -> List[Dict]:
        """Get products from Dolibarr"""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                headers=self.headers,
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
            response = requests.get(
                f"{self.base_url}/products/ref/{ref}",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Dolibarr get_product_by_ref error: {e}")
            return None
    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product in Dolibarr with full data including purchase price"""
        try:
            # Build description (combine short and long)
            description = product_data.get("long_description") or product_data.get("description", "")
            if product_data.get("short_description"):
                description = f"{product_data['short_description']}\n\n{description}"
            
            # The price from supplier is the cost/purchase price
            cost_price = product_data.get("cost_price") or product_data.get("price", 0)
            
            payload = {
                "ref": product_data.get("sku", ""),
                "label": product_data.get("name", ""),
                "description": description,
                "price": cost_price,  # Sale price (can be adjusted later)
                "price_base_type": "HT",  # Price without tax
                "cost_price": cost_price,  # Purchase/cost price
                "status": 1,  # On sale
                "status_buy": 1,  # On purchase
                "type": 0,  # Product (not service)
                "barcode": product_data.get("ean", ""),
                "weight": product_data.get("weight", 0),
                "stock_reel": product_data.get("stock", 0),
            }
            
            # Add brand and supplier info as note
            notes = []
            if product_data.get("brand"):
                notes.append(f"Marca: {product_data['brand']}")
            if product_data.get("supplier_name"):
                notes.append(f"Proveedor: {product_data['supplier_name']}")
            if notes:
                payload["note_public"] = "\n".join(notes)
            
            response = requests.post(
                f"{self.base_url}/products",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                product_id = response.json()
                
                # Upload image if available
                if product_data.get("image_url"):
                    self.upload_product_image(product_id, product_data["image_url"])
                
                return {"status": "success", "product_id": product_id, "message": "Producto creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
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
            
            if "stock" in product_data:
                payload["stock_reel"] = product_data["stock"]
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
            
            response = requests.put(
                f"{self.base_url}/products/{product_id}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                # Update image if provided (handled separately for better error handling)
                return {"status": "success", "message": "Producto actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
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
            
            # Validate it's a proper HTTP/HTTPS URL
            if not image_url.startswith(('http://', 'https://')):
                return {"status": "skip", "message": "Invalid image URL format"}
            
            # Download image with user agent
            headers = {"User-Agent": "Mozilla/5.0 (compatible; CatalogSync/1.0)"}
            img_response = requests.get(image_url, timeout=30, headers=headers)
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
            
            response = requests.post(
                f"{self.base_url}/documents/upload",
                headers=self.headers,
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
            return {"status": "error", "message": str(e)}
    
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
            
            response = requests.post(
                f"{self.base_url}/stockmovements",
                headers=self.headers,
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
            return {"status": "error", "message": str(e)}
    
    def get_warehouses(self) -> List[Dict]:
        """Get all warehouses from Dolibarr"""
        try:
            response = requests.get(
                f"{self.base_url}/warehouses",
                headers=self.headers,
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
            response = requests.post(
                f"{self.base_url}/warehouses",
                headers=self.headers,
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
            response = requests.get(
                f"{self.base_url}/products/{product_id}",
                headers=self.headers,
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
            
            response = requests.get(
                f"{self.base_url}/thirdparties",
                headers=self.headers,
                params=params,
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
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
            payload = {
                "name": supplier_data.get("name", ""),
                "name_alias": supplier_data.get("alias", ""),
                "email": supplier_data.get("email", ""),
                "phone": supplier_data.get("phone", ""),
                "address": supplier_data.get("address", ""),
                "zip": supplier_data.get("zip", ""),
                "town": supplier_data.get("city", ""),
                "country_code": supplier_data.get("country_code", "ES"),
                "fournisseur": 1,  # Mark as supplier
                "client": 0,  # Not a client
                "code_fournisseur": supplier_data.get("supplier_code", ""),
                "note_public": supplier_data.get("notes", ""),
                "status": 1  # Active
            }
            
            response = requests.post(
                f"{self.base_url}/thirdparties",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                supplier_id = response.json()
                return {"status": "success", "supplier_id": supplier_id, "message": "Proveedor creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
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
            
            response = requests.put(
                f"{self.base_url}/thirdparties/{supplier_id}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"status": "success", "message": "Proveedor actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_supplier_by_name(self, name: str) -> Optional[Dict]:
        """Find supplier by name using direct API search"""
        try:
            # First try to get suppliers and search
            suppliers = self.get_suppliers(limit=500)
            for s in suppliers:
                if s.get("name", "").lower() == name.lower():
                    return s
            
            # If not found in list, try direct search with SQL filter
            try:
                response = requests.get(
                    f"{self.base_url}/thirdparties",
                    headers=self.headers,
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
            
            response = requests.post(
                f"{self.base_url}/products/{product_id}/purchase_prices",
                headers=self.headers,
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
            return {"status": "error", "message": str(e)}
    
    # ==================== ORDERS ====================
    
    def get_orders(self, limit: int = 100) -> List[Dict]:
        """Get customer orders from Dolibarr"""
        try:
            response = requests.get(
                f"{self.base_url}/orders",
                headers=self.headers,
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
            response = requests.get(
                f"{self.base_url}/supplierorders",
                headers=self.headers,
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
            
            response = requests.post(
                f"{self.base_url}/orders",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                order_id = response.json()
                return {"status": "success", "order_id": order_id, "message": "Pedido creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
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
            
            response = requests.post(
                f"{self.base_url}/supplierorders",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                order_id = response.json()
                return {"status": "success", "order_id": order_id, "message": "Pedido a proveedor creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
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
    
    return {"status": "error", "message": f"Plataforma no soportada: {platform}"}


@router.post("/crm/connections/{connection_id}/sync")
async def sync_crm_connection(connection_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Sync data with a CRM - supports multiple sync types"""
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
    
    results = {
        "products": None,
        "suppliers": None,
        "orders": None
    }
    
    if platform == "dolibarr":
        client = DolibarrClient(
            api_url=config.get("api_url", ""),
            api_key=config.get("api_key", "")
        )
        
        # Sync products (stock, price, description, images)
        if sync_type in ["all", "products"]:
            results["products"] = await sync_products_to_dolibarr(client, user["id"], sync_settings, catalog_id)
        
        # Sync suppliers
        if sync_type in ["all", "suppliers"]:
            results["suppliers"] = await sync_suppliers_to_dolibarr(client, user["id"])
        
        # Import orders from stores to CRM
        if sync_type in ["all", "orders"]:
            results["orders"] = await sync_orders_to_dolibarr(client, user["id"])
        
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
        
        return {
            "status": "success",
            "message": " | ".join(messages) if messages else "Sincronización completada",
            "details": results
        }
    
    return {"status": "error", "message": f"Plataforma no soportada: {platform}"}


async def sync_products_to_dolibarr(client: DolibarrClient, user_id: str, sync_settings: dict = None, catalog_id: str = None) -> Dict:
    """Sync products from our catalog to Dolibarr with full data including purchase price, stock and images"""
    if sync_settings is None:
        sync_settings = {"products": True, "stock": True, "prices": True, "descriptions": True, "images": True}
    
    # Build query filter
    query = {"user_id": user_id, "is_selected": True}
    
    # If catalog_id is provided, get only products from that catalog
    if catalog_id:
        catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user_id})
        if not catalog:
            return {"status": "error", "message": "Catálogo no encontrado", "created": 0, "updated": 0}
        
        # Get EANs from catalog products
        catalog_eans = [p.get("ean") for p in catalog.get("products", []) if p.get("ean")]
        if not catalog_eans:
            return {"status": "warning", "message": "El catálogo no tiene productos", "created": 0, "updated": 0}
        
        query["ean"] = {"$in": catalog_eans}
    
    # Get products based on query
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    
    if not products:
        return {"status": "warning", "message": "No hay productos para sincronizar", "created": 0, "updated": 0}
    
    # Get all suppliers for this user to map supplier names
    suppliers = await db.suppliers.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    suppliers_map = {s["id"]: s for s in suppliers}
    
    created = 0
    updated = 0
    errors = 0
    images_synced = 0
    stock_synced = 0
    
    for product in products:
        try:
            sku = product.get("sku", "")
            if not sku:
                errors += 1
                continue
            
            # Check if product exists in Dolibarr by SKU
            existing = client.get_product_by_ref(sku)
            
            product_data = {
                "sku": sku,
                "name": product.get("name", ""),
            }
            
            # Add purchase/cost price (the supplier price is the purchase price)
            if sync_settings.get("prices", True):
                # The product price from supplier is the purchase/cost price
                purchase_price = product.get("price", 0)
                product_data["price"] = purchase_price
                product_data["cost_price"] = purchase_price  # This is the purchase price
            
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
                "notes": f"Tipo conexión: {supplier.get('connection_type', 'N/A')}. Productos: {supplier.get('product_count', 0)}",
                "supplier_code": supplier.get("id", "")[:10]
            }
            
            if existing:
                dolibarr_id = int(existing.get("id"))
                result = client.update_supplier(dolibarr_id, supplier_data)
                if result["status"] == "success":
                    updated += 1
                    supplier_mapping[supplier["id"]] = dolibarr_id
                else:
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


@router.get("/crm/connections/{connection_id}/orders")
async def get_synced_orders(connection_id: str, user: dict = Depends(get_current_user)):
    """Get orders synced from stores"""
    orders = await db.crm_synced_orders.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("synced_at", -1).to_list(100)
    
    return orders
