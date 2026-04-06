"""
Backend API Tests for Refactored Modular Architecture
Tests: Auth, Dashboard, Catalogs, WooCommerce, Notifications, Suppliers, Products
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"
TEST_USER_EMAIL = f"TEST_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "TestPass123!"


class TestHealthEndpoint:
    """Health check tests"""

    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        print("✓ Health endpoint working")


class TestAuthEndpoints:
    """Authentication endpoint tests"""

    def test_register_new_user(self):
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Test User API",
            "company": "Test Company"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_USER_EMAIL
        print(f"✓ Register endpoint working - created {TEST_USER_EMAIL}")

    def test_login_existing_user(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
        print("✓ Login endpoint working")

    def test_login_invalid_credentials(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✓ Login returns 401 for invalid credentials")

    def test_register_duplicate_email(self):
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": "anypassword",
            "name": "Duplicate User"
        })
        assert response.status_code == 400
        print("✓ Register returns 400 for duplicate email")


class TestAuthenticatedEndpoints:
    """Tests requiring authentication"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed")

    def test_get_me(self):
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert "id" in data
        assert "name" in data
        print("✓ GET /api/auth/me working")


class TestDashboardEndpoints:
    """Dashboard endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed")

    def test_dashboard_stats(self):
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200
        data = response.json()

        # Check all expected fields exist
        expected_fields = [
            "total_suppliers", "total_products", "total_catalog_items",
            "total_catalogs", "low_stock_count", "out_of_stock_count",
            "unread_notifications", "recent_price_changes",
            "woocommerce_stores", "woocommerce_connected",
            "woocommerce_auto_sync", "woocommerce_total_synced"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        print("✓ Dashboard stats endpoint returns all WooCommerce fields")

    def test_dashboard_sync_status(self):
        response = requests.get(f"{BASE_URL}/api/dashboard/sync-status", headers=self.headers)
        assert response.status_code == 200
        data = response.json()

        # Should contain suppliers and woocommerce_stores
        assert "suppliers" in data
        assert "woocommerce_stores" in data
        assert isinstance(data["suppliers"], list)
        assert isinstance(data["woocommerce_stores"], list)
        print("✓ Dashboard sync-status returns suppliers and woocommerce_stores")

    def test_stock_alerts(self):
        response = requests.get(f"{BASE_URL}/api/dashboard/stock-alerts", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "low_stock" in data
        assert "out_of_stock" in data
        print("✓ Dashboard stock-alerts endpoint working")


class TestCatalogsEndpoints:
    """Catalogs CRUD tests"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            self.catalog_id = None
        else:
            pytest.skip("Authentication failed")

    def test_01_get_catalogs_list(self):
        response = requests.get(f"{BASE_URL}/api/catalogs", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/catalogs returns {len(data)} catalogs")

    def test_02_create_catalog(self):
        catalog_name = f"TEST_Catalog_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/catalogs", headers=self.headers, json={
            "name": catalog_name,
            "description": "Test catalog description",
            "is_default": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == catalog_name
        assert "id" in data
        assert "product_count" in data
        assert "margin_rules_count" in data

        # Store for cleanup
        self.__class__.test_catalog_id = data["id"]
        print(f"✓ POST /api/catalogs creates catalog: {catalog_name}")

    def test_03_get_catalog_by_id(self):
        catalog_id = getattr(self.__class__, 'test_catalog_id', None)
        if not catalog_id:
            pytest.skip("No catalog created")

        response = requests.get(f"{BASE_URL}/api/catalogs/{catalog_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == catalog_id
        print("✓ GET /api/catalogs/{id} returns specific catalog")

    def test_04_catalog_margin_rules_create(self):
        catalog_id = getattr(self.__class__, 'test_catalog_id', None)
        if not catalog_id:
            pytest.skip("No catalog created")

        response = requests.post(f"{BASE_URL}/api/catalogs/{catalog_id}/margin-rules",
            headers=self.headers, json={
                "catalog_id": catalog_id,
                "name": "TEST_Rule",
                "rule_type": "percentage",
                "value": 10.0,
                "apply_to": "all",
                "priority": 1
            })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Rule"
        assert data["value"] == 10.0
        self.__class__.test_rule_id = data["id"]
        print("✓ POST /api/catalogs/{id}/margin-rules creates rule")

    def test_05_catalog_margin_rules_list(self):
        catalog_id = getattr(self.__class__, 'test_catalog_id', None)
        if not catalog_id:
            pytest.skip("No catalog created")

        response = requests.get(f"{BASE_URL}/api/catalogs/{catalog_id}/margin-rules",
            headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/catalogs/{catalog_id}/margin-rules returns {len(data)} rules")

    def test_06_catalog_margin_rules_delete(self):
        catalog_id = getattr(self.__class__, 'test_catalog_id', None)
        rule_id = getattr(self.__class__, 'test_rule_id', None)
        if not catalog_id or not rule_id:
            pytest.skip("No catalog or rule created")

        response = requests.delete(f"{BASE_URL}/api/catalogs/{catalog_id}/margin-rules/{rule_id}",
            headers=self.headers)
        assert response.status_code == 200
        print("✓ DELETE /api/catalogs/{id}/margin-rules/{rule_id} works")

    def test_07_delete_catalog(self):
        catalog_id = getattr(self.__class__, 'test_catalog_id', None)
        if not catalog_id:
            pytest.skip("No catalog created")

        response = requests.delete(f"{BASE_URL}/api/catalogs/{catalog_id}", headers=self.headers)
        assert response.status_code == 200
        print("✓ DELETE /api/catalogs/{id} works")

    def test_08_catalog_not_found(self):
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/catalogs/{fake_id}", headers=self.headers)
        assert response.status_code == 404
        print("✓ GET non-existent catalog returns 404")

    def test_09_create_catalog_validation(self):
        # Missing name should fail
        response = requests.post(f"{BASE_URL}/api/catalogs", headers=self.headers, json={
            "description": "No name catalog"
        })
        assert response.status_code == 422
        print("✓ POST /api/catalogs without name returns 422")


class TestWooCommerceEndpoints:
    """WooCommerce config tests"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed")

    def test_01_get_woocommerce_configs(self):
        response = requests.get(f"{BASE_URL}/api/woocommerce/configs", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/woocommerce/configs returns {len(data)} configs")

    def test_02_create_woocommerce_config(self):
        response = requests.post(f"{BASE_URL}/api/woocommerce/configs", headers=self.headers, json={
            "name": f"TEST_Store_{uuid.uuid4().hex[:6]}",
            "store_url": "https://test-store.example.com",
            "consumer_key": "ck_test123",
            "consumer_secret": "cs_test456",
            "catalog_id": None,
            "auto_sync_enabled": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["auto_sync_enabled"] == True
        assert "consumer_key_masked" in data
        self.__class__.test_wc_id = data["id"]
        print("✓ POST /api/woocommerce/configs creates config with catalog_id and auto_sync_enabled")

    def test_03_get_woocommerce_config_by_id(self):
        config_id = getattr(self.__class__, 'test_wc_id', None)
        if not config_id:
            pytest.skip("No WooCommerce config created")

        response = requests.get(f"{BASE_URL}/api/woocommerce/configs/{config_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == config_id
        print("✓ GET /api/woocommerce/configs/{id} works")

    def test_04_sync_without_catalog(self):
        config_id = getattr(self.__class__, 'test_wc_id', None)
        if not config_id:
            pytest.skip("No WooCommerce config created")

        response = requests.post(f"{BASE_URL}/api/woocommerce/configs/{config_id}/sync", headers=self.headers)
        assert response.status_code == 400
        data = response.json()
        assert "catálogo" in data.get("detail", "").lower() or "catalog" in data.get("detail", "").lower()
        print("✓ POST /api/woocommerce/configs/{id}/sync returns 400 when no catalog")

    def test_05_update_woocommerce_config(self):
        config_id = getattr(self.__class__, 'test_wc_id', None)
        if not config_id:
            pytest.skip("No WooCommerce config created")

        response = requests.put(f"{BASE_URL}/api/woocommerce/configs/{config_id}",
            headers=self.headers, json={
                "name": "Updated Store Name",
                "auto_sync_enabled": False
            })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Store Name"
        assert data["auto_sync_enabled"] == False
        print("✓ PUT /api/woocommerce/configs/{id} updates config")

    def test_06_delete_woocommerce_config(self):
        config_id = getattr(self.__class__, 'test_wc_id', None)
        if not config_id:
            pytest.skip("No WooCommerce config created")

        response = requests.delete(f"{BASE_URL}/api/woocommerce/configs/{config_id}", headers=self.headers)
        assert response.status_code == 200
        print("✓ DELETE /api/woocommerce/configs/{id} works")


class TestNotificationsEndpoints:
    """Notifications endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed")

    def test_get_notifications(self):
        response = requests.get(f"{BASE_URL}/api/notifications", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/notifications returns {len(data)} notifications")

    def test_get_unread_notifications(self):
        response = requests.get(f"{BASE_URL}/api/notifications?unread_only=true", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All should be unread
        for notif in data:
            assert notif["read"] == False
        print(f"✓ GET /api/notifications?unread_only=true returns {len(data)} unread")

    def test_mark_all_read(self):
        response = requests.put(f"{BASE_URL}/api/notifications/read-all", headers=self.headers)
        assert response.status_code == 200
        print("✓ PUT /api/notifications/read-all works")


class TestSuppliersEndpoints:
    """Suppliers CRUD tests"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed")

    def test_01_get_suppliers(self):
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/suppliers returns {len(data)} suppliers")

    def test_02_create_supplier(self):
        supplier_name = f"TEST_Supplier_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/suppliers", headers=self.headers, json={
            "name": supplier_name,
            "description": "Test supplier",
            "connection_type": "url",
            "file_url": "https://example.com/products.csv",
            "file_format": "csv"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == supplier_name
        assert "id" in data
        self.__class__.test_supplier_id = data["id"]
        print(f"✓ POST /api/suppliers creates supplier: {supplier_name}")

    def test_03_get_supplier_by_id(self):
        supplier_id = getattr(self.__class__, 'test_supplier_id', None)
        if not supplier_id:
            pytest.skip("No supplier created")

        response = requests.get(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == supplier_id
        print("✓ GET /api/suppliers/{id} works")

    def test_04_update_supplier(self):
        supplier_id = getattr(self.__class__, 'test_supplier_id', None)
        if not supplier_id:
            pytest.skip("No supplier created")

        response = requests.put(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=self.headers, json={
            "name": "Updated Supplier Name"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Supplier Name"
        print("✓ PUT /api/suppliers/{id} works")

    def test_05_delete_supplier(self):
        supplier_id = getattr(self.__class__, 'test_supplier_id', None)
        if not supplier_id:
            pytest.skip("No supplier created")

        response = requests.delete(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=self.headers)
        assert response.status_code == 200
        print("✓ DELETE /api/suppliers/{id} works")


class TestProductsEndpoints:
    """Products endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed")

    def test_get_products(self):
        response = requests.get(f"{BASE_URL}/api/products", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/products returns {len(data)} products")

    def test_get_categories(self):
        response = requests.get(f"{BASE_URL}/api/products/categories", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/products/categories returns {len(data)} categories")

    def test_get_unified_products(self):
        response = requests.get(f"{BASE_URL}/api/products-unified", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/products-unified returns {len(data)} unified products")


class TestPriceHistory:
    """Price history tests"""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if login_response.status_code == 200:
            self.token = login_response.json()["token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            pytest.skip("Authentication failed")

    def test_get_price_history(self):
        response = requests.get(f"{BASE_URL}/api/price-history", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/price-history returns {len(data)} records")


class TestUnauthorizedAccess:
    """Tests for unauthorized access"""

    def test_dashboard_without_auth(self):
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code in [401, 403]
        print("✓ Dashboard requires authentication")

    def test_catalogs_without_auth(self):
        response = requests.get(f"{BASE_URL}/api/catalogs")
        assert response.status_code in [401, 403]
        print("✓ Catalogs require authentication")

    def test_suppliers_without_auth(self):
        response = requests.get(f"{BASE_URL}/api/suppliers")
        assert response.status_code in [401, 403]
        print("✓ Suppliers require authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
