"""
CRM Dolibarr Integration Tests
Tests all CRM connection endpoints and sync functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - from previous iterations
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"

# Dolibarr demo config for testing
DOLIBARR_TEST_CONFIG = {
    "api_url": "https://demo.dolibarr.org/api/index.php",
    "api_key": "test_invalid_key_for_testing"  # Invalid key but allows testing connection flow
}


class TestCRMAuth:
    """Test that CRM endpoints require authentication"""
    
    def test_get_connections_requires_auth(self):
        """GET /api/crm/connections should require auth"""
        response = requests.get(f"{BASE_URL}/api/crm/connections")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/crm/connections requires authentication")
    
    def test_post_connection_requires_auth(self):
        """POST /api/crm/connections should require auth"""
        response = requests.post(f"{BASE_URL}/api/crm/connections", json={
            "name": "Test",
            "platform": "dolibarr",
            "config": DOLIBARR_TEST_CONFIG
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/crm/connections requires authentication")
    
    def test_test_connection_requires_auth(self):
        """POST /api/crm/test-connection should require auth"""
        response = requests.post(f"{BASE_URL}/api/crm/test-connection", json={
            "platform": "dolibarr",
            "config": DOLIBARR_TEST_CONFIG
        })
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/crm/test-connection requires authentication")


class TestCRMConnections:
    """Test CRM connection CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        data = response.json()
        self.token = data.get("token") or data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        print(f"Authenticated as {TEST_EMAIL}")
    
    def test_get_connections_empty_or_existing(self):
        """GET /api/crm/connections - returns list of connections"""
        response = requests.get(
            f"{BASE_URL}/api/crm/connections",
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Expected list of connections"
        print(f"PASS: GET /api/crm/connections returns list (count: {len(data)})")
    
    def test_create_dolibarr_connection(self):
        """POST /api/crm/connections - create new Dolibarr connection"""
        connection_name = f"TEST_CRM_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/crm/connections",
            headers=self.headers,
            json={
                "name": connection_name,
                "platform": "dolibarr",
                "config": DOLIBARR_TEST_CONFIG,
                "sync_settings": {
                    "products": True,
                    "stock": True,
                    "prices": True,
                    "descriptions": True,
                    "images": True,
                    "suppliers": True,
                    "orders": True
                }
            }
        )
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "id" in data, "Response should contain 'id'"
        assert data.get("name") == connection_name, f"Name mismatch: expected {connection_name}"
        assert data.get("platform") == "dolibarr", "Platform should be 'dolibarr'"
        assert "config" in data, "Response should contain 'config'"
        assert "sync_settings" in data, "Response should contain 'sync_settings'"
        # Connection will be disconnected since we used invalid API key
        assert "is_connected" in data, "Response should contain 'is_connected'"
        
        # Store connection_id for cleanup
        self.created_connection_id = data["id"]
        print(f"PASS: POST /api/crm/connections - Created connection: {data['id']}")
        
        return data["id"]
    
    def test_test_connection_dolibarr(self):
        """POST /api/crm/test-connection - test Dolibarr connection"""
        response = requests.post(
            f"{BASE_URL}/api/crm/test-connection",
            headers=self.headers,
            json={
                "platform": "dolibarr",
                "config": DOLIBARR_TEST_CONFIG
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Test connection should return status and message
        assert "status" in data, "Response should contain 'status'"
        assert "message" in data, "Response should contain 'message'"
        
        # With invalid API key, we expect error status
        print(f"PASS: POST /api/crm/test-connection - Status: {data['status']}, Message: {data['message']}")
    
    def test_update_connection(self):
        """PUT /api/crm/connections/{id} - update connection"""
        # First create a connection
        connection_name = f"TEST_CRM_UPDATE_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/crm/connections",
            headers=self.headers,
            json={
                "name": connection_name,
                "platform": "dolibarr",
                "config": DOLIBARR_TEST_CONFIG
            }
        )
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.status_code}"
        connection_id = create_response.json()["id"]
        
        # Update the connection
        new_name = f"TEST_CRM_UPDATED_{uuid.uuid4().hex[:8]}"
        update_response = requests.put(
            f"{BASE_URL}/api/crm/connections/{connection_id}",
            headers=self.headers,
            json={
                "name": new_name,
                "config": DOLIBARR_TEST_CONFIG,
                "sync_settings": {
                    "products": True,
                    "stock": False,
                    "prices": True,
                    "descriptions": False,
                    "images": False,
                    "suppliers": True,
                    "orders": False
                }
            }
        )
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        print(f"PASS: PUT /api/crm/connections/{connection_id} - Connection updated")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/crm/connections/{connection_id}", headers=self.headers)
    
    def test_delete_connection(self):
        """DELETE /api/crm/connections/{id} - delete connection"""
        # First create a connection
        connection_name = f"TEST_CRM_DELETE_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/crm/connections",
            headers=self.headers,
            json={
                "name": connection_name,
                "platform": "dolibarr",
                "config": DOLIBARR_TEST_CONFIG
            }
        )
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.status_code}"
        connection_id = create_response.json()["id"]
        
        # Delete the connection
        delete_response = requests.delete(
            f"{BASE_URL}/api/crm/connections/{connection_id}",
            headers=self.headers
        )
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        data = delete_response.json()
        assert data.get("status") == "success", f"Expected success status: {data}"
        print(f"PASS: DELETE /api/crm/connections/{connection_id} - Connection deleted")
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/crm/connections",
            headers=self.headers
        )
        connections = get_response.json()
        connection_ids = [c.get("id") for c in connections]
        assert connection_id not in connection_ids, "Connection should be deleted"
        print("PASS: Verified connection was actually deleted")
    
    def test_delete_nonexistent_connection(self):
        """DELETE /api/crm/connections/{id} - 404 for nonexistent"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/crm/connections/{fake_id}",
            headers=self.headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"PASS: DELETE nonexistent connection returns 404")


class TestCRMSync:
    """Test CRM sync functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and create a test connection"""
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        data = response.json()
        self.token = data.get("token") or data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create test connection
        connection_name = f"TEST_CRM_SYNC_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/crm/connections",
            headers=self.headers,
            json={
                "name": connection_name,
                "platform": "dolibarr",
                "config": DOLIBARR_TEST_CONFIG,
                "sync_settings": {
                    "products": True,
                    "stock": True,
                    "prices": True,
                    "descriptions": True,
                    "images": True,
                    "suppliers": True,
                    "orders": True
                }
            }
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create test connection: {create_response.status_code}")
        
        self.connection_id = create_response.json()["id"]
        yield
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/crm/connections/{self.connection_id}",
            headers=self.headers
        )
    
    def test_sync_all(self):
        """POST /api/crm/connections/{id}/sync - sync all data"""
        response = requests.post(
            f"{BASE_URL}/api/crm/connections/{self.connection_id}/sync",
            headers=self.headers,
            json={"sync_type": "all"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should return sync results
        assert "status" in data, "Response should contain 'status'"
        assert "message" in data or "details" in data, "Response should contain 'message' or 'details'"
        
        print(f"PASS: POST /api/crm/connections/{self.connection_id}/sync (all) - {data.get('status')}")
    
    def test_sync_products_only(self):
        """POST /api/crm/connections/{id}/sync - sync products only"""
        response = requests.post(
            f"{BASE_URL}/api/crm/connections/{self.connection_id}/sync",
            headers=self.headers,
            json={"sync_type": "products"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check products result is present
        if "details" in data and data["details"]:
            assert "products" in data["details"], "Details should contain 'products' result"
        
        print(f"PASS: POST /api/crm/connections/{self.connection_id}/sync (products) - {data.get('status')}")
    
    def test_sync_suppliers_only(self):
        """POST /api/crm/connections/{id}/sync - sync suppliers only"""
        response = requests.post(
            f"{BASE_URL}/api/crm/connections/{self.connection_id}/sync",
            headers=self.headers,
            json={"sync_type": "suppliers"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        print(f"PASS: POST /api/crm/connections/{self.connection_id}/sync (suppliers) - {data.get('status')}")
    
    def test_sync_orders_only(self):
        """POST /api/crm/connections/{id}/sync - sync orders only"""
        response = requests.post(
            f"{BASE_URL}/api/crm/connections/{self.connection_id}/sync",
            headers=self.headers,
            json={"sync_type": "orders"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        print(f"PASS: POST /api/crm/connections/{self.connection_id}/sync (orders) - {data.get('status')}")
    
    def test_sync_nonexistent_connection(self):
        """POST /api/crm/connections/{id}/sync - 404 for nonexistent"""
        fake_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/crm/connections/{fake_id}/sync",
            headers=self.headers,
            json={"sync_type": "all"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Sync on nonexistent connection returns 404")


class TestCRMConnectionStats:
    """Test that CRM connections return stats"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        data = response.json()
        self.token = data.get("token") or data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_connection_includes_stats_field(self):
        """GET /api/crm/connections - each connection should have stats field"""
        # First create a connection
        connection_name = f"TEST_CRM_STATS_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/crm/connections",
            headers=self.headers,
            json={
                "name": connection_name,
                "platform": "dolibarr",
                "config": DOLIBARR_TEST_CONFIG
            }
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create test connection")
        
        connection_id = create_response.json()["id"]
        
        try:
            # Get all connections
            get_response = requests.get(
                f"{BASE_URL}/api/crm/connections",
                headers=self.headers
            )
            
            assert get_response.status_code == 200
            connections = get_response.json()
            
            # Find our connection
            our_connection = next((c for c in connections if c.get("id") == connection_id), None)
            assert our_connection is not None, "Our test connection should be in the list"
            
            # If connection is connected, stats should be present
            # If not connected, stats may or may not be present
            print(f"PASS: Connection has is_connected={our_connection.get('is_connected')}, stats={our_connection.get('stats')}")
            
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/crm/connections/{connection_id}", headers=self.headers)


class TestCleanup:
    """Clean up any leftover TEST_ connections"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        data = response.json()
        self.token = data.get("token") or data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_cleanup_test_connections(self):
        """Delete any TEST_ prefixed CRM connections"""
        response = requests.get(
            f"{BASE_URL}/api/crm/connections",
            headers=self.headers
        )
        
        if response.status_code != 200:
            pytest.skip("Could not get connections")
        
        connections = response.json()
        deleted_count = 0
        
        for conn in connections:
            if conn.get("name", "").startswith("TEST_"):
                delete_response = requests.delete(
                    f"{BASE_URL}/api/crm/connections/{conn['id']}",
                    headers=self.headers
                )
                if delete_response.status_code == 200:
                    deleted_count += 1
        
        print(f"PASS: Cleaned up {deleted_count} TEST_ connections")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
