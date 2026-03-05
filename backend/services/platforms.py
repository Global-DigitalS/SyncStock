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
        self._category_map = {}  # Cache for category id mapping
    
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
        """Create a new product in PrestaShop with full product data"""
        try:
            # Build description combining short and long
            short_desc = product_data.get("short_description", "")
            long_desc = product_data.get("long_description", "") or product_data.get("description", "")
            
            # Category
            category_id = product_data.get("category_id", 2)  # Default to Home
            
            # PrestaShop requires XML format
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <product>
                    <reference><![CDATA[{product_data.get("sku", "")}]]></reference>
                    <ean13><![CDATA[{product_data.get("ean", "")}]]></ean13>
                    <name><language id="1"><![CDATA[{product_data.get("name", "")}]]></language></name>
                    <description><language id="1"><![CDATA[{long_desc}]]></language></description>
                    <description_short><language id="1"><![CDATA[{short_desc}]]></language></description_short>
                    <price>{product_data.get("price", 0)}</price>
                    <weight>{product_data.get("weight", 0)}</weight>
                    <active>1</active>
                    <state>1</state>
                    <id_category_default>{category_id}</id_category_default>
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
                # Extract product ID from response
                import re
                match = re.search(r'<id><!\[CDATA\[(\d+)\]\]></id>', response.text)
                product_id = match.group(1) if match else None
                
                # Upload images if product was created
                if product_id:
                    self._upload_product_images(product_id, product_data)
                
                return {"status": "success", "message": "Producto creado", "product_id": product_id}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}", "response": response.text[:500]}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def _upload_product_images(self, product_id: str, product_data: Dict) -> None:
        """Upload images to a PrestaShop product"""
        try:
            images = []
            # Main image first
            if product_data.get("image_url"):
                images.append(product_data["image_url"])
            # Gallery images
            gallery = product_data.get("gallery_images") or []
            images.extend(gallery)
            
            for img_url in images:
                if not img_url:
                    continue
                try:
                    # Download image
                    img_response = requests.get(img_url, timeout=30)
                    if img_response.status_code == 200:
                        # Upload to PrestaShop
                        files = {'image': ('image.jpg', img_response.content, 'image/jpeg')}
                        upload_response = requests.post(
                            f"{self.base_url}/images/products/{product_id}",
                            auth=self.auth,
                            files=files,
                            timeout=60
                        )
                        if upload_response.status_code not in [200, 201]:
                            logger.warning(f"PrestaShop image upload failed: {upload_response.status_code}")
                except Exception as e:
                    logger.warning(f"PrestaShop image upload error: {e}")
        except Exception as e:
            logger.error(f"PrestaShop _upload_product_images error: {e}")
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """Update an existing product with full data"""
        try:
            # Build update fields
            update_parts = [f"<id>{product_id}</id>"]
            
            if "name" in product_data:
                update_parts.append(f'<name><language id="1"><![CDATA[{product_data["name"]}]]></language></name>')
            if "price" in product_data:
                update_parts.append(f'<price>{product_data["price"]}</price>')
            if "short_description" in product_data:
                update_parts.append(f'<description_short><language id="1"><![CDATA[{product_data["short_description"]}]]></language></description_short>')
            if "long_description" in product_data or "description" in product_data:
                desc = product_data.get("long_description") or product_data.get("description", "")
                update_parts.append(f'<description><language id="1"><![CDATA[{desc}]]></language></description>')
            if "weight" in product_data:
                update_parts.append(f'<weight>{product_data["weight"]}</weight>')
            if "ean" in product_data:
                update_parts.append(f'<ean13><![CDATA[{product_data["ean"]}]]></ean13>')
            
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <product>
                    {"".join(update_parts)}
                </product>
            </prestashop>'''
            
            response = requests.put(
                f"{self.base_url}/products/{product_id}",
                auth=self.auth,
                headers={'Content-Type': 'application/xml'},
                data=xml_data.encode('utf-8'),
                timeout=30
            )
            if response.status_code in [200, 201]:
                # Upload new images if provided
                if product_data.get("image_url") or product_data.get("gallery_images"):
                    self._upload_product_images(str(product_id), product_data)
                return {"status": "success", "message": "Producto actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    # ==================== CATEGORY METHODS ====================
    
    def get_categories(self) -> List[Dict]:
        """Get all categories from PrestaShop"""
        try:
            response = requests.get(
                f"{self.base_url}/categories",
                auth=self.auth,
                headers=self.headers,
                params={
                    'output_format': 'JSON',
                    'display': '[id,name,id_parent,level_depth,active]'
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('categories', [])
            return []
        except Exception as e:
            logger.error(f"PrestaShop get_categories error: {e}")
            return []
    
    def create_category(self, category_data: Dict) -> Dict:
        """Create a new category in PrestaShop"""
        try:
            parent_id = category_data.get("parent_id", 2)  # 2 is usually "Home" in PrestaShop
            name = category_data.get("name", "")
            
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <category>
                    <id_parent>{parent_id}</id_parent>
                    <active>1</active>
                    <name><language id="1"><![CDATA[{name}]]></language></name>
                    <link_rewrite><language id="1"><![CDATA[{name.lower().replace(" ", "-")}]]></language></link_rewrite>
                </category>
            </prestashop>'''
            
            response = requests.post(
                f"{self.base_url}/categories",
                auth=self.auth,
                headers={'Content-Type': 'application/xml'},
                data=xml_data.encode('utf-8'),
                timeout=30
            )
            if response.status_code in [200, 201]:
                # Extract category ID from response
                import re
                match = re.search(r'<id><!\[CDATA\[(\d+)\]\]></id>', response.text)
                category_id = match.group(1) if match else None
                return {"status": "success", "message": "Categoría creada", "category_id": category_id}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}", "response": response.text[:200]}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def find_or_create_category(self, name: str, parent_id: int = 2) -> Optional[int]:
        """Find existing category by name or create it"""
        try:
            # First, try to find existing category
            categories = self.get_categories()
            for cat in categories:
                cat_name = cat.get('name', '')
                if isinstance(cat_name, dict):
                    cat_name = cat_name.get('language', {})
                    if isinstance(cat_name, list):
                        cat_name = cat_name[0].get('value', '') if cat_name else ''
                    elif isinstance(cat_name, dict):
                        cat_name = cat_name.get('value', '')
                if cat_name.lower() == name.lower():
                    return int(cat.get('id'))
            
            # Create new category
            result = self.create_category({"name": name, "parent_id": parent_id})
            if result.get("status") == "success" and result.get("category_id"):
                return int(result["category_id"])
            return None
        except Exception as e:
            logger.error(f"PrestaShop find_or_create_category error: {e}")
            return None


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
        """Create a new product in Shopify with full product data"""
        try:
            # Build description - prefer long_description, fallback to description
            description = product_data.get('long_description') or product_data.get('description', '')
            
            # Build images array - main image first, then gallery
            images = []
            if product_data.get('image_url'):
                images.append({'src': product_data['image_url']})
            gallery = product_data.get('gallery_images') or []
            for img_url in gallery:
                if img_url:
                    images.append({'src': img_url})
            
            # Build metafields for short_description and brand
            metafields = []
            if product_data.get('short_description'):
                metafields.append({
                    'namespace': 'custom',
                    'key': 'short_description',
                    'value': product_data['short_description'],
                    'type': 'multi_line_text_field'
                })
            
            payload = {
                'product': {
                    'title': product_data.get('name', ''),
                    'body_html': description,
                    'vendor': product_data.get('brand', ''),
                    'product_type': product_data.get('category', ''),
                    'tags': product_data.get('brand', ''),  # Add brand as tag too
                    'variants': [{
                        'sku': product_data.get('sku', ''),
                        'price': str(product_data.get('price', 0)),
                        'inventory_management': 'shopify',
                        'barcode': product_data.get('ean', ''),
                        'weight': product_data.get('weight', 0),
                        'weight_unit': 'kg'
                    }],
                    'images': images,
                    'metafields': metafields if metafields else None
                }
            }
            
            # Remove None values
            payload['product'] = {k: v for k, v in payload['product'].items() if v is not None}
            
            response = requests.post(
                f"{self.base_url}/products.json",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            if response.status_code in [200, 201]:
                product = response.json().get('product', {})
                return {"status": "success", "product_id": product.get('id'), "message": "Producto creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def update_product(self, product_id: int, product_data: Dict) -> Dict:
        """Update an existing product with full data"""
        try:
            payload = {'product': {'id': product_id}}
            
            if 'name' in product_data:
                payload['product']['title'] = product_data['name']
            
            if 'long_description' in product_data or 'description' in product_data:
                desc = product_data.get('long_description') or product_data.get('description', '')
                payload['product']['body_html'] = desc
            
            if 'brand' in product_data:
                payload['product']['vendor'] = product_data['brand']
                payload['product']['tags'] = product_data['brand']
            
            if 'category' in product_data:
                payload['product']['product_type'] = product_data['category']
            
            # Handle variants update
            if 'price' in product_data or 'sku' in product_data or 'ean' in product_data or 'weight' in product_data:
                variant = {}
                if 'price' in product_data:
                    variant['price'] = str(product_data['price'])
                if 'sku' in product_data:
                    variant['sku'] = product_data['sku']
                if 'ean' in product_data:
                    variant['barcode'] = product_data['ean']
                if 'weight' in product_data:
                    variant['weight'] = product_data['weight']
                    variant['weight_unit'] = 'kg'
                payload['product']['variants'] = [variant]
            
            # Handle images update
            if product_data.get('image_url') or product_data.get('gallery_images'):
                images = []
                if product_data.get('image_url'):
                    images.append({'src': product_data['image_url']})
                gallery = product_data.get('gallery_images') or []
                for img_url in gallery:
                    if img_url:
                        images.append({'src': img_url})
                if images:
                    payload['product']['images'] = images
            
            response = requests.put(
                f"{self.base_url}/products/{product_id}.json",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                return {"status": "success", "message": "Producto actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    # ==================== CATEGORY (COLLECTION) METHODS ====================
    
    def get_collections(self) -> List[Dict]:
        """Get all custom collections (categories) from Shopify"""
        try:
            response = requests.get(
                f"{self.base_url}/custom_collections.json",
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('custom_collections', [])
            return []
        except Exception as e:
            logger.error(f"Shopify get_collections error: {e}")
            return []
    
    def create_collection(self, collection_data: Dict) -> Dict:
        """Create a new custom collection (category) in Shopify"""
        try:
            payload = {
                'custom_collection': {
                    'title': collection_data.get('name', ''),
                    'body_html': collection_data.get('description', ''),
                    'published': True
                }
            }
            
            response = requests.post(
                f"{self.base_url}/custom_collections.json",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                collection = response.json().get('custom_collection', {})
                return {"status": "success", "collection_id": collection.get('id'), "message": "Colección creada"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def find_or_create_collection(self, name: str) -> Optional[int]:
        """Find existing collection by name or create it"""
        try:
            # First, try to find existing collection
            collections = self.get_collections()
            for coll in collections:
                if coll.get('title', '').lower() == name.lower():
                    return int(coll.get('id'))
            
            # Create new collection
            result = self.create_collection({"name": name})
            if result.get("status") == "success" and result.get("collection_id"):
                return int(result["collection_id"])
            return None
        except Exception as e:
            logger.error(f"Shopify find_or_create_collection error: {e}")
            return None
    
    def add_product_to_collection(self, collection_id: int, product_id: int) -> Dict:
        """Add a product to a collection"""
        try:
            payload = {
                'collect': {
                    'collection_id': collection_id,
                    'product_id': product_id
                }
            }
            response = requests.post(
                f"{self.base_url}/collects.json",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Producto añadido a colección"}
            elif response.status_code == 422:
                # Already in collection
                return {"status": "success", "message": "Producto ya en colección"}
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
        """Create a new product in Magento with full product data"""
        try:
            # Build custom attributes
            custom_attributes = []
            
            # Short description
            if product_data.get('short_description'):
                custom_attributes.append({
                    'attribute_code': 'short_description',
                    'value': product_data['short_description']
                })
            
            # Long description
            if product_data.get('long_description') or product_data.get('description'):
                custom_attributes.append({
                    'attribute_code': 'description',
                    'value': product_data.get('long_description') or product_data.get('description', '')
                })
            
            # EAN/Barcode
            if product_data.get('ean'):
                custom_attributes.append({
                    'attribute_code': 'barcode',
                    'value': product_data['ean']
                })
            
            # Brand/Manufacturer
            if product_data.get('brand'):
                custom_attributes.append({
                    'attribute_code': 'manufacturer',
                    'value': product_data['brand']
                })
            
            payload = {
                'product': {
                    'sku': product_data.get('sku', ''),
                    'name': product_data.get('name', ''),
                    'price': product_data.get('price', 0),
                    'status': 1,  # Enabled
                    'visibility': 4,  # Catalog, Search
                    'type_id': 'simple',
                    'attribute_set_id': 4,  # Default
                    'weight': product_data.get('weight', 0),
                    'extension_attributes': {
                        'stock_item': {
                            'qty': product_data.get('stock', 0),
                            'is_in_stock': product_data.get('stock', 0) > 0
                        }
                    },
                    'custom_attributes': custom_attributes
                }
            }
            
            response = requests.post(
                f"{self.base_url}/products",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code in [200, 201]:
                result = response.json()
                sku = result.get('sku', product_data.get('sku'))
                
                # Upload images after product creation
                if product_data.get('image_url') or product_data.get('gallery_images'):
                    self._upload_product_images(sku, product_data)
                
                return {"status": "success", "message": "Producto creado", "sku": sku}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def _upload_product_images(self, sku: str, product_data: Dict) -> None:
        """Upload images to a Magento product"""
        try:
            import base64
            
            images = []
            # Main image first
            if product_data.get("image_url"):
                images.append(("image", product_data["image_url"]))
            # Gallery images
            gallery = product_data.get("gallery_images") or []
            for idx, img_url in enumerate(gallery):
                if img_url:
                    images.append((f"gallery_{idx}", img_url))
            
            for position, (label, img_url) in enumerate(images):
                try:
                    # Download image
                    img_response = requests.get(img_url, timeout=30)
                    if img_response.status_code == 200:
                        # Encode to base64
                        img_base64 = base64.b64encode(img_response.content).decode('utf-8')
                        
                        # Determine content type
                        content_type = img_response.headers.get('content-type', 'image/jpeg')
                        if 'png' in content_type:
                            media_type = 'image/png'
                        elif 'gif' in content_type:
                            media_type = 'image/gif'
                        else:
                            media_type = 'image/jpeg'
                        
                        # Upload to Magento
                        media_payload = {
                            'entry': {
                                'media_type': 'image',
                                'label': label,
                                'position': position,
                                'disabled': False,
                                'types': ['image', 'small_image', 'thumbnail'] if position == 0 else [],
                                'content': {
                                    'base64_encoded_data': img_base64,
                                    'type': media_type,
                                    'name': f'{sku}_{label}.jpg'
                                }
                            }
                        }
                        
                        upload_response = requests.post(
                            f"{self.base_url}/products/{sku}/media",
                            headers=self.headers,
                            json=media_payload,
                            timeout=60
                        )
                        if upload_response.status_code not in [200, 201]:
                            logger.warning(f"Magento image upload failed: {upload_response.status_code}")
                except Exception as e:
                    logger.warning(f"Magento image upload error: {e}")
        except Exception as e:
            logger.error(f"Magento _upload_product_images error: {e}")
    
    def update_product(self, sku: str, product_data: Dict) -> Dict:
        """Update an existing product with full data"""
        try:
            payload = {'product': {'sku': sku}}
            custom_attributes = []
            
            if 'name' in product_data:
                payload['product']['name'] = product_data['name']
            if 'price' in product_data:
                payload['product']['price'] = product_data['price']
            if 'weight' in product_data:
                payload['product']['weight'] = product_data['weight']
            
            # Short description
            if 'short_description' in product_data:
                custom_attributes.append({
                    'attribute_code': 'short_description',
                    'value': product_data['short_description']
                })
            
            # Long description
            if 'long_description' in product_data or 'description' in product_data:
                custom_attributes.append({
                    'attribute_code': 'description',
                    'value': product_data.get('long_description') or product_data.get('description', '')
                })
            
            # Brand
            if 'brand' in product_data:
                custom_attributes.append({
                    'attribute_code': 'manufacturer',
                    'value': product_data['brand']
                })
            
            if custom_attributes:
                payload['product']['custom_attributes'] = custom_attributes
            
            response = requests.put(
                f"{self.base_url}/products/{sku}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                # Upload new images if provided
                if product_data.get('image_url') or product_data.get('gallery_images'):
                    self._upload_product_images(sku, product_data)
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
        """Create a new product in Wix with full product data"""
        try:
            # Build description - prefer long_description
            description = product_data.get('long_description') or product_data.get('description', '')
            
            # Build media array for images
            media = []
            if product_data.get('image_url'):
                media.append({
                    'url': product_data['image_url'],
                    'mediaType': 'IMAGE'
                })
            gallery = product_data.get('gallery_images') or []
            for img_url in gallery:
                if img_url:
                    media.append({
                        'url': img_url,
                        'mediaType': 'IMAGE'
                    })
            
            payload = {
                'product': {
                    'name': product_data.get('name', ''),
                    'description': description,
                    'productType': 'physical',
                    'priceData': {
                        'price': product_data.get('price', 0)
                    },
                    'sku': product_data.get('sku', ''),
                    'visible': True,
                    'manageVariants': False,
                    'weight': product_data.get('weight', 0),
                    'brand': product_data.get('brand', ''),
                    'media': {'items': media} if media else None,
                    'additionalInfoSections': []
                }
            }
            
            # Add short description as additional info section
            if product_data.get('short_description'):
                payload['product']['additionalInfoSections'].append({
                    'title': 'Resumen',
                    'description': product_data['short_description']
                })
            
            # Clean None values
            payload['product'] = {k: v for k, v in payload['product'].items() if v is not None}
            
            response = requests.post(
                f"{self.base_url}/products",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            if response.status_code in [200, 201]:
                product = response.json().get('product', {})
                return {"status": "success", "product_id": product.get('id'), "message": "Producto creado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """Update an existing product with full data"""
        try:
            payload = {'product': {'id': product_id}}
            
            if 'name' in product_data:
                payload['product']['name'] = product_data['name']
            
            if 'long_description' in product_data or 'description' in product_data:
                payload['product']['description'] = product_data.get('long_description') or product_data.get('description', '')
            
            if 'price' in product_data:
                payload['product']['priceData'] = {'price': product_data['price']}
            
            if 'brand' in product_data:
                payload['product']['brand'] = product_data['brand']
            
            if 'weight' in product_data:
                payload['product']['weight'] = product_data['weight']
            
            # Handle images
            if product_data.get('image_url') or product_data.get('gallery_images'):
                media = []
                if product_data.get('image_url'):
                    media.append({'url': product_data['image_url'], 'mediaType': 'IMAGE'})
                gallery = product_data.get('gallery_images') or []
                for img_url in gallery:
                    if img_url:
                        media.append({'url': img_url, 'mediaType': 'IMAGE'})
                if media:
                    payload['product']['media'] = {'items': media}
            
            response = requests.patch(
                f"{self.base_url}/products/{product_id}",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Producto actualizado"}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}"}
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
