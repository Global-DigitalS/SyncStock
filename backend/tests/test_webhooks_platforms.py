"""
Webhook System and Platform Integrations Tests
Tests for webhook CRUD, webhook stats, and platform client integrations
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def test_store(auth_headers):
    """Create a test store for webhook testing"""
    store_data = {
        "name": "TEST_Webhook_Store",
        "platform": "prestashop",
        "store_url": "https://test-prestashop-store.example.com",
        "api_key": "test_api_key_12345"
    }
    response = requests.post(
        f"{BASE_URL}/api/stores/configs",
        headers=auth_headers,
        json=store_data
    )
    if response.status_code == 200:
        store = response.json()
        yield store
        # Cleanup
        requests.delete(f"{BASE_URL}/api/stores/configs/{store['id']}", headers=auth_headers)
    else:
        pytest.skip(f"Failed to create test store: {response.text}")


class TestWebhookConfigs:
    """Webhook Configuration CRUD Tests"""
    
    def test_get_webhook_configs(self, auth_headers):
        """Test GET /api/webhooks/configs returns list"""
        response = requests.get(
            f"{BASE_URL}/api/webhooks/configs",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        print(f"GET /api/webhooks/configs returned {len(data)} configs")
    
    def test_get_webhook_stats(self, auth_headers):
        """Test GET /api/webhooks/stats returns statistics"""
        response = requests.get(
            f"{BASE_URL}/api/webhooks/stats",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify stats structure
        assert "total_events" in data, "Missing total_events in stats"
        assert "processed" in data, "Missing processed in stats"
        assert "pending" in data, "Missing pending in stats"
        assert "by_event_type" in data, "Missing by_event_type in stats"
        assert "by_store" in data, "Missing by_store in stats"
        
        print(f"Webhook stats: {data['total_events']} total, {data['processed']} processed, {data['pending']} pending")
    
    def test_create_webhook_config(self, auth_headers, test_store):
        """Test POST /api/webhooks/configs creates webhook"""
        webhook_data = {
            "store_id": test_store["id"],
            "enabled": True,
            "events": ["inventory.updated", "order.created", "product.updated"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/webhooks/configs",
            headers=auth_headers,
            json=webhook_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Missing webhook id"
        assert "secret_key" in data, "Missing secret_key (shown only on creation)"
        assert "webhook_url" in data, "Missing webhook_url"
        assert data["store_id"] == test_store["id"], "Store ID mismatch"
        assert data["enabled"] == True, "Enabled should be True"
        assert len(data["events"]) == 3, "Expected 3 events"
        
        # Store webhook id for cleanup
        webhook_id = data["id"]
        print(f"Created webhook: {webhook_id}")
        print(f"Webhook URL: {data['webhook_url']}")
        
        # Cleanup webhook
        requests.delete(f"{BASE_URL}/api/webhooks/configs/{webhook_id}", headers=auth_headers)
    
    def test_create_webhook_invalid_store(self, auth_headers):
        """Test POST /api/webhooks/configs with invalid store returns 404"""
        webhook_data = {
            "store_id": "nonexistent-store-id",
            "enabled": True,
            "events": ["inventory.updated"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/webhooks/configs",
            headers=auth_headers,
            json=webhook_data
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_webhook_crud_flow(self, auth_headers, test_store):
        """Test full CRUD flow for webhook"""
        # CREATE
        create_data = {
            "store_id": test_store["id"],
            "enabled": True,
            "events": ["inventory.updated"]
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/webhooks/configs",
            headers=auth_headers,
            json=create_data
        )
        assert create_resp.status_code == 200
        webhook = create_resp.json()
        webhook_id = webhook["id"]
        original_secret = webhook["secret_key"]
        
        # READ - verify webhook in list
        list_resp = requests.get(
            f"{BASE_URL}/api/webhooks/configs",
            headers=auth_headers
        )
        assert list_resp.status_code == 200
        configs = list_resp.json()
        found = any(c["id"] == webhook_id for c in configs)
        assert found, "Created webhook not found in list"
        
        # UPDATE - disable webhook
        update_resp = requests.put(
            f"{BASE_URL}/api/webhooks/configs/{webhook_id}",
            headers=auth_headers,
            json={"enabled": False, "events": ["order.created"]}
        )
        assert update_resp.status_code == 200
        
        # Verify update
        list_resp2 = requests.get(
            f"{BASE_URL}/api/webhooks/configs",
            headers=auth_headers
        )
        updated = next((c for c in list_resp2.json() if c["id"] == webhook_id), None)
        assert updated is not None
        assert updated["enabled"] == False, "Webhook should be disabled"
        
        # REGENERATE SECRET
        regen_resp = requests.post(
            f"{BASE_URL}/api/webhooks/configs/{webhook_id}/regenerate-secret",
            headers=auth_headers
        )
        assert regen_resp.status_code == 200
        new_secret = regen_resp.json().get("secret_key")
        assert new_secret is not None, "No new secret returned"
        assert new_secret != original_secret, "Secret should have changed"
        print("Secret regeneration works correctly")
        
        # DELETE
        delete_resp = requests.delete(
            f"{BASE_URL}/api/webhooks/configs/{webhook_id}",
            headers=auth_headers
        )
        assert delete_resp.status_code == 200
        
        # Verify deletion
        list_resp3 = requests.get(
            f"{BASE_URL}/api/webhooks/configs",
            headers=auth_headers
        )
        found_after_delete = any(c["id"] == webhook_id for c in list_resp3.json())
        assert not found_after_delete, "Webhook should be deleted"
        print("Full webhook CRUD flow passed")


class TestWebhookEvents:
    """Webhook Events Tests"""
    
    def test_get_webhook_events(self, auth_headers):
        """Test GET /api/webhooks/events returns event logs"""
        response = requests.get(
            f"{BASE_URL}/api/webhooks/events",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of events"
        print(f"Found {len(data)} webhook events")


class TestWebhookReceiver:
    """Webhook Receiver Endpoint Tests"""
    
    def test_receive_webhook_invalid_config(self):
        """Test POST /api/webhooks/receive/{invalid_id} returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/webhooks/receive/nonexistent-config-id",
            json={"event": "test.event", "data": {"test": "payload"}},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_receive_webhook_valid(self, auth_headers, test_store):
        """Test webhook receiver endpoint with valid config"""
        # Create a webhook config first
        create_data = {
            "store_id": test_store["id"],
            "enabled": True,
            "events": ["inventory.updated"]
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/webhooks/configs",
            headers=auth_headers,
            json=create_data
        )
        assert create_resp.status_code == 200
        webhook = create_resp.json()
        webhook_id = webhook["id"]
        
        try:
            # Send webhook (no auth required for webhook receiver)
            webhook_payload = {
                "event": "inventory.updated",
                "sku": "TEST-SKU-001",
                "quantity": 100
            }
            recv_resp = requests.post(
                f"{BASE_URL}/api/webhooks/receive/{webhook_id}",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            )
            assert recv_resp.status_code == 200, f"Expected 200, got {recv_resp.status_code}"
            data = recv_resp.json()
            assert data.get("status") == "received", "Expected status 'received'"
            print(f"Webhook received with event type: {data.get('event')}")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/webhooks/configs/{webhook_id}", headers=auth_headers)


