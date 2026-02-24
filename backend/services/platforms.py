"""
Multi-Platform eCommerce Integration Service
Supports: WooCommerce, PrestaShop, Shopify, Wix, Magento
"""
import logging
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)


class PlatformIntegrationError(Exception):
    """Custom exception for platform integration errors"""
    pass


# ==================== PRESTASHOP INTEGRATION ====================

class PrestaShopClient:
    """PrestaShop Webservice API Client"""
    
    def __init__(self, store_url: str, api_key: str):
        self.base_url = store_url.rstrip('/') + '/api'
        self.api_key = api_key
        self.auth = HTTPBasicAuth(api_key, api_key)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Io-Format': 'JSON',
            'Output-Format': 'JSON'
        }
    
    def test_connection(self) -> Dict:
        """Test API connection"""
        try:
            response = requests.get(
                f"{self.base_url}?output_format=JSON",
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return {"status": "success", "message": "Conexión exitosa a PrestaShop"}
            elif response.status_code == 401:
                return {"status": "error", "message": "API Key inválida o sin permisos"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error de conexión: {str(e)}"}
    
    def get_products(self, limit: int = 100) -> List[Dict]:
        """Get products from PrestaShop"""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                auth=self.auth,
                headers=self.headers,
                params={
                    'output_format': 'JSON',
                    'display': '[id,reference,name,price,active]',
                    'limit': limit
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('products', [])
            return []
        except Exception as e:
            logger.error(f"PrestaShop get_products error: {e}")
            return []
    
    def get_stock_available(self, product_id: int, combination_id: int = 0) -> Optional[Dict]:
        """Get stock info for a product"""
        try:
            response = requests.get(
                f"{self.base_url}/stock_availables",
                auth=self.auth,
                headers=self.headers,
                params={
                    'filter[id_product]': product_id,
                    'filter[id_product_attribute]': combination_id,
                    'output_format': 'JSON',
                    'display': 'full'
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                stocks = data.get('stock_availables', [])
                return stocks[0] if stocks else None
            return None
        except Exception as e:
            logger.error(f"PrestaShop get_stock error: {e}")
            return None
    
    def update_stock(self, stock_id: int, quantity: int) -> Dict:
        """Update stock quantity"""
        try:
            # PrestaShop requires XML format for PUT requests
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <stock_available>
                    <id>{stock_id}</id>
                    <quantity>{quantity}</quantity>
                </stock_available>
            </prestashop>'''
            
            response = requests.put(
                f"{self.base_url}/stock_availables/{stock_id}",
                auth=self.auth,
                headers={'Content-Type': 'application/xml'},
                data=xml_data,
                timeout=30
            )
            if response.status_code in [200, 201]:
                return {"status": "success", "message": f"Stock actualizado: {quantity}"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product in PrestaShop"""
        try:
            # PrestaShop requires XML format
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <product>
                    <reference><![CDATA[{product_data.get("sku", "")}]]></reference>
                    <name><language id="1"><![CDATA[{product_data.get("name", "")}]]></language></name>
                    <price>{product_data.get("price", 0)}</price>
                    <active>1</active>
                    <state>1</state>
                    <id_category_default>2</id_category_default>
                    <id_tax_rules_group>1</id_tax_rules_group>
                </product>
            </prestashop>'''
            
            response = requests.post(
                f"{self.base_url}/products",
                auth=self.auth,
                headers={'Content-Type': 'application/xml'},
                data=xml_data.encode('utf-8'),
                timeout=30
            )
            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Producto creado", "response": response.text[:500]}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}", "response": response.text[:500]}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """Update an existing product"""
        try:
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <product>
                    <id>{product_id}</id>
                    <price>{product_data.get("price", 0)}</price>
                </product>
            </prestashop>'''
            
            response = requests.put(
                f"{self.base_url}/products/{product_id}",
                auth=self.auth,
                headers={'Content-Type': 'application/xml'},
                data=xml_data,
                timeout=30
            )
            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Producto actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}


# ==================== SHOPIFY INTEGRATION ====================

class ShopifyClient:
    """Shopify Admin API Client"""
    
    def __init__(self, store_url: str, access_token: str, api_version: str = "2024-10"):
        # Normalize store URL
        store_url = store_url.replace('https://', '').replace('http://', '').rstrip('/')
        if not store_url.endswith('.myshopify.com'):
            store_url = f"{store_url}.myshopify.com"
        
        self.base_url = f"https://{store_url}/admin/api/{api_version}"
        self.access_token = access_token
        self.headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict:
        """Test API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/shop.json",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                shop = response.json().get('shop', {})
                return {"status": "success", "message": "Conexión exitosa", "store_name": shop.get('name')}
            elif response.status_code == 401:
                return {"status": "error", "message": "Access Token inválido"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error de conexión: {str(e)}"}
    
    def get_products(self, limit: int = 50) -> List[Dict]:
        """Get products from Shopify"""
        try:
            response = requests.get(
                f"{self.base_url}/products.json",
                headers=self.headers,
                params={'limit': limit},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('products', [])
            return []
        except Exception as e:
            logger.error(f"Shopify get_products error: {e}")
            return []
    
    def get_locations(self) -> List[Dict]:
        """Get inventory locations"""
        try:
            response = requests.get(
                f"{self.base_url}/locations.json",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('locations', [])
            return []
        except Exception as e:
            logger.error(f"Shopify get_locations error: {e}")
            return []
    
    def get_inventory_level(self, inventory_item_id: int, location_id: int) -> Optional[Dict]:
        """Get inventory level for an item at a location"""
        try:
            response = requests.get(
                f"{self.base_url}/inventory_levels.json",
                headers=self.headers,
                params={
                    'inventory_item_ids': inventory_item_id,
                    'location_ids': location_id
                },
                timeout=30
            )
            if response.status_code == 200:
                levels = response.json().get('inventory_levels', [])
                return levels[0] if levels else None
            return None
        except Exception as e:
            logger.error(f"Shopify get_inventory error: {e}")
            return None
    
    def update_inventory(self, inventory_item_id: int, location_id: int, available: int) -> Dict:
        """Update inventory quantity"""
        try:
            response = requests.post(
                f"{self.base_url}/inventory_levels/set.json",
                headers=self.headers,
                json={
                    'location_id': location_id,
                    'inventory_item_id': inventory_item_id,
                    'available': available
                },
                timeout=30
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Inventario actualizado: {available}"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product in Shopify"""
        try:
            payload = {
                'product': {
                    'title': product_data.get('name', ''),
                    'body_html': product_data.get('description', ''),
                    'vendor': product_data.get('brand', ''),
                    'product_type': product_data.get('category', ''),
                    'variants': [{
                        'sku': product_data.get('sku', ''),
                        'price': str(product_data.get('price', 0)),
                        'inventory_management': 'shopify',
                        'barcode': product_data.get('ean', '')
                    }],
                    'images': [{'src': product_data.get('image_url')}] if product_data.get('image_url') else []
                }
            }
            
            response = requests.post(
                f"{self.base_url}/products.json",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                product = response.json().get('product', {})
                return {"status": "success", "product_id": product.get('id'), "message": "Producto creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """Update an existing product"""
        try:
            payload = {'product': {'id': product_id}}
            if 'name' in product_data:
                payload['product']['title'] = product_data['name']
            if 'price' in product_data:
                payload['product']['variants'] = [{'price': str(product_data['price'])}]
            
            response = requests.put(
                f"{self.base_url}/products/{product_id}.json",
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


# ==================== MAGENTO INTEGRATION ====================

class MagentoClient:
    """Magento 2 REST API Client"""
    
    def __init__(self, store_url: str, access_token: str, store_code: str = "default"):
        self.base_url = store_url.rstrip('/') + f'/rest/{store_code}/V1'
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict:
        """Test API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/store/storeConfigs",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                configs = response.json()
                store_name = configs[0].get('base_url', '') if configs else 'Unknown'
                return {"status": "success", "message": "Conexión exitosa a Magento", "store_name": store_name}
            elif response.status_code == 401:
                return {"status": "error", "message": "Token inválido o expirado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error de conexión: {str(e)}"}
    
    def get_products(self, limit: int = 50) -> List[Dict]:
        """Get products from Magento"""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                headers=self.headers,
                params={
                    'searchCriteria[pageSize]': limit,
                    'searchCriteria[currentPage]': 1
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('items', [])
            return []
        except Exception as e:
            logger.error(f"Magento get_products error: {e}")
            return []
    
    def get_stock(self, sku: str) -> Optional[Dict]:
        """Get stock info for a product by SKU"""
        try:
            response = requests.get(
                f"{self.base_url}/stockItems/{sku}",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Magento get_stock error: {e}")
            return None
    
    def update_stock(self, sku: str, quantity: int, is_in_stock: bool = True) -> Dict:
        """Update stock quantity for a product"""
        try:
            stock_info = self.get_stock(sku)
            stock_id = stock_info.get('stock_id', 1) if stock_info else 1
            
            response = requests.put(
                f"{self.base_url}/products/{sku}/stockItems/{stock_id}",
                headers=self.headers,
                json={
                    'stockItem': {
                        'qty': quantity,
                        'is_in_stock': is_in_stock
                    }
                },
                timeout=30
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Stock actualizado: {quantity}"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product in Magento"""
        try:
            payload = {
                'product': {
                    'sku': product_data.get('sku', ''),
                    'name': product_data.get('name', ''),
                    'price': product_data.get('price', 0),
                    'status': 1,  # Enabled
                    'visibility': 4,  # Catalog, Search
                    'type_id': 'simple',
                    'attribute_set_id': 4,  # Default
                    'extension_attributes': {
                        'stock_item': {
                            'qty': product_data.get('stock', 0),
                            'is_in_stock': product_data.get('stock', 0) > 0
                        }
                    },
                    'custom_attributes': []
                }
            }
            
            if product_data.get('ean'):
                payload['product']['custom_attributes'].append({
                    'attribute_code': 'barcode',
                    'value': product_data['ean']
                })
            
            response = requests.post(
                f"{self.base_url}/products",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Producto creado", "sku": product_data.get('sku')}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def update_product(self, sku: str, product_data: Dict) -> Dict:
        """Update an existing product"""
        try:
            payload = {'product': {'sku': sku}}
            if 'name' in product_data:
                payload['product']['name'] = product_data['name']
            if 'price' in product_data:
                payload['product']['price'] = product_data['price']
            
            response = requests.put(
                f"{self.base_url}/products/{sku}",
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


# ==================== WIX INTEGRATION ====================

class WixClient:
    """Wix eCommerce API Client"""
    
    def __init__(self, store_url: str, api_key: str, site_id: str):
        self.base_url = "https://www.wixapis.com/stores/v1"
        self.api_key = api_key
        self.site_id = site_id
        self.headers = {
            'Authorization': api_key,
            'wix-site-id': site_id,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> Dict:
        """Test API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                headers=self.headers,
                params={'limit': 1},
                timeout=30
            )
            if response.status_code == 200:
                return {"status": "success", "message": "Conexión exitosa a Wix"}
            elif response.status_code == 401:
                return {"status": "error", "message": "API Key o Site ID inválidos"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Error de conexión: {str(e)}"}
    
    def get_products(self, limit: int = 50) -> List[Dict]:
        """Get products from Wix"""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                headers=self.headers,
                params={'limit': limit},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('products', [])
            return []
        except Exception as e:
            logger.error(f"Wix get_products error: {e}")
            return []
    
    def update_inventory(self, product_id: str, variant_id: str, quantity: int) -> Dict:
        """Update inventory for a product variant"""
        try:
            response = requests.post(
                f"{self.base_url}/inventoryItems/updateInventoryVariants",
                headers=self.headers,
                json={
                    'inventoryItem': {
                        'productId': product_id,
                        'variants': [{
                            'variantId': variant_id,
                            'quantity': quantity,
                            'inStock': quantity > 0
                        }]
                    }
                },
                timeout=30
            )
            if response.status_code in [200, 201]:
                return {"status": "success", "message": f"Inventario actualizado: {quantity}"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product in Wix"""
        try:
            payload = {
                'product': {
                    'name': product_data.get('name', ''),
                    'productType': 'physical',
                    'priceData': {
                        'price': product_data.get('price', 0)
                    },
                    'sku': product_data.get('sku', ''),
                    'visible': True,
                    'manageVariants': False
                }
            }
            
            response = requests.post(
                f"{self.base_url}/products",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                product = response.json().get('product', {})
                return {"status": "success", "product_id": product.get('id'), "message": "Producto creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}


# ==================== FACTORY FUNCTION ====================

def get_platform_client(config: Dict):
    """Factory function to get the appropriate platform client"""
    platform = config.get('platform', 'woocommerce')
    
    if platform == 'prestashop':
        return PrestaShopClient(
            store_url=config.get('store_url', ''),
            api_key=config.get('api_key', '')
        )
    elif platform == 'shopify':
        return ShopifyClient(
            store_url=config.get('store_url', ''),
            access_token=config.get('access_token', ''),
            api_version=config.get('api_version', '2024-10')
        )
    elif platform == 'magento':
        return MagentoClient(
            store_url=config.get('store_url', ''),
            access_token=config.get('access_token', ''),
            store_code=config.get('store_code', 'default')
        )
    elif platform == 'wix':
        return WixClient(
            store_url=config.get('store_url', ''),
            api_key=config.get('api_key', ''),
            site_id=config.get('site_id', '')
        )
    else:
        # WooCommerce - return None to use existing implementation
        return None
