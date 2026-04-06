"""
Backend API Tests for StockHub SaaS Application
Tests: Auth, Suppliers, Dashboard endpoints
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "Test1234!"
TEST_NAME = "Test User"

class TestHealthEndpoint:
    """Health check endpoint tests"""

    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'ok'
        assert 'timestamp' in data
        print(f"Health check passed: {data}")


class TestAuthEndpoints:
    """Authentication endpoint tests"""

    @pytest.fixture(scope="class")
    def registered_user(self):
        """Register a test user and return credentials"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            data = response.json()
            return {
                "email": unique_email,
                "password": TEST_PASSWORD,
                "token": data.get("token"),
                "user": data.get("user")
            }
        pytest.skip(f"Failed to register user: {response.text}")

    def test_register_user_success(self):
        """Test user registration"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Data assertions
        assert "token" in data, "Token should be returned"
        assert "user" in data, "User should be returned"
        assert data["user"]["email"] == unique_email
        assert data["user"]["name"] == TEST_NAME
        assert "id" in data["user"]
        print(f"Registration successful: user_id={data['user']['id']}")

    def test_register_duplicate_email(self, registered_user):
        """Test registration with existing email"""
        payload = {
            "email": registered_user["email"],
            "password": TEST_PASSWORD,
            "name": "Duplicate User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"Duplicate registration correctly rejected: {data}")

    def test_login_success(self, registered_user):
        """Test user login with valid credentials"""
        payload = {
            "email": registered_user["email"],
            "password": TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Data assertions
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == registered_user["email"]
        print(f"Login successful: user_id={data['user']['id']}")

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        payload = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"Invalid login correctly rejected: {data}")

    def test_get_current_user(self, registered_user):
        """Test GET /api/auth/me endpoint"""
        headers = {"Authorization": f"Bearer {registered_user['token']}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Data assertions
        assert data["email"] == registered_user["email"]
        assert data["name"] == TEST_NAME
        assert "id" in data
        assert "created_at" in data
        print(f"Current user retrieved: {data['email']}")

    def test_get_current_user_unauthorized(self):
        """Test GET /api/auth/me without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")

        assert response.status_code in [401, 403]
        print("Unauthorized access correctly rejected")


