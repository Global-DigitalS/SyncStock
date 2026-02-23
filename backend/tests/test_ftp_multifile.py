"""
Test file for FTP Browser and Multi-File Sync features
Tests:
- POST /api/suppliers/ftp-browse - connects to FTP and lists files
- POST /api/suppliers - create supplier with ftp_paths field  
- PUT /api/suppliers/{id} - update supplier with ftp_paths
- GET /api/suppliers - returns ftp_paths in response
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"

# FTP test credentials (real TechData server)
FTP_HOST = "ftp2.techdata-it-emea.com"
FTP_USER = "564195"
FTP_PASSWORD = "564195ELI"
FTP_PORT = 21


class TestAuth:
    """Authentication for supplier tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        
        # If login fails, try to register
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": "Test User"
        }, timeout=15)
        
        if reg_response.status_code in [200, 201]:
            # Login again
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }, timeout=15)
            if login_resp.status_code == 200:
                return login_resp.json().get("token")
        
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Headers with authorization"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }


class TestFtpBrowse(TestAuth):
    """Test FTP browser endpoint"""
    
    def test_ftp_browse_real_server(self, auth_headers):
        """Test FTP browse endpoint with real TechData server"""
        print(f"\n[TEST] Connecting to FTP: {FTP_HOST}")
        
        response = requests.post(
            f"{BASE_URL}/api/suppliers/ftp-browse",
            headers=auth_headers,
            json={
                "ftp_host": FTP_HOST,
                "ftp_user": FTP_USER,
                "ftp_password": FTP_PASSWORD,
                "ftp_port": FTP_PORT,
                "ftp_mode": "passive",
                "path": "/"
            },
            timeout=20  # FTP can take 5-8 seconds
        )
        
        print(f"[TEST] FTP browse response status: {response.status_code}")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        print(f"[TEST] FTP browse response: status={data.get('status')}, file_count={len(data.get('files', []))}")
        
        assert data.get("status") == "ok", f"Expected status 'ok', got {data.get('status')}"
        assert "files" in data, "Response should contain 'files' field"
        assert isinstance(data["files"], list), "files should be a list"
        
        # Should have at least some files/directories
        files = data["files"]
        if len(files) > 0:
            print(f"[TEST] Files found: {[f['name'] for f in files[:5]]}...")
            
            # Each file should have required fields
            first_file = files[0]
            assert "name" in first_file, "File should have 'name'"
            assert "path" in first_file, "File should have 'path'"
            assert "is_dir" in first_file, "File should have 'is_dir'"
        else:
            print("[TEST] No files found in root directory (may be empty or restricted)")
    
    def test_ftp_browse_invalid_credentials(self, auth_headers):
        """Test FTP browse with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/suppliers/ftp-browse",
            headers=auth_headers,
            json={
                "ftp_host": FTP_HOST,
                "ftp_user": "invalid_user",
                "ftp_password": "invalid_password",
                "path": "/"
            },
            timeout=20
        )
        
        # Should return 200 with error status (or 400/500)
        data = response.json()
        print(f"[TEST] Invalid FTP response: status={data.get('status')}, message={data.get('message', '')[:100]}")
        
        # Either error status or HTTP error
        if response.status_code == 200:
            assert data.get("status") == "error", "Should return error status for invalid credentials"
    
    def test_ftp_browse_without_auth(self):
        """Test FTP browse endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/suppliers/ftp-browse",
            json={
                "ftp_host": FTP_HOST,
                "ftp_user": FTP_USER,
                "ftp_password": FTP_PASSWORD,
                "path": "/"
            },
            timeout=15
        )
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


