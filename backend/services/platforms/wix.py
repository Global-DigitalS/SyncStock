"""
Wix eCommerce API Integration
"""
import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


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