class TestSupplierEndpoints:
    """Supplier CRUD endpoint tests"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        unique_email = f"test_supplier_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": TEST_PASSWORD,
            "name": "Supplier Test User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip(f"Failed to get auth: {response.text}")

    @pytest.fixture
    def created_supplier(self, auth_headers):
        """Create a supplier for tests and cleanup after"""
        payload = {
            "name": f"TEST_Supplier_{uuid.uuid4().hex[:8]}",
            "description": "Test supplier for automated testing",
            "ftp_schema": "ftp",
            "ftp_host": "test.ftp.example.com",
            "ftp_user": "testuser",
            "ftp_password": "testpass",
            "ftp_port": 21,
            "ftp_path": "/catalogo/test.csv",
            "ftp_mode": "passive",
            "file_format": "csv",
            "csv_separator": ";",
            "column_mapping": {"sku": "referencia", "name": "nombre", "price": "precio"}
        }
        response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=auth_headers)
        if response.status_code == 200:
            supplier = response.json()
            yield supplier
            # Cleanup
            requests.delete(f"{BASE_URL}/api/suppliers/{supplier['id']}", headers=auth_headers)
        else:
            pytest.fail(f"Failed to create supplier: {response.text}")

    def test_create_supplier_success(self, auth_headers):
        """Test POST /api/suppliers - create supplier with FTP config"""
        payload = {
            "name": f"TEST_NewSupplier_{uuid.uuid4().hex[:8]}",
            "description": "New test supplier",
            "ftp_schema": "ftp",
            "ftp_host": "speedtest.tele2.net",
            "ftp_user": "anonymous",
            "ftp_password": "",
            "ftp_port": 21,
            "ftp_path": "/1KB.zip",
            "ftp_mode": "passive",
            "file_format": "csv",
            "csv_separator": ";",
            "column_mapping": {"sku": "codigo", "name": "titulo"}
        }
        response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Data assertions
        assert "id" in data
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["ftp_schema"] == "ftp"
        assert data["ftp_host"] == "speedtest.tele2.net"
        assert data["ftp_port"] == 21
        assert data["file_format"] == "csv"
        assert data["column_mapping"] == payload["column_mapping"]
        assert "ftp_password" not in data  # Password should not be returned

        supplier_id = data["id"]
        print(f"Supplier created: {supplier_id}")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=auth_headers)

    def test_create_supplier_minimal(self, auth_headers):
        """Test create supplier with minimal data"""
        payload = {"name": f"TEST_MinimalSupplier_{uuid.uuid4().hex[:8]}"}
        response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == payload["name"]

        # Cleanup
        requests.delete(f"{BASE_URL}/api/suppliers/{data['id']}", headers=auth_headers)
        print("Minimal supplier created and deleted")

    def test_get_suppliers_list(self, auth_headers, created_supplier):
        """Test GET /api/suppliers - list suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should contain our created supplier
        supplier_ids = [s["id"] for s in data]
        assert created_supplier["id"] in supplier_ids
        print(f"Listed {len(data)} suppliers")

    def test_get_supplier_by_id(self, auth_headers, created_supplier):
        """Test GET /api/suppliers/{id} - get specific supplier"""
        response = requests.get(
            f"{BASE_URL}/api/suppliers/{created_supplier['id']}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Data assertions
        assert data["id"] == created_supplier["id"]
        assert data["name"] == created_supplier["name"]
        assert "ftp_password" not in data  # Password should not be returned
        print(f"Retrieved supplier: {data['name']}")

    def test_get_supplier_not_found(self, auth_headers):
        """Test GET /api/suppliers/{id} - non-existent supplier"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/suppliers/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        print("Non-existent supplier correctly returns 404")

    def test_update_supplier(self, auth_headers, created_supplier):
        """Test PUT /api/suppliers/{id} - update supplier"""
        update_payload = {
            "name": f"TEST_UpdatedSupplier_{uuid.uuid4().hex[:8]}",
            "description": "Updated description",
            "ftp_host": "updated.ftp.example.com"
        }
        response = requests.put(
            f"{BASE_URL}/api/suppliers/{created_supplier['id']}",
            json=update_payload,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify update was applied
        assert data["name"] == update_payload["name"]
        assert data["description"] == update_payload["description"]
        assert data["ftp_host"] == update_payload["ftp_host"]

        # GET to verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/suppliers/{created_supplier['id']}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["name"] == update_payload["name"]
        print(f"Supplier updated: {data['name']}")

    def test_delete_supplier(self, auth_headers):
        """Test DELETE /api/suppliers/{id}"""
        # Create supplier to delete
        payload = {"name": f"TEST_ToDelete_{uuid.uuid4().hex[:8]}"}
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        supplier_id = create_response.json()["id"]

        # Delete supplier
        delete_response = requests.delete(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=auth_headers)
        assert delete_response.status_code == 200

        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=auth_headers)
        assert get_response.status_code == 404
        print(f"Supplier deleted: {supplier_id}")


class TestSyncStockEndpoints:
    """Supplier FTP sync endpoint tests"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        unique_email = f"test_sync_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": TEST_PASSWORD,
            "name": "Sync Test User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip(f"Failed to get auth: {response.text}")

    def test_sync_supplier_no_ftp_config(self, auth_headers):
        """Test sync endpoint without FTP configuration"""
        # Create supplier without FTP
        payload = {"name": f"TEST_NoFTP_{uuid.uuid4().hex[:8]}"}
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        supplier_id = create_response.json()["id"]

        # Try to sync
        sync_response = requests.post(f"{BASE_URL}/api/suppliers/{supplier_id}/sync", headers=auth_headers)

        # Should fail with 400 (incomplete FTP config)
        assert sync_response.status_code == 400
        data = sync_response.json()
        assert "detail" in data
        print(f"Sync without FTP config correctly rejected: {data['detail']}")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=auth_headers)

    def test_sync_supplier_ftp_error_with_known_host(self, auth_headers):
        """Test sync endpoint with FTP permission error (known host that denies access)"""
        # Create supplier with real FTP server that denies access
        # speedtest.tele2.net exists but denies file access
        payload = {
            "name": f"TEST_PermissionDenied_{uuid.uuid4().hex[:8]}",
            "ftp_host": "speedtest.tele2.net",
            "ftp_path": "/nonexistent/test.csv",
            "ftp_user": "",
            "ftp_password": ""
        }
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        supplier_id = create_response.json()["id"]

        # Try to sync - should return 200 with error status (per the fix mentioned)
        # FTP connection is quick but file access is denied
        sync_response = requests.post(
            f"{BASE_URL}/api/suppliers/{supplier_id}/sync",
            headers=auth_headers,
            timeout=30
        )

        # Should return 200 with error status (per the main agent's fix)
        assert sync_response.status_code == 200, f"Expected 200, got {sync_response.status_code}: {sync_response.text}"
        data = sync_response.json()
        assert data.get("status") == "error"
        assert "message" in data
        # Error should mention permission denied or file not found
        print(f"FTP error handled gracefully: {data['message'][:80]}...")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=auth_headers)

    def test_get_sync_status(self, auth_headers):
        """Test GET /api/suppliers/{id}/sync-status"""
        # Create supplier with FTP
        payload = {
            "name": f"TEST_SyncStatus_{uuid.uuid4().hex[:8]}",
            "ftp_host": "test.example.com",
            "ftp_path": "/test.csv"
        }
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=auth_headers)
        assert create_response.status_code == 200
        supplier_id = create_response.json()["id"]

        # Get sync status
        status_response = requests.get(f"{BASE_URL}/api/suppliers/{supplier_id}/sync-status", headers=auth_headers)

        assert status_response.status_code == 200
        data = status_response.json()

        # Data assertions
        assert "last_sync" in data
        assert "next_scheduled_sync" in data
        assert "ftp_configured" in data
        assert "product_count" in data
        assert data["ftp_configured"] == True
        print(f"Sync status retrieved: ftp_configured={data['ftp_configured']}")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=auth_headers)


class TestDashboardEndpoints:
    """Dashboard endpoint tests"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        unique_email = f"test_dashboard_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": TEST_PASSWORD,
            "name": "Dashboard Test User"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        pytest.skip(f"Failed to get auth: {response.text}")

    def test_get_dashboard_stats(self, auth_headers):
        """Test GET /api/dashboard/stats"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Data assertions - verify all expected fields exist with correct types
        assert "total_suppliers" in data
        assert "total_products" in data
        assert "total_catalog_items" in data
        assert "low_stock_count" in data
        assert "out_of_stock_count" in data
        assert "unread_notifications" in data
        assert "recent_price_changes" in data

        # Type assertions
        assert isinstance(data["total_suppliers"], int)
        assert isinstance(data["total_products"], int)
        assert isinstance(data["low_stock_count"], int)

        print(f"Dashboard stats: suppliers={data['total_suppliers']}, products={data['total_products']}")

    def test_get_dashboard_stats_unauthorized(self):
        """Test dashboard stats without auth"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")

        assert response.status_code in [401, 403]
        print("Dashboard unauthorized access correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
