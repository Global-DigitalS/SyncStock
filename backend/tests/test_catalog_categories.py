"""
Test suite for Catalog Categories functionality
Tests CRUD operations for hierarchical categories (max 4 levels),
category assignment to products, filtering, and reordering.
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


class TestCatalogCategoriesAuth:
    """Authentication fixture for category tests"""

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


class TestCatalogCategoriesCRUD(TestCatalogCategoriesAuth):
    """Test CRUD operations for catalog categories"""

    def test_list_categories_tree(self, api_client):
        """Test listing categories as tree structure"""
        response = api_client.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories")

        assert response.status_code == 200, f"Failed to list categories: {response.text}"
        data = response.json()

        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} root categories (tree structure)")

        # If categories exist, verify structure
        if data:
            cat = data[0]
            assert "id" in cat
            assert "name" in cat
            assert "children" in cat
            assert "level" in cat
            assert "product_count" in cat
            print(f"✓ Category structure validated: {cat['name']}")

    def test_list_categories_flat(self, api_client):
        """Test listing categories as flat list"""
        response = api_client.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} categories (flat structure)")

        # Verify flat structure includes level
        if data:
            for cat in data:
                assert "level" in cat
                assert 0 <= cat["level"] <= 3  # Max 4 levels (0-3)

    def test_create_root_category(self, api_client):
        """Test creating a root category (level 0)"""
        category_data = {
            "name": "TEST_Root_Category",
            "description": "Test root category for CRUD operations"
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=category_data
        )

        assert response.status_code == 200, f"Failed to create category: {response.text}"
        data = response.json()

        assert "id" in data
        assert data["name"] == category_data["name"]
        assert data["level"] == 0  # Root level
        assert data["parent_id"] is None
        assert "created_at" in data

        self.__class__.root_category_id = data["id"]
        print(f"✓ Created root category: {data['name']} (Level 0)")

    def test_create_subcategory_level1(self, api_client):
        """Test creating a subcategory (level 1)"""
        if not hasattr(self.__class__, 'root_category_id'):
            pytest.skip("No root category to add subcategory to")

        category_data = {
            "name": "TEST_Subcategory_L1",
            "parent_id": self.__class__.root_category_id,
            "description": "Level 1 subcategory"
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=category_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["level"] == 1
        assert data["parent_id"] == self.__class__.root_category_id

        self.__class__.level1_category_id = data["id"]
        print(f"✓ Created level 1 subcategory: {data['name']}")

    def test_create_subcategory_level2(self, api_client):
        """Test creating a subcategory (level 2)"""
        if not hasattr(self.__class__, 'level1_category_id'):
            pytest.skip("No level 1 category to add subcategory to")

        category_data = {
            "name": "TEST_Subcategory_L2",
            "parent_id": self.__class__.level1_category_id,
            "description": "Level 2 subcategory"
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=category_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["level"] == 2

        self.__class__.level2_category_id = data["id"]
        print(f"✓ Created level 2 subcategory: {data['name']}")

    def test_create_subcategory_level3(self, api_client):
        """Test creating a subcategory (level 3 - max depth)"""
        if not hasattr(self.__class__, 'level2_category_id'):
            pytest.skip("No level 2 category to add subcategory to")

        category_data = {
            "name": "TEST_Subcategory_L3",
            "parent_id": self.__class__.level2_category_id,
            "description": "Level 3 subcategory (max depth)"
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=category_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["level"] == 3  # Max level

        self.__class__.level3_category_id = data["id"]
        print(f"✓ Created level 3 subcategory: {data['name']} (max depth)")

    def test_reject_level5_category(self, api_client):
        """Test that creating a 5th level category is rejected"""
        if not hasattr(self.__class__, 'level3_category_id'):
            pytest.skip("No level 3 category to test depth limit")

        category_data = {
            "name": "TEST_Subcategory_L4_Should_Fail",
            "parent_id": self.__class__.level3_category_id
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=category_data
        )

        assert response.status_code == 400
        assert "4 niveles" in response.json().get("detail", "").lower() or "maximum" in response.json().get("detail", "").lower()
        print("✓ Correctly rejected 5th level category (max 4 levels)")

    def test_get_single_category(self, api_client):
        """Test getting a specific category by ID"""
        if not hasattr(self.__class__, 'root_category_id'):
            pytest.skip("No category to get")

        category_id = self.__class__.root_category_id
        response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{category_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == category_id
        assert data["name"] == "TEST_Root_Category"
        assert "product_count" in data
        print(f"✓ Retrieved category by ID: {data['name']}")

    def test_update_category(self, api_client):
        """Test updating a category"""
        if not hasattr(self.__class__, 'root_category_id'):
            pytest.skip("No category to update")

        category_id = self.__class__.root_category_id
        update_data = {
            "name": "TEST_Root_Category_Updated",
            "description": "Updated description"
        }

        response = api_client.put(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{category_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == update_data["name"]

        # Verify persistence
        get_response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{category_id}"
        )
        assert get_response.json()["name"] == update_data["name"]
        print(f"✓ Updated category: {data['name']}")


class TestCatalogCategoriesReorder(TestCatalogCategoriesAuth):
    """Test category reordering functionality"""

    def test_reorder_categories(self, api_client):
        """Test bulk reordering of categories"""
        # First, create two categories at root level for reordering
        cat1_data = {"name": "TEST_Reorder_Cat1", "position": 0}
        cat2_data = {"name": "TEST_Reorder_Cat2", "position": 1}

        cat1_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=cat1_data
        )
        cat2_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=cat2_data
        )

        if cat1_res.status_code != 200 or cat2_res.status_code != 200:
            pytest.skip("Could not create categories for reorder test")

        cat1_id = cat1_res.json()["id"]
        cat2_id = cat2_res.json()["id"]

        # Swap positions
        reorder_data = {
            "updates": [
                {"category_id": cat1_id, "new_position": 1},
                {"category_id": cat2_id, "new_position": 0}
            ]
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/reorder",
            json=reorder_data
        )

        assert response.status_code == 200
        print("✓ Categories reordered successfully")

        # Cleanup
        api_client.delete(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{cat1_id}")
        api_client.delete(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{cat2_id}")


class TestProductCategoryAssignment(TestCatalogCategoriesAuth):
    """Test assigning categories to products in catalog"""

    @pytest.fixture(scope="class")
    def test_product(self, auth_headers):
        """Get a product from the catalog for category assignment tests"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })

        # Get products from catalog
        response = session.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products")
        if response.status_code != 200:
            return None

        products = response.json()
        return products[0] if products else None

    def test_assign_category_to_product(self, api_client, test_product):
        """Test assigning a category to a product"""
        if not test_product:
            pytest.skip("No products in catalog for category assignment")

        # Get existing categories
        cats_response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true"
        )
        categories = cats_response.json() if cats_response.status_code == 200 else []

        if not categories:
            pytest.skip("No categories available for assignment")

        item_id = test_product["id"]
        category_id = categories[0]["id"]

        update_data = {
            "category_ids": [category_id]
        }

        response = api_client.put(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/{item_id}/categories",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert category_id in data.get("category_ids", [])
        print("✓ Assigned category to product")

    def test_assign_multiple_categories(self, api_client, test_product):
        """Test assigning multiple categories to a product"""
        if not test_product:
            pytest.skip("No products in catalog")

        # Get categories
        cats_response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true"
        )
        categories = cats_response.json() if cats_response.status_code == 200 else []

        if len(categories) < 2:
            pytest.skip("Need at least 2 categories for multiple assignment")

        item_id = test_product["id"]
        category_ids = [categories[0]["id"], categories[1]["id"]]

        update_data = {
            "category_ids": category_ids
        }

        response = api_client.put(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/{item_id}/categories",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data.get("category_ids", [])) == 2
        print("✓ Assigned multiple categories to product")

    def test_filter_products_by_category(self, api_client):
        """Test filtering catalog products by category"""
        # Get categories first
        cats_response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true"
        )
        categories = cats_response.json() if cats_response.status_code == 200 else []

        if not categories:
            pytest.skip("No categories to filter by")

        category_id = categories[0]["id"]

        response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products?category_id={category_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # All returned products should have this category
        for product in data:
            assert category_id in product.get("category_ids", [])

        print(f"✓ Filtered products by category: {len(data)} products")

    def test_get_category_products(self, api_client):
        """Test getting all products in a specific category"""
        # Get categories
        cats_response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true"
        )
        categories = cats_response.json() if cats_response.status_code == 200 else []

        if not categories:
            pytest.skip("No categories to get products from")

        category_id = categories[0]["id"]

        response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{category_id}/products"
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        print(f"✓ Got products in category: {len(data)} products")


