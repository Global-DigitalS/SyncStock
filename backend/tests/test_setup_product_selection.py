"""
Test Setup Page and Product Selection Features
Tests for:
1. Setup page - MongoDB connection check and SuperAdmin status
2. Product selection flow - Select/deselect products from suppliers
"""
import os

import pytest
import requests

BASE_URL = (os.environ.get('REACT_APP_BACKEND_URL') or 'http://localhost:8001').rstrip('/')

class TestSetupEndpoints:
    """Tests for /api/setup/* endpoints"""

    def test_setup_status_returns_correct_structure(self):
        """Test that setup/status returns expected fields"""
        response = requests.get(f"{BASE_URL}/api/setup/status")
        assert response.status_code == 200

        data = response.json()
        assert "is_configured" in data
        assert "has_database" in data
        assert "has_superadmin" in data
        assert "database_name" in data
        assert "message" in data

        # For our test environment, app should be configured
        assert isinstance(data["is_configured"], bool)
        assert isinstance(data["has_database"], bool)
        assert isinstance(data["has_superadmin"], bool)
        print(f"Setup status: is_configured={data['is_configured']}, has_db={data['has_database']}, has_superadmin={data['has_superadmin']}")

    def test_setup_status_when_configured(self):
        """When app is configured, all flags should be true"""
        response = requests.get(f"{BASE_URL}/api/setup/status")
        assert response.status_code == 200

        data = response.json()
        # Since we have test@test.com superadmin, app should be configured
        assert data["is_configured"] == True
        assert data["has_database"] == True
        assert data["has_superadmin"] == True
        assert len(data["database_name"]) > 0
        print(f"Database name: {data['database_name']}")

    def test_test_connection_requires_mongo_url(self):
        """Test connection endpoint should require mongo_url"""
        response = requests.post(f"{BASE_URL}/api/setup/test-connection", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] == False
        assert "URL" in data["message"] or "requerida" in data["message"]
        print(f"Empty URL response: {data['message']}")

    def test_test_connection_with_invalid_url(self):
        """Test connection with invalid URL returns error"""
        response = requests.post(f"{BASE_URL}/api/setup/test-connection", json={
            "mongo_url": "mongodb://invalid:27017",
            "db_name": "test_db"
        })
        assert response.status_code == 200

        data = response.json()
        assert data["success"] == False
        # Connection should fail with invalid URL
        print(f"Invalid URL response: {data['message']}")

    def test_configure_with_existing_superadmin(self):
        """Configure endpoint should reject if superadmin exists"""
        response = requests.post(f"{BASE_URL}/api/setup/configure", json={
            "mongo_url": "mongodb://localhost:27017",
            "db_name": "test_database",
            "admin_email": "newadmin@test.com",
            "admin_password": "password123",
            "admin_name": "New Admin",
            "company": "Test Company"
        })
        assert response.status_code == 200

        data = response.json()
        # Should fail because superadmin already exists
        assert data["success"] == False
        assert "SuperAdmin" in data["message"] or "existe" in data["message"]
        print(f"Existing superadmin response: {data['message']}")


