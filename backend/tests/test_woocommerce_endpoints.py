"""
Backend API Tests for WooCommerce Integration Endpoints
Tests: CRUD operations for WooCommerce configs, connection test, and export
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_PASSWORD = "Test1234!"

class TestWooCommerceEndpoints:
    """WooCommerce configuration CRUD endpoint tests"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        unique_email = f"test_woo_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": TEST_PASSWORD,
            "name": "WooCommerce Test User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip(f"Failed to get auth: {response.text}")

    @pytest.fixture
    def created_config(self, auth_headers):
        """Create a WooCommerce config for tests and cleanup after"""
        payload = {
            "name": f"TEST_WooStore_{uuid.uuid4().hex[:8]}",
            "store_url": "https://test-store.example.com",
            "consumer_key": f"ck_test_{uuid.uuid4().hex[:20]}",
            "consumer_secret": f"cs_test_{uuid.uuid4().hex[:20]}"
        }
        response = requests.post(f"{BASE_URL}/api/woocommerce/configs", json=payload, headers=auth_headers)
        if response.status_code == 200:
            config = response.json()
            yield config
            # Cleanup
            requests.delete(f"{BASE_URL}/api/woocommerce/configs/{config['id']}", headers=auth_headers)
        else:
            pytest.fail(f"Failed to create WooCommerce config: {response.text}")

    # ==================== CREATE Tests ====================

    def test_create_woocommerce_config_success(self, auth_headers):
        """Test POST /api/woocommerce/configs - create new config"""
        payload = {
            "name": f"TEST_NewWooStore_{uuid.uuid4().hex[:8]}",
            "store_url": "https://my-woo-store.com",
            "consumer_key": f"ck_{uuid.uuid4().hex[:24]}",
            "consumer_secret": f"cs_{uuid.uuid4().hex[:24]}"
        }
        response = requests.post(f"{BASE_URL}/api/woocommerce/configs", json=payload, headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Data assertions
        assert "id" in data, "Config ID should be returned"
        assert data["name"] == payload["name"], "Name should match"
        assert data["store_url"] == payload["store_url"], "Store URL should match"
        assert "consumer_key_masked" in data, "Consumer key should be masked"
        assert data["consumer_key_masked"].endswith(payload["consumer_key"][-4:]), "Masked key should show last 4 chars"
        assert data["is_connected"] == False, "Should not be connected initially"
        assert data["products_synced"] == 0, "Products synced should be 0"
        assert "created_at" in data, "Created at timestamp should exist"

        config_id = data["id"]
        print(f"WooCommerce config created: {config_id}")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/woocommerce/configs/{config_id}", headers=auth_headers)

    def test_create_woocommerce_config_with_default_name(self, auth_headers):
        """Test creating config without name uses default"""
        payload = {
            "store_url": "https://default-name-store.com",
            "consumer_key": f"ck_{uuid.uuid4().hex[:24]}",
            "consumer_secret": f"cs_{uuid.uuid4().hex[:24]}"
        }
        response = requests.post(f"{BASE_URL}/api/woocommerce/configs", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should use default name
        assert data["name"] == "Mi Tienda WooCommerce", "Default name should be used"
        print(f"Config created with default name: {data['name']}")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/woocommerce/configs/{data['id']}", headers=auth_headers)

    def test_create_woocommerce_config_missing_fields(self, auth_headers):
        """Test creating config without required fields"""
        # Missing store_url
        payload = {
            "name": "Test Store",
            "consumer_key": "ck_test",
            "consumer_secret": "cs_test"
        }
        response = requests.post(f"{BASE_URL}/api/woocommerce/configs", json=payload, headers=auth_headers)

        assert response.status_code == 422, f"Expected 422 for missing required field, got {response.status_code}"
        print("Missing required field correctly rejected")

    def test_create_woocommerce_config_unauthorized(self):
        """Test creating config without auth token"""
        payload = {
            "name": "Unauthorized Store",
            "store_url": "https://test.com",
            "consumer_key": "ck_test",
            "consumer_secret": "cs_test"
        }
        response = requests.post(f"{BASE_URL}/api/woocommerce/configs", json=payload)

        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Unauthorized access correctly rejected")

    # ==================== READ Tests ====================

    def test_get_woocommerce_configs_list(self, auth_headers, created_config):
        """Test GET /api/woocommerce/configs - list all configs"""
        response = requests.get(f"{BASE_URL}/api/woocommerce/configs", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list), "Response should be a list"
        # Should contain our created config
        config_ids = [c["id"] for c in data]
        assert created_config["id"] in config_ids, "Created config should be in the list"

        # Verify consumer_secret is not returned
        for config in data:
            assert "consumer_secret" not in config or config.get("consumer_secret") is None
            assert "consumer_key_masked" in config

        print(f"Listed {len(data)} WooCommerce configs")

    def test_get_woocommerce_configs_empty(self, auth_headers):
        """Test GET /api/woocommerce/configs returns empty list for new user"""
        # Create a new user with no configs
        unique_email = f"test_empty_{uuid.uuid4().hex[:8]}@example.com"
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": TEST_PASSWORD,
            "name": "Empty User"
        })
        if reg_response.status_code != 200:
            pytest.skip("Could not create new user")

        new_headers = {"Authorization": f"Bearer {reg_response.json()['token']}"}
        response = requests.get(f"{BASE_URL}/api/woocommerce/configs", headers=new_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0, "New user should have no configs"
        print("Empty configs list returned for new user")

    def test_get_woocommerce_config_by_id(self, auth_headers, created_config):
        """Test GET /api/woocommerce/configs/{id} - get specific config"""
        response = requests.get(
            f"{BASE_URL}/api/woocommerce/configs/{created_config['id']}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Data assertions
        assert data["id"] == created_config["id"]
        assert data["name"] == created_config["name"]
        assert data["store_url"] == created_config["store_url"]
        assert "consumer_key_masked" in data
        assert data["is_connected"] == created_config["is_connected"]

        print(f"Retrieved WooCommerce config: {data['name']}")

    def test_get_woocommerce_config_not_found(self, auth_headers):
        """Test GET /api/woocommerce/configs/{id} - non-existent config"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/woocommerce/configs/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        print("Non-existent config correctly returns 404")

    # ==================== UPDATE Tests ====================

    def test_update_woocommerce_config(self, auth_headers, created_config):
        """Test PUT /api/woocommerce/configs/{id} - update config"""
        update_payload = {
            "name": f"TEST_UpdatedStore_{uuid.uuid4().hex[:8]}",
            "store_url": "https://updated-store.example.com"
        }
        response = requests.put(
            f"{BASE_URL}/api/woocommerce/configs/{created_config['id']}",
            json=update_payload,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify update was applied
        assert data["name"] == update_payload["name"], "Name should be updated"
        assert data["store_url"] == update_payload["store_url"], "Store URL should be updated"

        # GET to verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/woocommerce/configs/{created_config['id']}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["name"] == update_payload["name"], "Name change should be persisted"
        assert get_data["store_url"] == update_payload["store_url"], "URL change should be persisted"

        print(f"WooCommerce config updated: {data['name']}")

    def test_update_woocommerce_config_credentials(self, auth_headers, created_config):
        """Test updating API credentials"""
        new_key = f"ck_new_{uuid.uuid4().hex[:20]}"
        update_payload = {
            "consumer_key": new_key
        }
        response = requests.put(
            f"{BASE_URL}/api/woocommerce/configs/{created_config['id']}",
            json=update_payload,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify new key is masked correctly
        assert data["consumer_key_masked"].endswith(new_key[-4:])
        print("API credentials updated successfully")

    def test_update_woocommerce_config_not_found(self, auth_headers):
        """Test PUT /api/woocommerce/configs/{id} - non-existent config"""
        fake_id = str(uuid.uuid4())
        update_payload = {"name": "Updated Name"}
        response = requests.put(
            f"{BASE_URL}/api/woocommerce/configs/{fake_id}",
            json=update_payload,
            headers=auth_headers
        )

        assert response.status_code == 404
        print("Update non-existent config correctly returns 404")

    # ==================== DELETE Tests ====================

    def test_delete_woocommerce_config(self, auth_headers):
        """Test DELETE /api/woocommerce/configs/{id}"""
        # Create config to delete
        payload = {
            "name": f"TEST_ToDelete_{uuid.uuid4().hex[:8]}",
            "store_url": "https://delete-me.example.com",
            "consumer_key": f"ck_{uuid.uuid4().hex[:20]}",
            "consumer_secret": f"cs_{uuid.uuid4().hex[:20]}"
        }
        create_response = requests.post(f"{BASE_URL}/api/woocommerce/configs", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        # Delete config
        delete_response = requests.delete(f"{BASE_URL}/api/woocommerce/configs/{config_id}", headers=auth_headers)
        assert delete_response.status_code == 200

        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/woocommerce/configs/{config_id}", headers=auth_headers)
        assert get_response.status_code == 404, "Deleted config should return 404"

        print(f"WooCommerce config deleted: {config_id}")

    def test_delete_woocommerce_config_not_found(self, auth_headers):
        """Test DELETE /api/woocommerce/configs/{id} - non-existent config"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/woocommerce/configs/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        print("Delete non-existent config correctly returns 404")

    # ==================== TEST CONNECTION Tests ====================

    def test_woocommerce_connection_test_not_found(self, auth_headers):
        """Test connection test for non-existent config"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/woocommerce/configs/{fake_id}/test", headers=auth_headers)

        assert response.status_code == 404
        print("Connection test for non-existent config correctly returns 404")

    def test_woocommerce_connection_test_invalid_credentials(self, auth_headers, created_config):
        """Test connection with invalid credentials - should return error status"""
        response = requests.post(
            f"{BASE_URL}/api/woocommerce/configs/{created_config['id']}/test",
            headers=auth_headers,
            timeout=35  # WooCommerce API has 30s timeout
        )

        # Should return 200 with error status (not HTTP error)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Invalid credentials should result in error
        assert "status" in data
        assert data["status"] == "error", f"Expected error status, got: {data}"
        assert "message" in data

        print(f"Connection test with invalid credentials returned: {data['status']} - {data['message'][:50]}")

    # ==================== EXPORT Tests ====================

    def test_woocommerce_export_config_not_found(self, auth_headers):
        """Test export with non-existent config"""
        payload = {
            "config_id": str(uuid.uuid4()),
            "update_existing": True
        }
        response = requests.post(f"{BASE_URL}/api/woocommerce/export", json=payload, headers=auth_headers)

        assert response.status_code == 404
        print("Export with non-existent config correctly returns 404")

    def test_woocommerce_export_no_catalog_items(self, auth_headers, created_config):
        """Test export with no active catalog items"""
        payload = {
            "config_id": created_config["id"],
            "update_existing": True
        }
        response = requests.post(f"{BASE_URL}/api/woocommerce/export", json=payload, headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Should return warning about no products
        assert "status" in data
        assert data["status"] == "warning", f"Expected warning status, got: {data['status']}"
        assert "errors" in data
        assert any("No hay productos" in e for e in data["errors"]), f"Expected no products message, got: {data['errors']}"

        print(f"Export with no catalog items returned: {data['status']}")

    def test_woocommerce_export_unauthorized(self):
        """Test export without auth"""
        payload = {
            "config_id": str(uuid.uuid4()),
            "update_existing": True
        }
        response = requests.post(f"{BASE_URL}/api/woocommerce/export", json=payload)

        assert response.status_code in [401, 403]
        print("Export without auth correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