class TestCatalogCategoriesCleanup(TestCatalogCategoriesAuth):
    """Cleanup test categories"""

    def test_delete_category_with_children(self, api_client):
        """Test deleting a category that has children - should delete all descendants"""
        # Create parent and child categories
        parent_data = {"name": "TEST_Parent_Delete"}
        parent_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=parent_data
        )

        if parent_res.status_code != 200:
            pytest.skip("Could not create parent category")

        parent_id = parent_res.json()["id"]

        # Create child
        child_data = {"name": "TEST_Child_Delete", "parent_id": parent_id}
        child_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=child_data
        )

        # Delete parent - should also delete child
        response = api_client.delete(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{parent_id}"
        )

        assert response.status_code == 200
        assert "2" in response.json().get("message", "") or "Eliminad" in response.json().get("message", "")
        print("✓ Deleted category with children (cascade delete)")

    def test_cleanup_test_categories(self, api_client):
        """Clean up TEST_ prefixed categories"""
        # Get all categories
        response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true"
        )

        if response.status_code != 200:
            print("Could not list categories for cleanup")
            return

        categories = response.json()
        deleted = 0

        # Delete test categories (those starting with TEST_)
        for cat in categories:
            if cat["name"].startswith("TEST_"):
                del_response = api_client.delete(
                    f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{cat['id']}"
                )
                if del_response.status_code == 200:
                    deleted += 1

        print(f"✓ Cleaned up {deleted} test categories")


