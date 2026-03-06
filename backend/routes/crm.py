"""
CRM Integration Routes
Supports: Dolibarr, and future CRMs (HubSpot, Salesforce, Zoho, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import logging
import requests

from services.database import db
from services.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== DOLIBARR CLIENT ====================

class DolibarrClient:
    """Dolibarr ERP/CRM API Client"""
    
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
    
    def get_products(self, limit: int = 100) -> List[Dict]:
        """Get products from Dolibarr"""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                headers=self.headers,
                params={'limit': limit, 'sortfield': 'rowid', 'sortorder': 'DESC'},
                timeout=30
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
        """Create a new product in Dolibarr"""
        try:
            payload = {
                "ref": product_data.get("sku", ""),
                "label": product_data.get("name", ""),
                "description": product_data.get("description", ""),
                "price": product_data.get("price", 0),
                "price_base_type": "HT",  # Price without tax
                "status": 1,  # On sale
                "status_buy": 1,  # On purchase
                "type": 0,  # Product (not service)
                "barcode": product_data.get("ean", ""),
                "weight": product_data.get("weight", 0),
                "stock_reel": product_data.get("stock", 0),
            }
            
            response = requests.post(
                f"{self.base_url}/products",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                product_id = response.json()
                return {"status": "success", "product_id": product_id, "message": "Producto creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """Update an existing product"""
        try:
            payload = {}
            if "name" in product_data:
                payload["label"] = product_data["name"]
            if "description" in product_data:
                payload["description"] = product_data["description"]
            if "price" in product_data:
                payload["price"] = product_data["price"]
            if "stock" in product_data:
                payload["stock_reel"] = product_data["stock"]
            if "ean" in product_data:
                payload["barcode"] = product_data["ean"]
            
            response = requests.put(
                f"{self.base_url}/products/{product_id}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return {"status": "success", "message": "Producto actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def get_thirdparties(self, limit: int = 100) -> List[Dict]:
        """Get third parties (clients/suppliers) from Dolibarr"""
        try:
            response = requests.get(
                f"{self.base_url}/thirdparties",
                headers=self.headers,
                params={'limit': limit},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Dolibarr get_thirdparties error: {e}")
            return []
    
    def get_orders(self, limit: int = 100) -> List[Dict]:
        """Get orders from Dolibarr"""
        try:
            response = requests.get(
                f"{self.base_url}/orders",
                headers=self.headers,
                params={'limit': limit, 'sortfield': 'rowid', 'sortorder': 'DESC'},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Dolibarr get_orders error: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get basic stats from Dolibarr"""
        try:
            # Count totals
            products_count = len(self.get_products(limit=10000))
            clients_count = len([t for t in self.get_thirdparties(limit=10000) if t.get('client') == '1'])
            orders_count = len(self.get_orders(limit=10000))
            
            return {
                "products": products_count,
                "clients": clients_count,
                "orders": orders_count
            }
        except Exception as e:
            logger.error(f"Dolibarr get_stats error: {e}")
            return {"products": 0, "clients": 0, "orders": 0}


# ==================== CRM ENDPOINTS ====================

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
                conn["stats"] = {"products": 0, "clients": 0, "orders": 0}
    
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
        "is_connected": False,
        "last_sync": None,
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
    """Sync data with a CRM"""
    connection = await db.crm_connections.find_one({
        "id": connection_id,
        "user_id": user["id"]
    })
    
    if not connection:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    sync_type = request.get("sync_type", "products")
    platform = connection["platform"]
    config = connection["config"]
    
    if platform == "dolibarr":
        client = DolibarrClient(
            api_url=config.get("api_url", ""),
            api_key=config.get("api_key", "")
        )
        
        if sync_type == "products":
            # Get products from our catalog to sync to Dolibarr
            result = await sync_products_to_dolibarr(client, user["id"])
        elif sync_type == "clients":
            # Import clients from Dolibarr
            result = await import_clients_from_dolibarr(client, user["id"])
        else:
            result = {"status": "error", "message": f"Tipo de sync no soportado: {sync_type}"}
        
        # Update last sync time
        await db.crm_connections.update_one(
            {"id": connection_id},
            {"$set": {"last_sync": datetime.now(timezone.utc).isoformat()}}
        )
        
        return result
    
    return {"status": "error", "message": f"Plataforma no soportada: {platform}"}


async def sync_products_to_dolibarr(client: DolibarrClient, user_id: str) -> Dict:
    """Sync products from our catalog to Dolibarr"""
    # Get user's products
    products = await db.products.find(
        {"user_id": user_id, "is_selected": True},
        {"_id": 0}
    ).to_list(10000)
    
    if not products:
        return {"status": "warning", "message": "No hay productos para sincronizar"}
    
    created = 0
    updated = 0
    errors = 0
    
    for product in products:
        try:
            # Check if product exists in Dolibarr by SKU
            existing = client.get_product_by_ref(product.get("sku", ""))
            
            product_data = {
                "sku": product.get("sku", ""),
                "name": product.get("name", ""),
                "description": product.get("long_description") or product.get("description", ""),
                "price": product.get("price", 0),
                "stock": product.get("stock", 0),
                "ean": product.get("ean", ""),
                "weight": product.get("weight", 0)
            }
            
            if existing:
                result = client.update_product(int(existing.get("id")), product_data)
                if result["status"] == "success":
                    updated += 1
                else:
                    errors += 1
            else:
                result = client.create_product(product_data)
                if result["status"] == "success":
                    created += 1
                else:
                    errors += 1
        except Exception as e:
            logger.error(f"Error syncing product to Dolibarr: {e}")
            errors += 1
    
    return {
        "status": "success",
        "message": f"{created} creados, {updated} actualizados, {errors} errores",
        "created": created,
        "updated": updated,
        "errors": errors
    }


async def import_clients_from_dolibarr(client: DolibarrClient, user_id: str) -> Dict:
    """Import clients from Dolibarr"""
    thirdparties = client.get_thirdparties(limit=10000)
    clients = [t for t in thirdparties if t.get('client') == '1']
    
    imported = 0
    updated = 0
    
    for c in clients:
        try:
            existing = await db.crm_clients.find_one({
                "user_id": user_id,
                "external_id": str(c.get("id"))
            })
            
            client_data = {
                "user_id": user_id,
                "external_id": str(c.get("id")),
                "source": "dolibarr",
                "name": c.get("name", ""),
                "email": c.get("email", ""),
                "phone": c.get("phone", ""),
                "address": c.get("address", ""),
                "city": c.get("town", ""),
                "zip": c.get("zip", ""),
                "country": c.get("country", ""),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if existing:
                await db.crm_clients.update_one(
                    {"_id": existing["_id"]},
                    {"$set": client_data}
                )
                updated += 1
            else:
                client_data["id"] = str(uuid.uuid4())
                client_data["created_at"] = datetime.now(timezone.utc).isoformat()
                await db.crm_clients.insert_one(client_data)
                imported += 1
        except Exception as e:
            logger.error(f"Error importing client from Dolibarr: {e}")
    
    return {
        "status": "success",
        "message": f"{imported} importados, {updated} actualizados",
        "imported": imported,
        "updated": updated
    }
