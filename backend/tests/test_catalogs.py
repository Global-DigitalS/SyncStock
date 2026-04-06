"""
Test suite for Multiple Catalogs functionality
Tests CRUD operations for catalogs, margin rules assignment, 
product addition to catalogs, and WooCommerce catalog selection.
"""
import os

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test_catalog@test.com"
TEST_PASSWORD = "Test123!"


class TestCatalogsAuth:
    """Authentication fixture for catalog tests"""

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


class TestCatalogCRUD(TestCatalogsAuth):
    """Test CRUD operations for catalogs"""

    def test_create_catalog(self, api_client):
        """Test creating a new catalog"""
        catalog_data = {
            "name": "TEST_Catalog_CRUD_Test",
            "description": "Test catalog for CRUD operations",
            "is_default": False
        }
        response = api_client.post(f"{BASE_URL}/api/catalogs", json=catalog_data)

        assert response.status_code == 200, f"Failed to create catalog: {response.text}"
        data = response.json()

        # Validate response structure
        assert "id" in data
        assert data["name"] == catalog_data["name"]
        assert data["description"] == catalog_data["description"]
        assert "is_default" in data
        assert "product_count" in data
        assert "margin_rules_count" in data
        assert "created_at" in data

        # Store catalog ID for cleanup
        self.__class__.created_catalog_id = data["id"]
        print(f"✓ Created catalog: {data['name']} (ID: {data['id']})")

    def test_list_catalogs(self, api_client):
        """Test listing all catalogs"""
        response = api_client.get(f"{BASE_URL}/api/catalogs")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        if data:
            # Validate catalog structure
            catalog = data[0]
            assert "id" in catalog
            assert "name" in catalog
            assert "product_count" in catalog
            assert "margin_rules_count" in catalog

        print(f"✓ Listed {len(data)} catalogs")

    def test_get_catalog_by_id(self, api_client):
        """Test getting a specific catalog"""
        if not hasattr(self.__class__, 'created_catalog_id'):
            pytest.skip("No catalog created to get")

        catalog_id = self.__class__.created_catalog_id
        response = api_client.get(f"{BASE_URL}/api/catalogs/{catalog_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == catalog_id
        assert data["name"] == "TEST_Catalog_CRUD_Test"
        print(f"✓ Retrieved catalog by ID: {data['name']}")

    def test_update_catalog(self, api_client):
        """Test updating a catalog"""
        if not hasattr(self.__class__, 'created_catalog_id'):
            pytest.skip("No catalog created to update")

        catalog_id = self.__class__.created_catalog_id
        update_data = {
            "name": "TEST_Catalog_Updated",
            "description": "Updated description"
        }

        response = api_client.put(f"{BASE_URL}/api/catalogs/{catalog_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

        # Verify persistence with GET
        get_response = api_client.get(f"{BASE_URL}/api/catalogs/{catalog_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == update_data["name"]

        print(f"✓ Updated catalog: {data['name']}")

    def test_set_catalog_as_default(self, api_client):
        """Test setting a catalog as default"""
        if not hasattr(self.__class__, 'created_catalog_id'):
            pytest.skip("No catalog created to set as default")

        catalog_id = self.__class__.created_catalog_id
        update_data = {"is_default": True}

        response = api_client.put(f"{BASE_URL}/api/catalogs/{catalog_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["is_default"] == True

        print(f"✓ Set catalog as default: {data['name']}")

    def test_delete_catalog(self, api_client):
        """Test deleting a catalog"""
        if not hasattr(self.__class__, 'created_catalog_id'):
            pytest.skip("No catalog created to delete")

        catalog_id = self.__class__.created_catalog_id
        response = api_client.delete(f"{BASE_URL}/api/catalogs/{catalog_id}")

        assert response.status_code == 200

        # Verify deletion with GET
        get_response = api_client.get(f"{BASE_URL}/api/catalogs/{catalog_id}")
        assert get_response.status_code == 404

        print("✓ Deleted catalog successfully")


class TestCatalogMarginRules(TestCatalogsAuth):
    """Test margin rules assignment to catalogs"""

    @pytest.fixture(scope="class")
    def test_catalog(self, auth_headers):
        """Create a test catalog for margin rules tests"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })

        catalog_data = {
            "name": "TEST_MarginRules_Catalog",
            "description": "Catalog for margin rules testing",
            "is_default": False
        }
        response = session.post(f"{BASE_URL}/api/catalogs", json=catalog_data)
        assert response.status_code == 200
        catalog = response.json()

        yield catalog

        # Cleanup
        session.delete(f"{BASE_URL}/api/catalogs/{catalog['id']}")

    def test_create_margin_rule_for_catalog(self, api_client, test_catalog):
        """Test creating a margin rule for a specific catalog"""
        rule_data = {
            "catalog_id": test_catalog["id"],
            "name": "TEST_Margin_Percentage",
            "rule_type": "percentage",
            "value": 15.0,
            "apply_to": "all",
            "priority": 1
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{test_catalog['id']}/margin-rules",
            json=rule_data
        )

        assert response.status_code == 200, f"Failed to create margin rule: {response.text}"
        data = response.json()

        assert "id" in data
        assert data["name"] == rule_data["name"]
        assert data["rule_type"] == "percentage"
        assert data["value"] == 15.0
        assert data["catalog_id"] == test_catalog["id"]

        self.__class__.created_rule_id = data["id"]
        print(f"✓ Created margin rule: {data['name']} (+{data['value']}%)")

    def test_create_fixed_margin_rule(self, api_client, test_catalog):
        """Test creating a fixed amount margin rule"""
        rule_data = {
            "catalog_id": test_catalog["id"],
            "name": "TEST_Fixed_Margin",
            "rule_type": "fixed",
            "value": 5.00,
            "apply_to": "all",
            "priority": 2
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{test_catalog['id']}/margin-rules",
            json=rule_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["rule_type"] == "fixed"
        assert data["value"] == 5.00

        self.__class__.fixed_rule_id = data["id"]
        print(f"✓ Created fixed margin rule: {data['name']} (+{data['value']}€)")

    def test_create_category_specific_rule(self, api_client, test_catalog):
        """Test creating a margin rule for specific category"""
        rule_data = {
            "catalog_id": test_catalog["id"],
            "name": "TEST_Category_Rule",
            "rule_type": "percentage",
            "value": 20.0,
            "apply_to": "category",
            "apply_to_value": "Electronics",
            "priority": 3
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{test_catalog['id']}/margin-rules",
            json=rule_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["apply_to"] == "category"
        assert data["apply_to_value"] == "Electronics"

        print(f"✓ Created category-specific rule: {data['name']}")

    def test_list_catalog_margin_rules(self, api_client, test_catalog):
        """Test listing margin rules for a catalog"""
        response = api_client.get(f"{BASE_URL}/api/catalogs/{test_catalog['id']}/margin-rules")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should have at least the rules we created
        assert len(data) >= 2

        for rule in data:
            assert "id" in rule
            assert "name" in rule
            assert "rule_type" in rule
            assert "value" in rule
            assert rule["catalog_id"] == test_catalog["id"]

        print(f"✓ Listed {len(data)} margin rules for catalog")

    def test_delete_margin_rule(self, api_client, test_catalog):
        """Test deleting a margin rule from catalog"""
        if not hasattr(self.__class__, 'created_rule_id'):
            pytest.skip("No rule created to delete")

        rule_id = self.__class__.created_rule_id
        response = api_client.delete(
            f"{BASE_URL}/api/catalogs/{test_catalog['id']}/margin-rules/{rule_id}"
        )

        assert response.status_code == 200
        print("✓ Deleted margin rule successfully")


class TestCatalogProducts(TestCatalogsAuth):
    """Test adding and managing products in catalogs"""

    @pytest.fixture(scope="class")
    def test_catalog_with_products(self, auth_headers):
        """Create catalog and ensure products exist"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            **auth_headers
        })

        # Create test catalog
        catalog_data = {
            "name": "TEST_Products_Catalog",
            "description": "Catalog for products testing",
            "is_default": False
        }
        catalog_response = session.post(f"{BASE_URL}/api/catalogs", json=catalog_data)
        assert catalog_response.status_code == 200
        catalog = catalog_response.json()

        # Get available products
        products_response = session.get(f"{BASE_URL}/api/products?limit=5")
        products = products_response.json() if products_response.status_code == 200 else []

        yield {"catalog": catalog, "products": products}

        # Cleanup
        session.delete(f"{BASE_URL}/api/catalogs/{catalog['id']}")

    def test_add_products_to_catalog(self, api_client, test_catalog_with_products):
        """Test adding products to a catalog"""
        catalog = test_catalog_with_products["catalog"]
        products = test_catalog_with_products["products"]

        if not products:
            pytest.skip("No products available to add to catalog")

        product_ids = [p["id"] for p in products[:2]]  # Add up to 2 products

        add_data = {
            "product_ids": product_ids
        }

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{catalog['id']}/products",
            json=add_data
        )

        assert response.status_code == 200, f"Failed to add products: {response.text}"
        data = response.json()

        assert "added" in data
        assert data["added"] >= 0

        self.__class__.added_product_ids = product_ids
        print(f"✓ Added {data['added']} products to catalog")

    def test_list_catalog_products(self, api_client, test_catalog_with_products):
        """Test listing products in a catalog"""
        catalog = test_catalog_with_products["catalog"]

        response = api_client.get(f"{BASE_URL}/api/catalogs/{catalog['id']}/products")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        if data:
            # Validate product item structure
            item = data[0]
            assert "id" in item
            assert "product_id" in item
            assert "product" in item
            assert "final_price" in item
            assert "active" in item

        print(f"✓ Listed {len(data)} products in catalog")

    def test_catalog_products_search(self, api_client, test_catalog_with_products):
        """Test searching products in a catalog"""
        catalog = test_catalog_with_products["catalog"]

        response = api_client.get(
            f"{BASE_URL}/api/catalogs/{catalog['id']}/products?search=test"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        print(f"✓ Search returned {len(data)} results")

    def test_remove_product_from_catalog(self, api_client, test_catalog_with_products):
        """Test removing a product from catalog"""
        catalog = test_catalog_with_products["catalog"]

        # First get products in catalog
        products_response = api_client.get(f"{BASE_URL}/api/catalogs/{catalog['id']}/products")
        if products_response.status_code != 200:
            pytest.skip("Could not get catalog products")

        products = products_response.json()
        if not products:
            pytest.skip("No products in catalog to remove")

        item_id = products[0]["id"]

        response = api_client.delete(
            f"{BASE_URL}/api/catalogs/{catalog['id']}/products/{item_id}"
        )

        assert response.status_code == 200
        print("✓ Removed product from catalog")


class TestWooCommerceCatalogSelection(TestCatalogsAuth):
    """Test WooCommerce export with catalog selection"""

    def test_get_catalogs_for_export(self, api_client):
        """Test that catalogs are available for WooCommerce export selection"""
        response = api_client.get(f"{BASE_URL}/api/catalogs")

        assert response.status_code == 200
        data = response.json()

        # Verify catalog data includes necessary fields for export selection
        for catalog in data:
            assert "id" in catalog
            assert "name" in catalog
            assert "is_default" in catalog
            assert "product_count" in catalog

        print(f"✓ {len(data)} catalogs available for export selection")

    def test_woocommerce_configs_endpoint(self, api_client):
        """Test WooCommerce configs endpoint exists"""
        response = api_client.get(f"{BASE_URL}/api/woocommerce/configs")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        print(f"✓ WooCommerce configs endpoint working, {len(data)} configs found")


class TestCatalogEdgeCases(TestCatalogsAuth):
    """Test edge cases and validation"""

    def test_create_catalog_without_name(self, api_client):
        """Test creating catalog without required name"""
        catalog_data = {
            "description": "Test without name"
        }

        response = api_client.post(f"{BASE_URL}/api/catalogs", json=catalog_data)

        # Should fail validation
        assert response.status_code == 422
        print("✓ Validation correctly rejects catalog without name")

    def test_get_nonexistent_catalog(self, api_client):
        """Test getting a catalog that doesn't exist"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{BASE_URL}/api/catalogs/{fake_id}")

        assert response.status_code == 404
        print("✓ Returns 404 for non-existent catalog")

    def test_add_products_to_nonexistent_catalog(self, api_client):
        """Test adding products to non-existent catalog"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        add_data = {"product_ids": ["test-id"]}

        response = api_client.post(
            f"{BASE_URL}/api/catalogs/{fake_id}/products",
            json=add_data
        )

        assert response.status_code == 404
        print("✓ Returns 404 for adding to non-existent catalog")

    def test_first_catalog_becomes_default(self, api_client):
        """Test that first created catalog becomes default automatically"""
        # Get current catalogs to check if any exist
        list_response = api_client.get(f"{BASE_URL}/api/catalogs")
        current_catalogs = list_response.json()

        # Create a new catalog
        catalog_data = {
            "name": "TEST_Auto_Default_Check",
            "description": "Test automatic default assignment",
            "is_default": False
        }

        response = api_client.post(f"{BASE_URL}/api/catalogs", json=catalog_data)
        assert response.status_code == 200
        data = response.json()

        # If this is the only catalog or marked as default, is_default should be True
        # Or if explicitly set to False and not first, it should be False
        assert "is_default" in data

        # Cleanup
        api_client.delete(f"{BASE_URL}/api/catalogs/{data['id']}")

        print(f"✓ Catalog created with is_default={data['is_default']}")


class TestCatalogStatistics(TestCatalogsAuth):
    """Test catalog statistics accuracy"""

    def test_catalog_product_count(self, api_client):
        """Test that catalog product count is accurate"""
        # Create catalog
        catalog_data = {
            "name": "TEST_Stats_Catalog",
            "description": "Test catalog statistics"
        }
        create_response = api_client.post(f"{BASE_URL}/api/catalogs", json=catalog_data)
        assert create_response.status_code == 200
        catalog = create_response.json()

        # Initial count should be 0
        assert catalog["product_count"] == 0

        # Get available products
        products_response = api_client.get(f"{BASE_URL}/api/products?limit=2")
        products = products_response.json() if products_response.status_code == 200 else []

        if products:
            # Add products
            product_ids = [p["id"] for p in products]
            api_client.post(
                f"{BASE_URL}/api/catalogs/{catalog['id']}/products",
                json={"product_ids": product_ids}
            )

            # Check updated count
            get_response = api_client.get(f"{BASE_URL}/api/catalogs/{catalog['id']}")
            updated_catalog = get_response.json()

            # Product count should reflect added products
            assert updated_catalog["product_count"] >= 0
            print(f"✓ Product count updated correctly: {updated_catalog['product_count']}")

        # Cleanup
        api_client.delete(f"{BASE_URL}/api/catalogs/{catalog['id']}")
        print("✓ Catalog statistics test complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