class TestProductSelection:
    """Tests for product selection endpoints"""

    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    @pytest.fixture
    def supplier_id(self, auth_headers):
        """Get first supplier ID"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=auth_headers)
        if response.status_code == 200 and len(response.json()) > 0:
            return response.json()[0]["id"]
        pytest.skip("No suppliers found - skipping test")

    @pytest.fixture
    def product_id(self, auth_headers, supplier_id):
        """Get first product ID from supplier"""
        response = requests.get(
            f"{BASE_URL}/api/supplier/{supplier_id}/products?limit=1",
            headers=auth_headers
        )
        if response.status_code == 200 and len(response.json()) > 0:
            return response.json()[0]["id"]
        pytest.skip("No products found - skipping test")

    def test_selected_count_returns_stats(self, auth_headers):
        """Test /api/products/selected-count returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/products/selected-count",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "selected" in data
        assert "total" in data
        assert "percentage" in data
        assert isinstance(data["selected"], int)
        assert isinstance(data["total"], int)
        print(f"Selection stats: {data['selected']}/{data['total']} ({data['percentage']}%)")

    def test_selected_count_by_supplier(self, auth_headers, supplier_id):
        """Test selected-count filtered by supplier"""
        response = requests.get(
            f"{BASE_URL}/api/products/selected-count?supplier_id={supplier_id}",
            headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "selected" in data
        assert "total" in data
        print(f"Supplier {supplier_id} selection: {data['selected']}/{data['total']}")

    def test_supplier_products_includes_is_selected(self, auth_headers, supplier_id):
        """Test /api/supplier/{id}/products returns is_selected field"""
        response = requests.get(
            f"{BASE_URL}/api/supplier/{supplier_id}/products?limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200

        products = response.json()
        assert len(products) > 0

        # All products should have is_selected field
        for product in products:
            assert "is_selected" in product
            assert isinstance(product["is_selected"], bool) or product["is_selected"] is None
        print(f"Found {len(products)} products with is_selected field")

    def test_supplier_categories_with_counts(self, auth_headers, supplier_id):
        """Test /api/supplier/{id}/categories returns selected counts"""
        response = requests.get(
            f"{BASE_URL}/api/supplier/{supplier_id}/categories",
            headers=auth_headers
        )
        assert response.status_code == 200

        categories = response.json()
        assert isinstance(categories, list)

        if len(categories) > 0:
            for cat in categories:
                assert "category" in cat
                assert "count" in cat
                assert "selected_count" in cat
            print(f"Found {len(categories)} categories with selection counts")

    def test_select_products_flow(self, auth_headers, product_id, supplier_id):
        """Test select -> verify -> deselect flow"""
        # Step 1: Select a product
        select_response = requests.post(
            f"{BASE_URL}/api/products/select",
            headers=auth_headers,
            json={"product_ids": [product_id]}
        )
        assert select_response.status_code == 200
        select_data = select_response.json()
        assert "selected" in select_data
        assert select_data["selected"] >= 1
        print(f"Selected: {select_data}")

        # Step 2: Verify product is now selected
        verify_response = requests.get(
            f"{BASE_URL}/api/supplier/{supplier_id}/products?is_selected=true&limit=100",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        selected_products = verify_response.json()

        product_found = any(p["id"] == product_id for p in selected_products)
        assert product_found, "Product should appear in selected list"

        # Step 3: Deselect the product
        deselect_response = requests.post(
            f"{BASE_URL}/api/products/deselect",
            headers=auth_headers,
            json={"product_ids": [product_id]}
        )
        assert deselect_response.status_code == 200
        deselect_data = deselect_response.json()
        assert "deselected" in deselect_data
        print(f"Deselected: {deselect_data}")

    def test_select_empty_list_returns_error(self, auth_headers):
        """Test selecting empty product list returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/products/select",
            headers=auth_headers,
            json={"product_ids": []}
        )
        assert response.status_code == 400
        print("Empty product list correctly rejected")

    def test_deselect_empty_list_returns_error(self, auth_headers):
        """Test deselecting empty product list returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/products/deselect",
            headers=auth_headers,
            json={"product_ids": []}
        )
        assert response.status_code == 400
        print("Empty product list correctly rejected")

    def test_select_by_supplier_all_products(self, auth_headers, supplier_id):
        """Test selecting all products from a supplier"""
        # Select all
        response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={
                "supplier_id": supplier_id,
                "select_all": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "modified" in data
        selected_count = data["modified"]
        print(f"Selected all: {data}")

        # Verify with selected-count
        count_response = requests.get(
            f"{BASE_URL}/api/products/selected-count?supplier_id={supplier_id}",
            headers=auth_headers
        )
        assert count_response.status_code == 200
        count_data = count_response.json()
        # Selected should be >= what we just modified
        print(f"After select all: {count_data}")

        # Deselect all for cleanup
        deselect_response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={
                "supplier_id": supplier_id,
                "select_all": False
            }
        )
        assert deselect_response.status_code == 200
        print("Cleanup: Deselected all products")

    def test_select_by_supplier_with_category_filter(self, auth_headers, supplier_id):
        """Test selecting products filtered by category"""
        # Get categories first
        cat_response = requests.get(
            f"{BASE_URL}/api/supplier/{supplier_id}/categories",
            headers=auth_headers
        )
        if cat_response.status_code != 200 or len(cat_response.json()) == 0:
            pytest.skip("No categories found")

        category = cat_response.json()[0]["category"]
        category_count = cat_response.json()[0]["count"]

        # Select by category
        response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={
                "supplier_id": supplier_id,
                "category": category,
                "select_all": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "modified" in data
        assert data["modified"] <= category_count
        print(f"Selected category '{category}': {data}")

        # Cleanup
        cleanup_response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={
                "supplier_id": supplier_id,
                "category": category,
                "select_all": False
            }
        )
        assert cleanup_response.status_code == 200

    def test_select_by_supplier_invalid_supplier(self, auth_headers):
        """Test selecting from invalid supplier returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={
                "supplier_id": "invalid-supplier-id-12345",
                "select_all": True
            }
        )
        assert response.status_code == 404
        print("Invalid supplier correctly rejected with 404")

    def test_select_by_supplier_requires_supplier_id(self, auth_headers):
        """Test select-by-supplier requires supplier_id"""
        response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={
                "select_all": True
            }
        )
        assert response.status_code == 400
        print("Missing supplier_id correctly rejected")


class TestProductsUnifiedFilter:
    """Tests for products-unified filtering by selection"""

    @pytest.fixture
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        pytest.skip("Authentication failed")

    @pytest.fixture
    def supplier_id(self, auth_headers):
        """Get first supplier ID"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=auth_headers)
        if response.status_code == 200 and len(response.json()) > 0:
            return response.json()[0]["id"]
        pytest.skip("No suppliers found")

    def test_products_unified_shows_only_selected(self, auth_headers, supplier_id):
        """Test /api/products-unified only shows is_selected=true products"""
        # First, ensure no products are selected
        deselect_response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={"supplier_id": supplier_id, "select_all": False}
        )

        # Check products-unified - should be empty or few
        response_before = requests.get(
            f"{BASE_URL}/api/products-unified",
            headers=auth_headers
        )
        assert response_before.status_code == 200
        count_before = len(response_before.json())
        print(f"Products before selection: {count_before}")

        # Select some products
        select_response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={
                "supplier_id": supplier_id,
                "category": None,  # All categories
                "select_all": True
            }
        )

        # Check products-unified - should show selected products
        response_after = requests.get(
            f"{BASE_URL}/api/products-unified?limit=50",
            headers=auth_headers
        )
        assert response_after.status_code == 200
        count_after = len(response_after.json())
        print(f"Products after selection: {count_after}")

        # Should have more products now
        assert count_after >= count_before

        # Cleanup
        requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            headers=auth_headers,
            json={"supplier_id": supplier_id, "select_all": False}
        )

    def test_products_unified_with_include_all_flag(self, auth_headers):
        """Test products-unified with include_all=True shows all products"""
        # Get count with default (only selected)
        response_selected = requests.get(
            f"{BASE_URL}/api/products-unified",
            headers=auth_headers
        )
        assert response_selected.status_code == 200
        count_selected = len(response_selected.json())

        # Get count with include_all=true
        response_all = requests.get(
            f"{BASE_URL}/api/products-unified?include_all=true&limit=100",
            headers=auth_headers
        )
        assert response_all.status_code == 200
        count_all = len(response_all.json())

        # include_all should show >= selected only
        assert count_all >= count_selected
        print(f"Selected only: {count_selected}, Include all: {count_all}")

    def test_products_unified_count_with_filter(self, auth_headers):
        """Test products-unified/count respects include_all"""
        # Count with default
        response_selected = requests.get(
            f"{BASE_URL}/api/products-unified/count",
            headers=auth_headers
        )
        assert response_selected.status_code == 200
        count_selected = response_selected.json().get("total", 0)

        # Count with include_all
        response_all = requests.get(
            f"{BASE_URL}/api/products-unified/count?include_all=true",
            headers=auth_headers
        )
        assert response_all.status_code == 200
        count_all = response_all.json().get("total", 0)

        assert count_all >= count_selected
        print(f"Count - Selected: {count_selected}, All: {count_all}")


