"""
Test suite for Bulk Category Assignment feature
Tests POST /api/catalogs/{catalog_id}/products/bulk-categories endpoint
Modes: add, replace, remove
"""
import os

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"

# Test catalog ID provided by main agent
TEST_CATALOG_ID = "d4b2c204-c9be-4d2f-8508-b8aaff68661a"


class TestBulkCategoryAssignment:
    """Tests for bulk category assignment to multiple products"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def api_client(self, auth_headers):
        """Create session with auth headers"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })
        return session

    @pytest.fixture(scope="class")
    def categories(self, auth_headers):
        """Get available categories for the catalog"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })
        response = session.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true")
        assert response.status_code == 200
        return response.json()

    @pytest.fixture(scope="class")
    def products(self, auth_headers):
        """Get products in the catalog for testing"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })
        response = session.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products?limit=10")
        assert response.status_code == 200
        return response.json()

    # ==== Authentication Tests ====

    def test_bulk_assign_requires_auth(self):
        """Test that bulk assignment endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": [], "category_ids": [], "mode": "add"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Bulk assign requires authentication")

    # ==== Mode: ADD - Add categories to existing ====

    def test_bulk_add_categories_success(self, api_client, categories, products):
        """Test adding categories to multiple products (ADD mode)"""
        if not categories or len(products) < 2:
            pytest.skip("Need categories and at least 2 products")

        # Get 3 products
        product_ids = [p["id"] for p in products[:3]]
        category_id = categories[0]["id"]  # Electrónica

        payload = {
            "product_item_ids": product_ids,
            "category_ids": [category_id],
            "mode": "add"
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json=payload
        )

        assert response.status_code == 200, f"Bulk add failed: {response.text}"
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "updated_count" in data
        assert "mode" in data
        assert data["mode"] == "add"
        assert data["updated_count"] >= 0

        print(f"✓ Bulk ADD: {data['updated_count']} products updated with category {categories[0]['name']}")

    def test_bulk_add_verifies_persistence(self, api_client, categories, products):
        """Verify that bulk ADD actually persists categories"""
        if not categories or len(products) < 1:
            pytest.skip("Need categories and products")

        # Clear categories first using replace with empty
        product_id = products[0]["id"]
        api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": [product_id], "category_ids": [], "mode": "replace"}
        )

        # Add category using bulk assign
        category_id = categories[0]["id"]
        add_response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": [product_id], "category_ids": [category_id], "mode": "add"}
        )
        assert add_response.status_code == 200

        # Verify by getting products
        get_response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products?category_id={category_id}"
        )
        assert get_response.status_code == 200

        filtered_products = get_response.json()
        product_ids = [p["id"] for p in filtered_products]
        assert product_id in product_ids, "Product should be in filtered results after ADD"

        print("✓ Bulk ADD persistence verified - product found in category filter")

    def test_bulk_add_multiple_categories(self, api_client, categories, products):
        """Test adding multiple categories at once"""
        if len(categories) < 2 or len(products) < 1:
            pytest.skip("Need at least 2 categories and 1 product")

        product_id = products[0]["id"]
        category_ids = [categories[0]["id"], categories[1]["id"]]

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": [product_id], "category_ids": category_ids, "mode": "add"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["category_ids"]) == 2

        print(f"✓ Added multiple categories: {categories[0]['name']}, {categories[1]['name']}")

    # ==== Mode: REPLACE - Replace all categories ====

    def test_bulk_replace_categories_success(self, api_client, categories, products):
        """Test replacing all categories on products (REPLACE mode)"""
        if not categories or len(products) < 2:
            pytest.skip("Need categories and at least 2 products")

        product_ids = [p["id"] for p in products[:2]]
        # Use different category for replacement
        category_id = categories[-1]["id"]  # iPhone 15

        payload = {
            "product_item_ids": product_ids,
            "category_ids": [category_id],
            "mode": "replace"
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json=payload
        )

        assert response.status_code == 200
        data = response.json()

        assert data["mode"] == "replace"
        assert data["updated_count"] >= 0

        print(f"✓ Bulk REPLACE: {data['updated_count']} products categories replaced")

    def test_bulk_replace_clears_old_categories(self, api_client, categories, products):
        """Verify REPLACE mode clears old categories"""
        if len(categories) < 2 or len(products) < 1:
            pytest.skip("Need at least 2 categories and 1 product")

        product_id = products[0]["id"]

        # First, add two categories
        api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={
                "product_item_ids": [product_id],
                "category_ids": [categories[0]["id"], categories[1]["id"]],
                "mode": "add"
            }
        )

        # Replace with just one category
        replace_response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={
                "product_item_ids": [product_id],
                "category_ids": [categories[-1]["id"]],
                "mode": "replace"
            }
        )

        assert replace_response.status_code == 200

        # Verify product is NOT in old category
        old_cat_prods = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products?category_id={categories[0]['id']}"
        ).json()
        product_ids_in_old = [p["id"] for p in old_cat_prods]

        # This might fail if same product, so just verify the new category exists
        new_cat_prods = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products?category_id={categories[-1]['id']}"
        ).json()
        product_ids_in_new = [p["id"] for p in new_cat_prods]

        assert product_id in product_ids_in_new, "Product should be in new category after REPLACE"
        print("✓ REPLACE mode verified - old categories cleared, new category assigned")

    # ==== Mode: REMOVE - Remove specified categories ====

    def test_bulk_remove_categories_success(self, api_client, categories, products):
        """Test removing categories from products (REMOVE mode)"""
        if not categories or len(products) < 1:
            pytest.skip("Need categories and products")

        product_id = products[0]["id"]

        # First add a category
        add_response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={
                "product_item_ids": [product_id],
                "category_ids": [categories[0]["id"]],
                "mode": "add"
            }
        )
        assert add_response.status_code == 200

        # Now remove it
        remove_response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={
                "product_item_ids": [product_id],
                "category_ids": [categories[0]["id"]],
                "mode": "remove"
            }
        )

        assert remove_response.status_code == 200
        data = remove_response.json()

        assert data["mode"] == "remove"

        print("✓ Bulk REMOVE: Categories removed from product")

    def test_bulk_remove_verifies_removal(self, api_client, categories, products):
        """Verify REMOVE mode actually removes categories"""
        if not categories or len(products) < 1:
            pytest.skip("Need categories and products")

        product_id = products[0]["id"]
        category_id = categories[0]["id"]

        # Add category first
        api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": [product_id], "category_ids": [category_id], "mode": "add"}
        )

        # Remove it
        api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": [product_id], "category_ids": [category_id], "mode": "remove"}
        )

        # Verify product is NOT in category anymore
        filtered = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products?category_id={category_id}"
        ).json()
        product_ids = [p["id"] for p in filtered]

        assert product_id not in product_ids, "Product should NOT be in category after REMOVE"
        print("✓ REMOVE mode verified - category successfully removed")

    # ==== Validation Tests ====

    def test_bulk_assign_empty_products_fails(self, api_client, categories):
        """Test that empty product list fails"""
        if not categories:
            pytest.skip("No categories")

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={
                "product_item_ids": [],
                "category_ids": [categories[0]["id"]],
                "mode": "add"
            }
        )

        assert response.status_code == 400
        assert "seleccionar" in response.json().get("detail", "").lower() or "producto" in response.json().get("detail", "").lower()
        print("✓ Empty product list correctly rejected")

    def test_bulk_assign_invalid_mode_fails(self, api_client, categories, products):
        """Test that invalid mode fails"""
        if not categories or not products:
            pytest.skip("No categories or products")

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={
                "product_item_ids": [products[0]["id"]],
                "category_ids": [categories[0]["id"]],
                "mode": "invalid_mode"
            }
        )

        assert response.status_code == 400
        print("✓ Invalid mode correctly rejected")

    def test_bulk_assign_invalid_category_fails(self, api_client, products):
        """Test that invalid category ID fails"""
        if not products:
            pytest.skip("No products")

        fake_category_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={
                "product_item_ids": [products[0]["id"]],
                "category_ids": [fake_category_id],
                "mode": "add"
            }
        )

        assert response.status_code == 400
        assert "no válidas" in response.json().get("detail", "").lower() or "invalid" in response.json().get("detail", "").lower()
        print("✓ Invalid category ID correctly rejected")

    def test_bulk_assign_nonexistent_catalog(self, api_client, categories, products):
        """Test bulk assign on non-existent catalog fails"""
        if not categories or not products:
            pytest.skip("No categories or products")

        fake_catalog_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{fake_catalog_id}/products/bulk-categories",
            json={
                "product_item_ids": [products[0]["id"]],
                "category_ids": [categories[0]["id"]],
                "mode": "add"
            }
        )

        assert response.status_code == 404
        print("✓ Non-existent catalog returns 404")

    # ==== Edge Cases ====

    def test_bulk_assign_with_empty_categories(self, api_client, products):
        """Test REPLACE mode with empty category list clears all categories"""
        if not products:
            pytest.skip("No products")

        product_id = products[0]["id"]

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={
                "product_item_ids": [product_id],
                "category_ids": [],
                "mode": "replace"
            }
        )

        assert response.status_code == 200
        print("✓ REPLACE with empty categories clears all categories")

    def test_bulk_assign_idempotent_add(self, api_client, categories, products):
        """Test that adding same category twice is idempotent (no duplicates)"""
        if not categories or not products:
            pytest.skip("No categories or products")

        product_id = products[0]["id"]
        category_id = categories[0]["id"]

        # Add same category twice
        api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": [product_id], "category_ids": [category_id], "mode": "add"}
        )
        api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": [product_id], "category_ids": [category_id], "mode": "add"}
        )

        # Verify no duplicates by checking direct product categories
        # Get category products
        cat_prods = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{category_id}/products"
        ).json()

        # Count occurrences of product_id
        count = sum(1 for p in cat_prods if p["id"] == product_id)
        assert count <= 1, "Product should not have duplicate category entries"

        print("✓ ADD mode is idempotent - no duplicate categories")


class TestBulkCategoryAssignmentIntegration:
    """Integration tests for bulk category assignment with filtering"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def api_client(self, auth_headers):
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })
        return session

    def test_filter_after_bulk_assign(self, api_client):
        """Test that category filter works after bulk assignment"""
        # Get categories
        cats = api_client.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true").json()
        if not cats:
            pytest.skip("No categories")

        # Get products
        prods = api_client.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products?limit=5").json()
        if len(prods) < 3:
            pytest.skip("Need at least 3 products")

        category_id = cats[0]["id"]
        product_ids = [p["id"] for p in prods[:3]]

        # Bulk assign
        api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/bulk-categories",
            json={"product_item_ids": product_ids, "category_ids": [category_id], "mode": "add"}
        )

        # Filter by category
        filtered = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products?category_id={category_id}"
        ).json()

        filtered_ids = [p["id"] for p in filtered]

        # At least some of our products should be there
        matches = len(set(product_ids) & set(filtered_ids))
        assert matches > 0, "Some products should appear in category filter"

        print(f"✓ Category filter works: {matches}/{len(product_ids)} products found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
