"""
Test stores multi-platform API endpoints
Tests for: GET /api/stores/configs, POST /api/stores/configs
Tests all 5 platforms: WooCommerce, PrestaShop, Shopify, Wix, Magento
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER = {"email": "test@test.com", "password": "test123"}


class TestStoresMultiplatform:
    """Test stores multi-platform API"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_USER
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def created_stores(self):
        """Track created stores for cleanup"""
        return []
    
    def test_get_stores_configs_empty(self, auth_headers):
        """Test GET /api/stores/configs - should return list"""
        response = requests.get(
            f"{BASE_URL}/api/stores/configs",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/stores/configs returned {len(data)} stores")
    
    def test_create_woocommerce_store(self, auth_headers, created_stores):
        """Test creating a WooCommerce store"""
        store_data = {
            "name": "TEST_WooCommerce_Store",
            "platform": "woocommerce",
            "store_url": "https://test-woocommerce.example.com",
            "consumer_key": "ck_test123456789",
            "consumer_secret": "cs_test987654321"
        }
        response = requests.post(
            f"{BASE_URL}/api/stores/configs",
            json=store_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create WooCommerce store: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["platform"] == "woocommerce"
        assert data["name"] == "TEST_WooCommerce_Store"
        assert data["store_url"] == "https://test-woocommerce.example.com"
        
        # Credentials should be masked in response
        assert "consumer_key_masked" in data
        assert "consumer_secret_masked" in data
        
        created_stores.append(data["id"])
        print(f"✓ Created WooCommerce store: {data['id']}")
    
    def test_create_prestashop_store(self, auth_headers, created_stores):
        """Test creating a PrestaShop store"""
        store_data = {
            "name": "TEST_PrestaShop_Store",
            "platform": "prestashop",
            "store_url": "https://test-prestashop.example.com",
            "api_key": "PS_TEST_API_KEY_12345"
        }
        response = requests.post(
            f"{BASE_URL}/api/stores/configs",
            json=store_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create PrestaShop store: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["platform"] == "prestashop"
        assert data["name"] == "TEST_PrestaShop_Store"
        assert "api_key_masked" in data
        
        created_stores.append(data["id"])
        print(f"✓ Created PrestaShop store: {data['id']}")
    
    def test_create_shopify_store(self, auth_headers, created_stores):
        """Test creating a Shopify store"""
        store_data = {
            "name": "TEST_Shopify_Store",
            "platform": "shopify",
            "store_url": "test-shop.myshopify.com",
            "access_token": "shpat_test_token_12345",
            "api_version": "2024-10"
        }
        response = requests.post(
            f"{BASE_URL}/api/stores/configs",
            json=store_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create Shopify store: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["platform"] == "shopify"
        assert data["name"] == "TEST_Shopify_Store"
        assert "access_token_masked" in data
        
        created_stores.append(data["id"])
        print(f"✓ Created Shopify store: {data['id']}")
    
    def test_create_wix_store(self, auth_headers, created_stores):
        """Test creating a Wix eCommerce store"""
        store_data = {
            "name": "TEST_Wix_Store",
            "platform": "wix",
            "store_url": "https://test-wix.wixsite.com",
            "api_key": "IST.test_wix_api_key",
            "site_id": "12345678-1234-1234-1234-123456789012"
        }
        response = requests.post(
            f"{BASE_URL}/api/stores/configs",
            json=store_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create Wix store: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["platform"] == "wix"
        assert data["name"] == "TEST_Wix_Store"
        assert "api_key_masked" in data
        
        created_stores.append(data["id"])
        print(f"✓ Created Wix store: {data['id']}")
    
    def test_create_magento_store(self, auth_headers, created_stores):
        """Test creating a Magento store"""
        store_data = {
            "name": "TEST_Magento_Store",
            "platform": "magento",
            "store_url": "https://test-magento.example.com",
            "access_token": "magento_integration_token_12345",
            "store_code": "default"
        }
        response = requests.post(
            f"{BASE_URL}/api/stores/configs",
            json=store_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create Magento store: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["platform"] == "magento"
        assert data["name"] == "TEST_Magento_Store"
        assert "access_token_masked" in data
        
        created_stores.append(data["id"])
        print(f"✓ Created Magento store: {data['id']}")
    
    def test_get_stores_after_creation(self, auth_headers, created_stores):
        """Verify created stores appear in GET"""
        response = requests.get(
            f"{BASE_URL}/api/stores/configs",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all TEST_ stores are present
        store_ids = [s["id"] for s in data]
        for store_id in created_stores:
            assert store_id in store_ids, f"Store {store_id} not found in GET response"
        
        print(f"✓ All {len(created_stores)} created stores found in GET response")
    
    def test_validation_missing_required_fields(self, auth_headers):
        """Test validation - missing required fields"""
        store_data = {
            "name": "TEST_Invalid_Store",
            "platform": "woocommerce",
            # Missing store_url, consumer_key, consumer_secret
        }
        response = requests.post(
            f"{BASE_URL}/api/stores/configs",
            json=store_data,
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for missing fields, got {response.status_code}"
        print("✓ Validation correctly rejects missing required fields")
    
    def test_validation_invalid_platform(self, auth_headers):
        """Test validation - invalid platform"""
        store_data = {
            "name": "TEST_Invalid_Platform",
            "platform": "invalid_platform",
            "store_url": "https://test.com"
        }
        response = requests.post(
            f"{BASE_URL}/api/stores/configs",
            json=store_data,
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid platform, got {response.status_code}"
        print("✓ Validation correctly rejects invalid platform")
    
    def test_get_single_store_config(self, auth_headers, created_stores):
        """Test GET /api/stores/configs/{config_id}"""
        if not created_stores:
            pytest.skip("No stores created")
        
        store_id = created_stores[0]
        response = requests.get(
            f"{BASE_URL}/api/stores/configs/{store_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == store_id
        print(f"✓ GET single store config works: {store_id}")
    
    def test_update_store_config(self, auth_headers, created_stores):
        """Test PUT /api/stores/configs/{config_id}"""
        if not created_stores:
            pytest.skip("No stores created")
        
        store_id = created_stores[0]
        update_data = {
            "name": "TEST_Updated_Store_Name"
        }
        response = requests.put(
            f"{BASE_URL}/api/stores/configs/{store_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Updated_Store_Name"
        print(f"✓ PUT update store config works")
    
    def test_test_connection_woocommerce(self, auth_headers, created_stores):
        """Test POST /api/stores/configs/{config_id}/test for WooCommerce"""
        if not created_stores:
            pytest.skip("No stores created")
        
        store_id = created_stores[0]  # WooCommerce store
        response = requests.post(
            f"{BASE_URL}/api/stores/configs/{store_id}/test",
            headers=auth_headers
        )
        # WooCommerce test may fail since it's not a real store, but endpoint should work
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data
        print(f"✓ Test connection endpoint works (status: {data['status']})")
    
    def test_test_connection_demo_platforms(self, auth_headers, created_stores):
        """Test connection for demo platforms (PrestaShop, Shopify, Wix, Magento)"""
        if len(created_stores) < 2:
            pytest.skip("Not enough stores created")
        
        # Test PrestaShop (index 1)
        store_id = created_stores[1]
        response = requests.post(
            f"{BASE_URL}/api/stores/configs/{store_id}/test",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"  # Demo platforms return success
        print(f"✓ PrestaShop test connection returns success (demo mode)")
    
    def test_cleanup_stores(self, auth_headers, created_stores):
        """Cleanup - delete all TEST_ stores"""
        deleted = 0
        for store_id in created_stores:
            response = requests.delete(
                f"{BASE_URL}/api/stores/configs/{store_id}",
                headers=auth_headers
            )
            if response.status_code in [200, 204]:
                deleted += 1
        
        print(f"✓ Cleanup: deleted {deleted}/{len(created_stores)} test stores")
        assert deleted == len(created_stores)


class TestStoresUnauthorized:
    """Test stores API without authentication"""
    
    def test_get_stores_unauthorized(self):
        """Test GET /api/stores/configs without auth"""
        response = requests.get(f"{BASE_URL}/api/stores/configs")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ GET /api/stores/configs correctly requires authentication")
    
    def test_create_store_unauthorized(self):
        """Test POST /api/stores/configs without auth"""
        response = requests.post(
            f"{BASE_URL}/api/stores/configs",
            json={"name": "Test", "platform": "woocommerce", "store_url": "https://test.com"}
        )
        assert response.status_code == 401 or response.status_code == 403
        print("✓ POST /api/stores/configs correctly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