class TestSupplierCRUDWithFtpPaths(TestAuth):
    """Test supplier CRUD with ftp_paths field for multi-file sync"""
    
    created_supplier_id = None
    
    def test_create_supplier_with_ftp_paths(self, auth_headers):
        """Test creating supplier with ftp_paths array"""
        ftp_paths = [
            {
                "path": "/test/StockFile.txt",
                "role": "stock",
                "label": "Stock File",
                "separator": ";",
                "header_row": 1
            },
            {
                "path": "/test/Products.zip",
                "role": "products",
                "label": "Products ZIP",
                "separator": ";",
                "header_row": 1
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/suppliers",
            headers=auth_headers,
            json={
                "name": "TEST_FTP_MultiFile_Supplier",
                "description": "Test supplier with multiple FTP files",
                "connection_type": "ftp",
                "ftp_schema": "ftp",
                "ftp_host": FTP_HOST,
                "ftp_user": FTP_USER,
                "ftp_password": FTP_PASSWORD,
                "ftp_port": FTP_PORT,
                "ftp_mode": "passive",
                "ftp_paths": ftp_paths,
                "file_format": "csv",
                "csv_separator": ";"
            },
            timeout=15
        )
        
        print(f"[TEST] Create supplier response: {response.status_code}")
        
        # Status assertion
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "id" in data, "Response should contain 'id'"
        assert data["name"] == "TEST_FTP_MultiFile_Supplier"
        assert "ftp_paths" in data, "Response should contain 'ftp_paths'"
        assert isinstance(data["ftp_paths"], list), "ftp_paths should be a list"
        assert len(data["ftp_paths"]) == 2, f"Expected 2 ftp_paths, got {len(data['ftp_paths'])}"
        
        # Verify ftp_paths structure
        first_path = data["ftp_paths"][0]
        assert first_path["path"] == "/test/StockFile.txt"
        assert first_path["role"] == "stock"
        
        # Store supplier ID for later tests
        TestSupplierCRUDWithFtpPaths.created_supplier_id = data["id"]
        print(f"[TEST] Created supplier ID: {data['id']}")
    
    def test_get_supplier_returns_ftp_paths(self, auth_headers):
        """Test GET supplier returns ftp_paths"""
        supplier_id = TestSupplierCRUDWithFtpPaths.created_supplier_id
        
        if not supplier_id:
            pytest.skip("No supplier created")
        
        response = requests.get(
            f"{BASE_URL}/api/suppliers/{supplier_id}",
            headers=auth_headers,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["id"] == supplier_id
        assert "ftp_paths" in data, "Response should contain 'ftp_paths'"
        assert len(data["ftp_paths"]) == 2, f"Expected 2 ftp_paths, got {len(data.get('ftp_paths', []))}"
        
        print(f"[TEST] GET supplier ftp_paths: {data['ftp_paths']}")
    
    def test_get_suppliers_list_returns_ftp_paths(self, auth_headers):
        """Test GET suppliers list includes ftp_paths"""
        response = requests.get(
            f"{BASE_URL}/api/suppliers",
            headers=auth_headers,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Find our test supplier
        test_supplier = next((s for s in data if s.get("name") == "TEST_FTP_MultiFile_Supplier"), None)
        
        if test_supplier:
            assert "ftp_paths" in test_supplier, "Supplier in list should have ftp_paths"
            print(f"[TEST] Found test supplier with {len(test_supplier.get('ftp_paths', []))} ftp_paths")
    
    def test_update_supplier_ftp_paths(self, auth_headers):
        """Test updating supplier ftp_paths"""
        supplier_id = TestSupplierCRUDWithFtpPaths.created_supplier_id
        
        if not supplier_id:
            pytest.skip("No supplier created")
        
        new_ftp_paths = [
            {
                "path": "/updated/NewStock.txt",
                "role": "stock",
                "label": "Updated Stock",
                "separator": ";",
                "header_row": 1
            },
            {
                "path": "/updated/Products.zip",
                "role": "products",
                "label": "Products",
                "separator": ";",
                "header_row": 1
            },
            {
                "path": "/updated/Prices.txt",
                "role": "prices",
                "label": "Prices",
                "separator": ";",
                "header_row": 1
            }
        ]
        
        response = requests.put(
            f"{BASE_URL}/api/suppliers/{supplier_id}",
            headers=auth_headers,
            json={
                "ftp_paths": new_ftp_paths
            },
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "ftp_paths" in data, "Response should contain 'ftp_paths'"
        assert len(data["ftp_paths"]) == 3, f"Expected 3 ftp_paths after update, got {len(data['ftp_paths'])}"
        
        # Verify updated path
        assert data["ftp_paths"][0]["path"] == "/updated/NewStock.txt"
        print(f"[TEST] Updated ftp_paths count: {len(data['ftp_paths'])}")
    
    def test_update_supplier_clear_ftp_paths(self, auth_headers):
        """Test clearing ftp_paths by setting to empty array"""
        supplier_id = TestSupplierCRUDWithFtpPaths.created_supplier_id
        
        if not supplier_id:
            pytest.skip("No supplier created")
        
        response = requests.put(
            f"{BASE_URL}/api/suppliers/{supplier_id}",
            headers=auth_headers,
            json={
                "ftp_paths": []
            },
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # ftp_paths should be empty or None
        ftp_paths = data.get("ftp_paths", [])
        assert ftp_paths == [] or ftp_paths is None, f"Expected empty ftp_paths, got {ftp_paths}"
        print(f"[TEST] Cleared ftp_paths: {data.get('ftp_paths')}")
    
    def test_delete_test_supplier(self, auth_headers):
        """Cleanup: delete test supplier"""
        supplier_id = TestSupplierCRUDWithFtpPaths.created_supplier_id
        
        if not supplier_id:
            pytest.skip("No supplier to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/suppliers/{supplier_id}",
            headers=auth_headers,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"[TEST] Deleted test supplier: {supplier_id}")


class TestExistingEndpoints(TestAuth):
    """Verify other existing endpoints still work"""
    
    def test_dashboard_endpoint(self, auth_headers):
        """Test dashboard endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "total_suppliers" in data, "Dashboard should have total_suppliers"
        print(f"[TEST] Dashboard stats: suppliers={data.get('total_suppliers')}, products={data.get('total_products')}")
    
    def test_products_endpoint(self, auth_headers):
        """Test products endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/products",
            headers=auth_headers,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Products should be a list"
        print(f"[TEST] Products count: {len(data)}")
    
    def test_catalogs_endpoint(self, auth_headers):
        """Test catalogs endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/catalogs",
            headers=auth_headers,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Catalogs should be a list"
        print(f"[TEST] Catalogs count: {len(data)}")
    
    def test_suppliers_list_endpoint(self, auth_headers):
        """Test suppliers list endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/suppliers",
            headers=auth_headers,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Suppliers should be a list"
        print(f"[TEST] Suppliers count: {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
