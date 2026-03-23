"""
Shopify Admin API Integration
"""
import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


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