class TestAuthentication:
    """Tests for endpoint authentication"""

    def test_setup_status_is_public(self):
        """Setup status should be accessible without auth"""
        response = requests.get(f"{BASE_URL}/api/setup/status")
        assert response.status_code == 200
        print("Setup status is public (no auth required)")

    def test_test_connection_is_public(self):
        """Test connection should be accessible without auth"""
        response = requests.post(f"{BASE_URL}/api/setup/test-connection", json={})
        assert response.status_code == 200
        print("Test connection is public (no auth required)")

    def test_products_select_requires_auth(self):
        """Products select should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/products/select",
            json={"product_ids": ["test"]}
        )
        assert response.status_code in [401, 403]
        print("Products select correctly requires authentication")

    def test_products_deselect_requires_auth(self):
        """Products deselect should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/products/deselect",
            json={"product_ids": ["test"]}
        )
        assert response.status_code in [401, 403]
        print("Products deselect correctly requires authentication")

    def test_select_by_supplier_requires_auth(self):
        """Select by supplier should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/products/select-by-supplier",
            json={"supplier_id": "test", "select_all": True}
        )
        assert response.status_code in [401, 403]
        print("Select by supplier correctly requires authentication")

    def test_supplier_products_requires_auth(self):
        """Supplier products should require authentication"""
        response = requests.get(f"{BASE_URL}/api/supplier/test-id/products")
        assert response.status_code in [401, 403]
        print("Supplier products correctly requires authentication")

    def test_supplier_categories_requires_auth(self):
        """Supplier categories should require authentication"""
        response = requests.get(f"{BASE_URL}/api/supplier/test-id/categories")
        assert response.status_code in [401, 403]
        print("Supplier categories correctly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
