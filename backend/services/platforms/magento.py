"""
Magento 2 REST API Integration
"""
import base64
import logging

import requests

logger = logging.getLogger(__name__)


class MagentoClient:
    """Magento 2 REST API Client"""

    def __init__(self, store_url: str, access_token: str, store_code: str = "default"):
        self.base_url = store_url.rstrip('/') + f'/rest/{store_code}/V1'
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

    def test_connection(self) -> dict:
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

    def get_products(self, limit: int = 50) -> list[dict]:
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

    def get_all_products(self, page_size: int = 100) -> list[dict]:
        """Get all products from Magento with pagination"""
        all_products = []
        page = 1
        try:
            while True:
                response = requests.get(
                    f"{self.base_url}/products",
                    headers=self.headers,
                    params={
                        'searchCriteria[pageSize]': page_size,
                        'searchCriteria[currentPage]': page
                    },
                    timeout=60
                )
                if response.status_code != 200:
                    break
                data = response.json()
                products = data.get('items', [])
                if not products:
                    break
                all_products.extend(products)
                total = data.get('total_count', 0)
                if len(all_products) >= total:
                    break
                page += 1
        except Exception as e:
            logger.error(f"Magento get_all_products error: {e}")
        return all_products

    def get_stock(self, sku: str) -> dict | None:
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

    def update_stock(self, sku: str, quantity: int, is_in_stock: bool = True) -> dict:
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

    def create_product(self, product_data: dict) -> dict:
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

    def _upload_product_images(self, sku: str, product_data: dict) -> None:
        """Upload images to a Magento product"""
        try:
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

    def update_product(self, sku: str, product_data: dict) -> dict:
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
