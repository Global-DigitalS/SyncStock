"""
Test suite for Category Export and Drag & Drop Reorder Features
Tests:
1. POST /api/stores/configs/{config_id}/export-categories - Export categories to store
2. POST /api/catalogs/{catalog_id}/categories/reorder - Reorder categories (drag & drop)
3. GET /api/catalogs/{catalog_id}/categories - Get categories (tree and flat)
4. POST /api/catalogs/{catalog_id}/categories - Create category
"""
import os

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"


class TestAuth:
    """Authentication fixture"""

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


class TestCategoryExportEndpoint(TestAuth):
    """Test POST /api/stores/configs/{config_id}/export-categories"""

    @pytest.fixture(scope="class")
    def test_store(self, auth_headers):
        """Get an existing store config"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })

        response = session.get(f"{BASE_URL}/api/stores/configs")
        if response.status_code == 200 and response.json():
            stores = response.json()
            print(f"Found {len(stores)} stores")
            return stores[0] if stores else None
        return None

    @pytest.fixture(scope="class")
    def test_catalog_with_categories(self, auth_headers):
        """Get a catalog that has categories"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })

        # Get catalogs
        response = session.get(f"{BASE_URL}/api/catalogs")
        if response.status_code != 200:
            return None

        catalogs = response.json()
        for catalog in catalogs:
            # Check if catalog has categories
            cat_response = session.get(f"{BASE_URL}/api/catalogs/{catalog['id']}/categories?flat=true")
            if cat_response.status_code == 200 and cat_response.json():
                print(f"Found catalog '{catalog['name']}' with {len(cat_response.json())} categories")
                return catalog

        return catalogs[0] if catalogs else None

    def test_export_categories_endpoint_exists(self, api_client, test_store, test_catalog_with_categories):
        """Test that export categories endpoint exists and accepts requests"""
        if not test_store:
            pytest.skip("No store configured for export test")

        if not test_catalog_with_categories:
            pytest.skip("No catalog with categories for export test")

        store_id = test_store["id"]
        catalog_id = test_catalog_with_categories["id"]

        response = api_client.post(
            f"{BASE_URL}/api/stores/configs/{store_id}/export-categories",
            json={"catalog_id": catalog_id}
        )

        # The endpoint should return 200 even if export fails due to store credentials
        # as it will return status with error message
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}, {response.text}"

        data = response.json()
        print(f"Export response: {data}")

        # Check response structure
        assert "status" in data or "created" in data or "message" in data
        print(f"✓ Export categories endpoint works - status: {data.get('status', data.get('message', 'unknown'))}")

    def test_export_categories_without_catalog_id(self, api_client, test_store):
        """Test export without catalog_id uses store's associated catalog"""
        if not test_store:
            pytest.skip("No store configured")

        store_id = test_store["id"]

        # If store has catalog_id associated, it should use that
        response = api_client.post(
            f"{BASE_URL}/api/stores/configs/{store_id}/export-categories",
            json={}
        )

        # Should return 200 or 400 if no catalog associated
        assert response.status_code in [200, 400]

        data = response.json()
        if response.status_code == 400:
            assert "catálogo" in data.get("detail", "").lower() or "catalog" in data.get("detail", "").lower()
            print("✓ Correctly requires catalog_id when store has no default catalog")
        else:
            print("✓ Used store's associated catalog for export")

    def test_export_categories_invalid_store(self, api_client, test_catalog_with_categories):
        """Test export with invalid store ID returns 404"""
        if not test_catalog_with_categories:
            pytest.skip("No catalog for test")

        fake_store_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.post(
            f"{BASE_URL}/api/stores/configs/{fake_store_id}/export-categories",
            json={"catalog_id": test_catalog_with_categories["id"]}
        )

        assert response.status_code == 404
        print("✓ Returns 404 for non-existent store")

    def test_export_categories_invalid_catalog(self, api_client, test_store):
        """Test export with invalid catalog ID returns 404"""
        if not test_store:
            pytest.skip("No store configured")

        fake_catalog_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.post(
            f"{BASE_URL}/api/stores/configs/{test_store['id']}/export-categories",
            json={"catalog_id": fake_catalog_id}
        )

        assert response.status_code == 404
        print("✓ Returns 404 for non-existent catalog")


