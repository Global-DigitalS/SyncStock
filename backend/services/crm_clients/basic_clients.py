"""
Basic CRM clients: HubSpot, Salesforce, Zoho, Pipedrive, Monday, Freshsales.
"""
import logging

import requests

from .base import _validate_crm_url

logger = logging.getLogger(__name__)


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

    def test_connection(self) -> dict:
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

    def get_products(self, limit: int = 500) -> list[dict]:
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

    def get_product_by_sku(self, sku: str) -> dict | None:
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

    def create_product(self, product_data: dict) -> dict | None:
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

    def update_product(self, product_id: str, product_data: dict) -> bool:
        try:
            response = self._rate_limited_request(
                'PATCH', f"{self.base_url}/crm/v3/objects/products/{product_id}",
                json={'properties': product_data}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HubSpot update_product error: {e}")
            return False

    def get_stats(self) -> dict:
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

    def test_connection(self) -> dict:
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

    def get_products(self, limit: int = 500) -> list[dict]:
        try:
            query = f"SELECT Id, Name, ProductCode, Description, IsActive FROM Product2 WHERE IsActive = true LIMIT {limit}"
            response = self._rate_limited_request('GET', f"{self.base_url}/services/data/v59.0/query", params={'q': query})
            if response.status_code == 200:
                return response.json().get('records', [])
            return []
        except Exception as e:
            logger.error(f"Salesforce get_products error: {e}")
            return []

    def get_product_by_sku(self, sku: str) -> dict | None:
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

    def create_product(self, product_data: dict) -> dict | None:
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

    def update_product(self, product_id: str, product_data: dict) -> bool:
        try:
            response = self._rate_limited_request(
                'PATCH', f"{self.base_url}/services/data/v59.0/sobjects/Product2/{product_id}",
                json=product_data
            )
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Salesforce update_product error: {e}")
            return False

    def get_stats(self) -> dict:
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

    def test_connection(self) -> dict:
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

    def get_products(self, limit: int = 500) -> list[dict]:
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

    def get_product_by_sku(self, sku: str) -> dict | None:
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

    def create_product(self, product_data: dict) -> dict | None:
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

    def update_product(self, product_id: str, product_data: dict) -> bool:
        try:
            response = self._rate_limited_request(
                'PUT', f"{self.base_url}/crm/v6/Products/{product_id}",
                json={'data': [product_data]}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Zoho update_product error: {e}")
            return False

    def get_stats(self) -> dict:
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

    def test_connection(self) -> dict:
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

    def get_products(self, limit: int = 500) -> list[dict]:
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

    def get_product_by_sku(self, sku: str) -> dict | None:
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

    def create_product(self, product_data: dict) -> dict | None:
        try:
            response = self._rate_limited_request('POST', f"{self.base_url}/api/v1/products", json=product_data)
            if response.status_code in [200, 201] and response.json().get('success'):
                return response.json().get('data')
            return None
        except Exception as e:
            logger.error(f"Pipedrive create_product error: {e}")
            return None

    def update_product(self, product_id: str, product_data: dict) -> bool:
        try:
            response = self._rate_limited_request('PUT', f"{self.base_url}/api/v1/products/{product_id}", json=product_data)
            return response.status_code == 200 and response.json().get('success')
        except Exception as e:
            logger.error(f"Pipedrive update_product error: {e}")
            return False

    def get_stats(self) -> dict:
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

    def _rate_limited_request(self, query: str, variables: dict = None) -> dict:
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

    def test_connection(self) -> dict:
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

    def get_products(self, limit: int = 500) -> list[dict]:
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

    def get_product_by_sku(self, sku: str) -> dict | None:
        products = self.get_products(limit=500)
        for item in products:
            for col in item.get('column_values', []):
                if col.get('text') == sku:
                    return item
        return None

    def create_product(self, product_data: dict) -> dict | None:
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

    def update_product(self, item_id: str, product_data: dict) -> bool:
        try:
            columns = product_data.get('column_values', '{}')
            query = 'mutation ($boardId: ID!, $itemId: ID!, $columnValues: JSON) { change_multiple_column_values(board_id: $boardId, item_id: $itemId, column_values: $columnValues) { id } }'
            result = self._rate_limited_request(query, {'boardId': self.board_id, 'itemId': item_id, 'columnValues': columns})
            return bool(result.get('data', {}).get('change_multiple_column_values'))
        except Exception as e:
            logger.error(f"Monday update_product error: {e}")
            return False

    def get_stats(self) -> dict:
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

    def test_connection(self) -> dict:
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

    def get_products(self, limit: int = 500) -> list[dict]:
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

    def get_product_by_sku(self, sku: str) -> dict | None:
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

    def create_product(self, product_data: dict) -> dict | None:
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

    def update_product(self, product_id: str, product_data: dict) -> bool:
        try:
            response = self._rate_limited_request(
                'PUT', f"{self.base_url}/api/cpq/products/{product_id}",
                json={'product': product_data}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Freshsales update_product error: {e}")
            return False

    def get_stats(self) -> dict:
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
