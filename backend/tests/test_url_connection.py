"""
Tests for URL Direct Connection Feature for Suppliers
New functionality: Import CSV from HTTP/HTTPS URL besides FTP
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestURLConnectionBackend:
    """Tests for connection_type='url' and file_url field in suppliers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser@example.com",
            "password": "Test1234!"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.created_supplier_ids = []
        yield
        # Cleanup created suppliers
        for sid in self.created_supplier_ids:
            try:
                requests.delete(f"{BASE_URL}/api/suppliers/{sid}", headers=self.headers)
            except:
                pass

    # ==================== POST /api/suppliers with connection_type='url' ====================
    
    def test_create_supplier_with_url_connection_type(self):
        """Test creating supplier with connection_type='url' and file_url"""
        payload = {
            "name": f"TEST_URL_Supplier_{uuid.uuid4().hex[:8]}",
            "description": "Test supplier with URL connection",
            "connection_type": "url",
            "file_url": "https://people.sc.fsu.edu/~jburkardt/data/csv/airtravel.csv",
            "file_format": "csv"
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        
        assert response.status_code == 200, f"Create supplier failed: {response.text}"
        data = response.json()
        
        # Verify connection_type is stored correctly
        assert data["connection_type"] == "url", f"Expected connection_type='url', got {data.get('connection_type')}"
        
        # Verify file_url is stored
        assert data.get("file_url") == payload["file_url"], f"file_url not stored correctly"
        
        # Store for cleanup
        self.created_supplier_ids.append(data["id"])
        print(f"✓ Created supplier with URL connection: {data['id']}")

    def test_create_supplier_with_ftp_connection_type(self):
        """Test creating supplier with connection_type='ftp' (default behavior)"""
        payload = {
            "name": f"TEST_FTP_Supplier_{uuid.uuid4().hex[:8]}",
            "description": "Test supplier with FTP connection",
            "connection_type": "ftp",
            "ftp_host": "ftp.example.com",
            "ftp_port": 21,
            "ftp_path": "/data/products.csv",
            "file_format": "csv"
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        
        assert response.status_code == 200, f"Create supplier failed: {response.text}"
        data = response.json()
        
        # Verify connection_type defaults to ftp
        assert data["connection_type"] == "ftp", f"Expected connection_type='ftp', got {data.get('connection_type')}"
        assert data.get("ftp_host") == payload["ftp_host"]
        
        self.created_supplier_ids.append(data["id"])
        print(f"✓ Created supplier with FTP connection: {data['id']}")

    def test_create_supplier_default_connection_type(self):
        """Test that connection_type defaults to 'ftp' when not specified"""
        payload = {
            "name": f"TEST_Default_Supplier_{uuid.uuid4().hex[:8]}",
            "description": "Test supplier with default connection type"
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        
        assert response.status_code == 200, f"Create supplier failed: {response.text}"
        data = response.json()
        
        # Default should be ftp
        assert data["connection_type"] == "ftp", f"Expected default connection_type='ftp', got {data.get('connection_type')}"
        
        self.created_supplier_ids.append(data["id"])
        print(f"✓ Supplier defaults to FTP connection type")

    # ==================== POST /api/suppliers/{id}/sync with URL ====================

    def test_sync_supplier_with_url_success(self):
        """Test syncing supplier that uses URL connection downloads from HTTP/HTTPS"""
        # Create supplier with URL
        payload = {
            "name": f"TEST_Sync_URL_{uuid.uuid4().hex[:8]}",
            "connection_type": "url",
            "file_url": "https://people.sc.fsu.edu/~jburkardt/data/csv/airtravel.csv",
            "file_format": "csv",
            "csv_separator": ","
        }
        
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        assert create_response.status_code == 200, f"Create supplier failed: {create_response.text}"
        supplier_id = create_response.json()["id"]
        self.created_supplier_ids.append(supplier_id)
        
        # Trigger sync
        sync_response = requests.post(f"{BASE_URL}/api/suppliers/{supplier_id}/sync", headers=self.headers)
        
        assert sync_response.status_code == 200, f"Sync failed: {sync_response.text}"
        sync_data = sync_response.json()
        
        # Check sync result - status should be 'success' (though products may not import due to CSV format)
        assert sync_data.get("status") == "success", f"Sync status not success: {sync_data}"
        print(f"✓ Sync from URL completed: imported={sync_data.get('imported')}, updated={sync_data.get('updated')}, errors={sync_data.get('errors')}")
        
        # Verify detected_columns were captured
        supplier_response = requests.get(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=self.headers)
        assert supplier_response.status_code == 200
        supplier_data = supplier_response.json()
        assert supplier_data.get("detected_columns") is not None, "detected_columns should be set after sync"
        print(f"✓ Detected columns: {supplier_data.get('detected_columns')}")

    def test_sync_supplier_with_url_missing_url_fails(self):
        """Test that sync fails with proper error when URL is not configured"""
        # Create supplier with URL type but no file_url
        payload = {
            "name": f"TEST_NoURL_{uuid.uuid4().hex[:8]}",
            "connection_type": "url"
            # file_url is intentionally missing
        }
        
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        assert create_response.status_code == 200, f"Create supplier failed: {create_response.text}"
        supplier_id = create_response.json()["id"]
        self.created_supplier_ids.append(supplier_id)
        
        # Trigger sync - should fail with 400
        sync_response = requests.post(f"{BASE_URL}/api/suppliers/{supplier_id}/sync", headers=self.headers)
        
        assert sync_response.status_code == 400, f"Expected 400 for missing URL, got {sync_response.status_code}: {sync_response.text}"
        error_data = sync_response.json()
        assert "URL" in error_data.get("detail", ""), f"Error should mention URL: {error_data}"
        print(f"✓ Missing URL properly returns 400 error")

    def test_sync_supplier_ftp_missing_config_fails(self):
        """Test that FTP sync fails properly when FTP is not configured"""
        # Create supplier with FTP type but no FTP config
        payload = {
            "name": f"TEST_NoFTP_{uuid.uuid4().hex[:8]}",
            "connection_type": "ftp"
            # ftp_host and ftp_path are intentionally missing
        }
        
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        assert create_response.status_code == 200, f"Create supplier failed: {create_response.text}"
        supplier_id = create_response.json()["id"]
        self.created_supplier_ids.append(supplier_id)
        
        # Trigger sync - should fail with 400
        sync_response = requests.post(f"{BASE_URL}/api/suppliers/{supplier_id}/sync", headers=self.headers)
        
        assert sync_response.status_code == 400, f"Expected 400 for missing FTP config, got {sync_response.status_code}: {sync_response.text}"
        error_data = sync_response.json()
        assert "FTP" in error_data.get("detail", ""), f"Error should mention FTP: {error_data}"
        print(f"✓ Missing FTP config properly returns 400 error")

    # ==================== Update supplier connection type ====================

    def test_update_supplier_change_to_url(self):
        """Test updating supplier from FTP to URL connection"""
        # Create with FTP
        payload = {
            "name": f"TEST_Switch_{uuid.uuid4().hex[:8]}",
            "connection_type": "ftp",
            "ftp_host": "ftp.example.com"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        assert create_response.status_code == 200
        supplier_id = create_response.json()["id"]
        self.created_supplier_ids.append(supplier_id)
        
        # Update to URL
        update_payload = {
            "connection_type": "url",
            "file_url": "https://example.com/products.csv"
        }
        
        update_response = requests.put(f"{BASE_URL}/api/suppliers/{supplier_id}", json=update_payload, headers=self.headers)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated_data = update_response.json()
        assert updated_data["connection_type"] == "url"
        assert updated_data["file_url"] == "https://example.com/products.csv"
        print(f"✓ Supplier connection type updated from FTP to URL")

    # ==================== GET supplier reflects connection type ====================

    def test_get_supplier_returns_url_fields(self):
        """Test that GET /api/suppliers/{id} returns URL-related fields"""
        payload = {
            "name": f"TEST_GetURL_{uuid.uuid4().hex[:8]}",
            "connection_type": "url",
            "file_url": "https://example.com/data.csv"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        assert create_response.status_code == 200
        supplier_id = create_response.json()["id"]
        self.created_supplier_ids.append(supplier_id)
        
        # GET the supplier
        get_response = requests.get(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=self.headers)
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["connection_type"] == "url"
        assert data["file_url"] == "https://example.com/data.csv"
        print(f"✓ GET supplier returns connection_type and file_url correctly")

    def test_list_suppliers_includes_connection_type(self):
        """Test that GET /api/suppliers list includes connection_type for each supplier"""
        # Create one URL supplier
        payload = {
            "name": f"TEST_ListURL_{uuid.uuid4().hex[:8]}",
            "connection_type": "url",
            "file_url": "https://test.com/data.csv"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        assert create_response.status_code == 200
        self.created_supplier_ids.append(create_response.json()["id"])
        
        # List all suppliers
        list_response = requests.get(f"{BASE_URL}/api/suppliers", headers=self.headers)
        assert list_response.status_code == 200
        
        suppliers = list_response.json()
        assert len(suppliers) > 0
        
        # Find our test supplier
        test_supplier = next((s for s in suppliers if s["id"] == self.created_supplier_ids[-1]), None)
        assert test_supplier is not None
        assert test_supplier["connection_type"] == "url"
        print(f"✓ Supplier list includes connection_type field")


class TestURLDownloadFunction:
    """Test the actual URL download functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser@example.com",
            "password": "Test1234!"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.created_supplier_ids = []
        yield
        for sid in self.created_supplier_ids:
            try:
                requests.delete(f"{BASE_URL}/api/suppliers/{sid}", headers=self.headers)
            except:
                pass

    def test_sync_downloads_real_csv_from_url(self):
        """Test downloading a real CSV from a public URL"""
        # Use a real public CSV
        payload = {
            "name": f"TEST_RealCSV_{uuid.uuid4().hex[:8]}",
            "connection_type": "url",
            "file_url": "https://people.sc.fsu.edu/~jburkardt/data/csv/cities.csv",
            "file_format": "csv",
            "csv_separator": ","
        }
        
        create_response = requests.post(f"{BASE_URL}/api/suppliers", json=payload, headers=self.headers)
        assert create_response.status_code == 200
        supplier_id = create_response.json()["id"]
        self.created_supplier_ids.append(supplier_id)
        
        # Sync
        sync_response = requests.post(f"{BASE_URL}/api/suppliers/{supplier_id}/sync", headers=self.headers)
        assert sync_response.status_code == 200, f"Sync failed: {sync_response.text}"
        
        sync_data = sync_response.json()
        assert sync_data.get("status") == "success"
        
        # Verify columns were detected from the CSV
        get_response = requests.get(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=self.headers)
        supplier = get_response.json()
        
        detected_cols = supplier.get("detected_columns", [])
        assert len(detected_cols) > 0, "Should detect columns from CSV"
        print(f"✓ Downloaded and processed CSV from URL. Detected columns: {detected_cols}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