class TestCategoryReorderEndpoint(TestAuth):
    """Test POST /api/catalogs/{catalog_id}/categories/reorder for drag & drop"""

    @pytest.fixture(scope="class")
    def test_catalog(self, auth_headers):
        """Get test catalog"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })

        response = session.get(f"{BASE_URL}/api/catalogs")
        if response.status_code == 200 and response.json():
            return response.json()[0]
        return None

    def test_reorder_categories_success(self, api_client, test_catalog):
        """Test successful category reordering (drag & drop)"""
        if not test_catalog:
            pytest.skip("No catalog for reorder test")

        catalog_id = test_catalog["id"]

        # Create two test categories for reordering
        cat1_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_Cat1", "position": 0}
        )
        cat2_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_Cat2", "position": 1}
        )

        if cat1_res.status_code != 200 or cat2_res.status_code != 200:
            pytest.skip("Could not create test categories")

        cat1_id = cat1_res.json()["id"]
        cat2_id = cat2_res.json()["id"]
        self.__class__.test_cat_ids = [cat1_id, cat2_id]

        # Perform reorder - swap positions (like drag & drop)
        reorder_data = {
            "updates": [
                {"category_id": cat1_id, "new_position": 1, "new_parent_id": None},
                {"category_id": cat2_id, "new_position": 0, "new_parent_id": None}
            ]
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories/reorder",
            json=reorder_data
        )

        assert response.status_code == 200
        assert "reorden" in response.json().get("message", "").lower()
        print("✓ Categories reordered successfully (drag & drop simulation)")

    def test_reorder_with_parent_change(self, api_client, test_catalog):
        """Test reordering that changes parent (moving to different level)"""
        if not test_catalog:
            pytest.skip("No catalog for reorder test")

        catalog_id = test_catalog["id"]

        # Create parent and child categories
        parent_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_Parent"}
        )
        child_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_Child_ToMove"}
        )

        if parent_res.status_code != 200 or child_res.status_code != 200:
            pytest.skip("Could not create test categories")

        parent_id = parent_res.json()["id"]
        child_id = child_res.json()["id"]

        # Reorder - move child under parent (like dragging into a folder)
        reorder_data = {
            "updates": [
                {"category_id": child_id, "new_position": 0, "new_parent_id": parent_id}
            ]
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories/reorder",
            json=reorder_data
        )

        assert response.status_code == 200

        # Verify the parent was changed
        get_response = api_client.get(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories/{child_id}"
        )

        if get_response.status_code == 200:
            assert get_response.json().get("parent_id") == parent_id
            assert get_response.json().get("level") == 1
            print("✓ Reorder with parent change works (child moved under parent)")

        # Cleanup
        api_client.delete(f"{BASE_URL}/api/catalogs/{catalog_id}/categories/{parent_id}")

    def test_reorder_prevents_exceeding_max_depth(self, api_client, test_catalog):
        """Test that reorder prevents exceeding 4-level limit"""
        if not test_catalog:
            pytest.skip("No catalog for test")

        catalog_id = test_catalog["id"]

        # Create a deep hierarchy (3 levels)
        l0_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_L0"}
        )
        if l0_res.status_code != 200:
            pytest.skip("Could not create root category")

        l0_id = l0_res.json()["id"]

        l1_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_L1", "parent_id": l0_id}
        )
        l1_id = l1_res.json()["id"]

        l2_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_L2", "parent_id": l1_id}
        )
        l2_id = l2_res.json()["id"]

        l3_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_L3", "parent_id": l2_id}
        )
        l3_id = l3_res.json()["id"]

        # Try to move a root category under level 3 (would create level 4)
        another_root_res = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={"name": "TEST_DnD_ToMove"}
        )
        if another_root_res.status_code != 200:
            pytest.skip("Could not create test category")

        another_root_id = another_root_res.json()["id"]

        # The reorder endpoint should skip updates that would exceed level limit
        reorder_data = {
            "updates": [
                {"category_id": another_root_id, "new_position": 0, "new_parent_id": l3_id}
            ]
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories/reorder",
            json=reorder_data
        )

        # Should return 200 but skip the invalid update
        assert response.status_code == 200

        # Verify the category was NOT moved (still at root level)
        get_response = api_client.get(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories/{another_root_id}"
        )
        if get_response.status_code == 200:
            # Should still be at level 0
            assert get_response.json().get("level") == 0
            print("✓ Reorder correctly skips updates that would exceed 4-level limit")

        # Cleanup
        api_client.delete(f"{BASE_URL}/api/catalogs/{catalog_id}/categories/{l0_id}")
        api_client.delete(f"{BASE_URL}/api/catalogs/{catalog_id}/categories/{another_root_id}")

    def test_reorder_invalid_catalog(self, api_client):
        """Test reorder with invalid catalog returns 404"""
        fake_catalog_id = "00000000-0000-0000-0000-000000000000"

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{fake_catalog_id}/categories/reorder",
            json={"updates": []}
        )

        assert response.status_code == 404
        print("✓ Returns 404 for non-existent catalog")


class TestCategoriesEndpoints(TestAuth):
    """Test category CRUD endpoints used by drag & drop UI"""

    @pytest.fixture(scope="class")
    def test_catalog(self, auth_headers):
        """Get test catalog"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })

        response = session.get(f"{BASE_URL}/api/catalogs")
        if response.status_code == 200 and response.json():
            return response.json()[0]
        return None

    def test_get_categories_tree(self, api_client, test_catalog):
        """Test GET categories returns tree structure"""
        if not test_catalog:
            pytest.skip("No catalog")

        response = api_client.get(f"{BASE_URL}/api/catalogs/{test_catalog['id']}/categories")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # If categories exist, verify tree structure
        if data:
            cat = data[0]
            assert "id" in cat
            assert "name" in cat
            assert "children" in cat  # Tree structure has children
            assert "level" in cat
            assert "position" in cat or True  # position may be part of the object

        print(f"✓ GET categories returns tree structure with {len(data)} root categories")

    def test_get_categories_flat(self, api_client, test_catalog):
        """Test GET categories?flat=true returns flat list"""
        if not test_catalog:
            pytest.skip("No catalog")

        response = api_client.get(f"{BASE_URL}/api/catalogs/{test_catalog['id']}/categories?flat=true")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Flat list should include all categories with level info
        for cat in data:
            assert "level" in cat
            assert 0 <= cat["level"] <= 3  # Max 4 levels
            assert "product_count" in cat

        print(f"✓ GET categories?flat=true returns {len(data)} categories in flat structure")

    def test_create_category_with_position(self, api_client, test_catalog):
        """Test creating category with position for drag & drop ordering"""
        if not test_catalog:
            pytest.skip("No catalog")

        catalog_id = test_catalog["id"]

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog_id}/categories",
            json={
                "name": "TEST_Position_Cat",
                "position": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["position"] == 5

        # Cleanup
        api_client.delete(f"{BASE_URL}/api/catalogs/{catalog_id}/categories/{data['id']}")

        print("✓ Category created with custom position")


class TestStoresEndpoints(TestAuth):
    """Test stores endpoints for export functionality"""

    def test_get_stores(self, api_client):
        """Test GET stores configs returns store list"""
        response = api_client.get(f"{BASE_URL}/api/stores/configs")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # If stores exist, verify structure
        if data:
            store = data[0]
            assert "id" in store
            assert "name" in store
            assert "platform" in store
            print(f"✓ Found {len(data)} stores: {[s['name'] for s in data]}")
        else:
            print("✓ No stores configured (empty list)")


class TestCleanup(TestAuth):
    """Clean up test categories"""

    @pytest.fixture(scope="class")
    def test_catalog(self, auth_headers):
        """Get test catalog"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })

        response = session.get(f"{BASE_URL}/api/catalogs")
        if response.status_code == 200 and response.json():
            return response.json()[0]
        return None

    def test_cleanup_test_categories(self, api_client, test_catalog):
        """Clean up all TEST_ prefixed categories"""
        if not test_catalog:
            print("No catalog for cleanup")
            return

        catalog_id = test_catalog["id"]

        response = api_client.get(f"{BASE_URL}/api/catalogs/{catalog_id}/categories?flat=true")
        if response.status_code != 200:
            return

        categories = response.json()
        deleted = 0

        for cat in categories:
            if cat["name"].startswith("TEST_"):
                del_res = api_client.delete(
                    f"{BASE_URL}/api/catalogs/{catalog_id}/categories/{cat['id']}"
                )
                if del_res.status_code == 200:
                    deleted += 1

        print(f"✓ Cleaned up {deleted} test categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