class TestCatalogCategoriesEdgeCases(TestCatalogCategoriesAuth):
    """Test edge cases and validation"""

    def test_create_category_without_name(self, api_client):
        """Test creating category without name fails validation"""
        category_data = {
            "description": "No name category"
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=category_data
        )

        assert response.status_code == 422  # Validation error
        print("✓ Correctly rejected category without name")

    def test_get_nonexistent_category(self, api_client):
        """Test getting a category that doesn't exist"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{fake_id}"
        )

        assert response.status_code == 404
        print("✓ Returns 404 for non-existent category")

    def test_create_category_nonexistent_parent(self, api_client):
        """Test creating category with non-existent parent fails"""
        fake_parent_id = "00000000-0000-0000-0000-000000000000"
        category_data = {
            "name": "TEST_Bad_Parent",
            "parent_id": fake_parent_id
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=category_data
        )

        assert response.status_code == 404
        print("✓ Correctly rejected category with invalid parent")

    def test_category_cannot_be_own_parent(self, api_client):
        """Test that a category cannot be set as its own parent"""
        # Create a category first
        category_data = {"name": "TEST_Self_Parent"}
        create_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories",
            json=category_data
        )

        if create_res.status_code != 200:
            pytest.skip("Could not create category for self-parent test")

        cat_id = create_res.json()["id"]

        # Try to set itself as parent
        update_data = {"parent_id": cat_id}
        response = api_client.put(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{cat_id}",
            json=update_data
        )

        assert response.status_code == 400
        print("✓ Correctly rejected self-referencing parent")

        # Cleanup
        api_client.delete(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories/{cat_id}")

    def test_assign_invalid_category_to_product(self, api_client):
        """Test assigning invalid category to product fails"""
        # Get a product
        products_res = api_client.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products")
        products = products_res.json() if products_res.status_code == 200 else []

        if not products:
            pytest.skip("No products to test with")

        item_id = products[0]["id"]
        fake_category_id = "00000000-0000-0000-0000-000000000000"

        update_data = {"category_ids": [fake_category_id]}

        response = api_client.put(
            f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/products/{item_id}/categories",
            json=update_data
        )

        assert response.status_code == 400
        print("✓ Correctly rejected invalid category assignment")


class TestExistingCategories(TestCatalogCategoriesAuth):
    """Test existing categories mentioned by main agent"""

    def test_verify_existing_hierarchy(self, api_client):
        """Verify existing category hierarchy: Electrónica > Smartphones > iPhone > iPhone 15"""
        response = api_client.get(f"{BASE_URL}/api/catalogs/{TEST_CATALOG_ID}/categories?flat=true")

        assert response.status_code == 200
        categories = response.json()

        # Check for the expected hierarchy
        cat_names = [c["name"] for c in categories]
        expected_names = ["Electrónica", "Smartphones", "iPhone", "iPhone 15"]

        found = []
        for name in expected_names:
            if name in cat_names:
                found.append(name)

        print(f"✓ Found existing categories: {found}")

        # Verify levels if categories exist
        for cat in categories:
            if cat["name"] == "Electrónica":
                assert cat["level"] == 0, "Electrónica should be level 0"
            elif cat["name"] == "Smartphones":
                assert cat["level"] == 1, "Smartphones should be level 1"
            elif cat["name"] == "iPhone":
                assert cat["level"] == 2, "iPhone should be level 2"
            elif cat["name"] == "iPhone 15":
                assert cat["level"] == 3, "iPhone 15 should be level 3"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