class TestPlatformIntegrations:
    """Platform Integration Tests - Verifying real clients exist"""
    
    def test_prestashop_store_connection_test(self, auth_headers):
        """Test PrestaShop store connection test endpoint"""
        # Create a PrestaShop store
        store_data = {
            "name": "TEST_PrestaShop_Integration",
            "platform": "prestashop",
            "store_url": "https://example-prestashop.com",
            "api_key": "test_prestashop_api_key"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/stores/configs",
            headers=auth_headers,
            json=store_data
        )
        assert create_resp.status_code == 200
        store = create_resp.json()
        
        try:
            # Test connection - will fail with invalid credentials but tests the client
            test_resp = requests.post(
                f"{BASE_URL}/api/stores/configs/{store['id']}/test",
                headers=auth_headers
            )
            # Either success or error - both are valid responses
            assert test_resp.status_code == 200, f"Expected 200, got {test_resp.status_code}"
            data = test_resp.json()
            assert "status" in data, "Missing status in response"
            # PrestaShop client should attempt real connection
            print(f"PrestaShop test result: {data.get('status')} - {data.get('message', '')}")
        finally:
            requests.delete(f"{BASE_URL}/api/stores/configs/{store['id']}", headers=auth_headers)
    
    def test_shopify_store_connection_test(self, auth_headers):
        """Test Shopify store connection test endpoint"""
        store_data = {
            "name": "TEST_Shopify_Integration",
            "platform": "shopify",
            "store_url": "test-store.myshopify.com",
            "access_token": "shpat_test_token_12345"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/stores/configs",
            headers=auth_headers,
            json=store_data
        )
        assert create_resp.status_code == 200
        store = create_resp.json()
        
        try:
            test_resp = requests.post(
                f"{BASE_URL}/api/stores/configs/{store['id']}/test",
                headers=auth_headers
            )
            assert test_resp.status_code == 200
            data = test_resp.json()
            assert "status" in data
            print(f"Shopify test result: {data.get('status')} - {data.get('message', '')}")
        finally:
            requests.delete(f"{BASE_URL}/api/stores/configs/{store['id']}", headers=auth_headers)
    
    def test_magento_store_connection_test(self, auth_headers):
        """Test Magento store connection test endpoint"""
        store_data = {
            "name": "TEST_Magento_Integration",
            "platform": "magento",
            "store_url": "https://example-magento.com",
            "access_token": "test_magento_token"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/stores/configs",
            headers=auth_headers,
            json=store_data
        )
        assert create_resp.status_code == 200
        store = create_resp.json()
        
        try:
            test_resp = requests.post(
                f"{BASE_URL}/api/stores/configs/{store['id']}/test",
                headers=auth_headers
            )
            assert test_resp.status_code == 200
            data = test_resp.json()
            assert "status" in data
            print(f"Magento test result: {data.get('status')} - {data.get('message', '')}")
        finally:
            requests.delete(f"{BASE_URL}/api/stores/configs/{store['id']}", headers=auth_headers)
    
    def test_wix_store_connection_test(self, auth_headers):
        """Test Wix store connection test endpoint"""
        store_data = {
            "name": "TEST_Wix_Integration",
            "platform": "wix",
            "store_url": "https://example-wix-store.com",
            "api_key": "test_wix_api_key",
            "site_id": "test_site_id_12345"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/stores/configs",
            headers=auth_headers,
            json=store_data
        )
        assert create_resp.status_code == 200
        store = create_resp.json()
        
        try:
            test_resp = requests.post(
                f"{BASE_URL}/api/stores/configs/{store['id']}/test",
                headers=auth_headers
            )
            assert test_resp.status_code == 200
            data = test_resp.json()
            assert "status" in data
            print(f"Wix test result: {data.get('status')} - {data.get('message', '')}")
        finally:
            requests.delete(f"{BASE_URL}/api/stores/configs/{store['id']}", headers=auth_headers)


class TestAuthRequired:
    """Tests to verify authentication is required"""
    
    def test_webhook_configs_requires_auth(self):
        """Test GET /api/webhooks/configs requires auth"""
        response = requests.get(f"{BASE_URL}/api/webhooks/configs")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_webhook_stats_requires_auth(self):
        """Test GET /api/webhooks/stats requires auth"""
        response = requests.get(f"{BASE_URL}/api/webhooks/stats")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
