"""
PrestaShop Webservice API Integration
"""
import logging
import re

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


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

    def test_connection(self) -> dict:
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

    def get_products(self, limit: int = 100) -> list[dict]:
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

    def get_all_products(self, page_size: int = 100) -> list[dict]:
        """Get all products from PrestaShop with pagination"""
        all_products = []
        offset = 0
        try:
            while True:
                response = requests.get(
                    f"{self.base_url}/products",
                    auth=self.auth,
                    headers=self.headers,
                    params={
                        'output_format': 'JSON',
                        'display': '[id,reference,name,price,active,ean13]',
                        'limit': f'{offset},{page_size}'
                    },
                    timeout=60
                )
                if response.status_code != 200:
                    break
                products = response.json().get('products', [])
                if not products:
                    break
                all_products.extend(products)
                offset += page_size
                if len(products) < page_size:
                    break
        except Exception as e:
            logger.error(f"PrestaShop get_all_products error: {e}")
        return all_products

    def get_stock_available(self, product_id: int, combination_id: int = 0) -> dict | None:
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

    def update_stock(self, stock_id: int, quantity: int) -> dict:
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

    def create_product(self, product_data: dict) -> dict:
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

    def _upload_product_images(self, product_id: str, product_data: dict) -> None:
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

    def update_product(self, product_id: int, product_data: dict) -> dict:
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

    def get_categories(self) -> list[dict]:
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

    def create_category(self, category_data: dict) -> dict:
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
                match = re.search(r'<id><!\[CDATA\[(\d+)\]\]></id>', response.text)
                category_id = match.group(1) if match else None
                return {"status": "success", "message": "Categoría creada", "category_id": category_id}
            else:
                return {"status": "error", "message": f"Error: {response.status_code}", "response": response.text[:200]}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}

    def find_or_create_category(self, name: str, parent_id: int = 2) -> int | None:
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

    # ==================== SYNC RESOLUTION METHODS ====================

    def count_products(self) -> int:
        """Return total number of products in the store."""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                auth=self.auth,
                headers=self.headers,
                params={
                    'output_format': 'JSON',
                    'display': '[id]',
                    'limit': '1,1',
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                # Fallback: use a head request on page 1 to detect if there are any
                return len(products) if products is None else (1 if products else 0)
            # Alternative: get first page and check X-Total-Count header
            response2 = requests.get(
                f"{self.base_url}/products",
                auth=self.auth,
                headers=self.headers,
                params={'output_format': 'JSON', 'display': '[id]', 'limit': '0,1'},
                timeout=30
            )
            if response2.status_code == 200:
                return len(response2.json().get('products', []))
            return 0
        except Exception as e:
            logger.error(f"PrestaShop count_products error: {e}")
            return 0

    def has_products(self) -> bool:
        """Return True if store has at least one product."""
        try:
            response = requests.get(
                f"{self.base_url}/products",
                auth=self.auth,
                headers=self.headers,
                params={'output_format': 'JSON', 'display': '[id]', 'limit': '1'},
                timeout=30
            )
            if response.status_code == 200:
                return bool(response.json().get('products'))
            return False
        except Exception as e:
            logger.error(f"PrestaShop has_products error: {e}")
            return False

    def find_by_ean(self, ean: str) -> str | None:
        """Find product ID by EAN13. Returns product id string or None."""
        if not ean:
            return None
        try:
            response = requests.get(
                f"{self.base_url}/products",
                auth=self.auth,
                headers=self.headers,
                params={
                    'output_format': 'JSON',
                    'display': '[id,ean13]',
                    'filter[ean13]': ean,
                    'limit': '1',
                },
                timeout=30
            )
            if response.status_code == 200:
                products = response.json().get('products', [])
                if products:
                    return str(products[0].get('id'))
            return None
        except Exception as e:
            logger.error(f"PrestaShop find_by_ean error: {e}")
            return None

    def find_by_sku(self, sku: str) -> str | None:
        """Find product ID by reference (SKU). Returns product id string or None."""
        if not sku:
            return None
        try:
            response = requests.get(
                f"{self.base_url}/products",
                auth=self.auth,
                headers=self.headers,
                params={
                    'output_format': 'JSON',
                    'display': '[id,reference]',
                    'filter[reference]': sku,
                    'limit': '1',
                },
                timeout=30
            )
            if response.status_code == 200:
                products = response.json().get('products', [])
                if products:
                    return str(products[0].get('id'))
            return None
        except Exception as e:
            logger.error(f"PrestaShop find_by_sku error: {e}")
            return None

    def update_price_stock(self, product_id: str, price: float, stock: int) -> dict:
        """Update only price and stock of an existing product (no other fields changed)."""
        try:
            pid = int(product_id)
            # Update price via product PUT
            price_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
            <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
                <product>
                    <id>{pid}</id>
                    <price>{round(price, 6)}</price>
                </product>
            </prestashop>'''

            r_price = requests.put(
                f"{self.base_url}/products/{pid}",
                auth=self.auth,
                headers={'Content-Type': 'application/xml'},
                data=price_xml.encode('utf-8'),
                timeout=30
            )
            if r_price.status_code not in [200, 201]:
                return {"status": "error", "message": f"Error actualizando precio: {r_price.status_code}"}

            # Update stock via stock_availables
            stock_info = self.get_stock_available(pid)
            if stock_info:
                stock_id = stock_info.get('id')
                if stock_id:
                    r_stock = self.update_stock(int(stock_id), stock)
                    if r_stock.get("status") != "success":
                        return {"status": "error", "message": f"Precio OK, error en stock: {r_stock.get('message', '')}"}

            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def create_draft_product(self, product_data: dict) -> dict:
        """Create a product in draft state (active=0) with all available data."""
        try:
            short_desc = product_data.get("short_description", "")
            long_desc = product_data.get("long_description", "") or product_data.get("description", "")
            category_id = product_data.get("category_id", 2)

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
                    <active>0</active>
                    <state>0</state>
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
                match = re.search(r'<id><!\[CDATA\[(\d+)\]\]></id>', response.text)
                product_id = match.group(1) if match else None
                if product_id:
                    self._upload_product_images(product_id, product_data)
                return {"status": "success", "product_id": product_id}
            return {"status": "error", "message": f"Error: {response.status_code}", "response": response.text[:300]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            return None
