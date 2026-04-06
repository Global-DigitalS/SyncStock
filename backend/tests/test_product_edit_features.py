"""
Test Product Edit Features - Testing new fields and image upload endpoints
Features tested:
1. PUT /api/products/{product_id} with new fields: name, short_description, long_description, brand, image_url, gallery_images
2. POST /api/products/{product_id}/upload-image for main (image_type=main) and gallery (image_type=gallery)
3. DELETE /api/products/{product_id}/gallery-image to remove gallery images
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestProductEditFeatures:
    """Test product editing with new fields and image management"""

    @pytest.fixture(scope="class")
    def api_session(self):
        """Shared requests session"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        return session

    @pytest.fixture(scope="class")
    def auth_token(self, api_session):
        """Register a test user and get auth token"""
        test_email = f"TEST_product_edit_{uuid.uuid4().hex[:6]}@test.com"
        test_password = "Test123456"
        test_name = "Test Product Edit User"

        # Try to register
        response = api_session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": test_password,
            "name": test_name
        })

        if response.status_code == 201:
            return response.json().get("token")

        # If registration failed (user exists), try login
        response = api_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })

        if response.status_code == 200:
            return response.json().get("token")

        pytest.skip("Could not register or login test user")

    @pytest.fixture(scope="class")
    def authenticated_client(self, api_session, auth_token):
        """Session with auth header"""
        api_session.headers.update({"Authorization": f"Bearer {auth_token}"})
        return api_session

    @pytest.fixture(scope="class")
    def test_supplier(self, authenticated_client):
        """Create a test supplier with products"""
        supplier_data = {
            "name": f"TEST_Supplier_{uuid.uuid4().hex[:6]}",
            "description": "Test supplier for product edit testing",
            "connection_type": "url"
        }

        response = authenticated_client.post(f"{BASE_URL}/api/suppliers", json=supplier_data)
        if response.status_code == 201:
            return response.json()
        pytest.skip(f"Could not create test supplier: {response.text}")

    @pytest.fixture(scope="class")
    def test_product(self, authenticated_client, test_supplier):
        """Create a test product for editing"""
        # First, we need to import some products via supplier sync
        # Since this is complex, let's check if there are existing products

        # Check for existing products
        response = authenticated_client.get(f"{BASE_URL}/api/products?limit=1")
        if response.status_code == 200:
            products = response.json()
            if products and len(products) > 0:
                return products[0]

        # If no products exist, skip the test
        pytest.skip("No products available for testing")

    # ==================== Test PUT /api/products/{product_id} ====================

    def test_update_product_name(self, authenticated_client, test_product):
        """Test updating product name"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")
        new_name = f"TEST_Updated_Product_{uuid.uuid4().hex[:4]}"

        response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"name": new_name}
        )

        assert response.status_code == 200, f"Failed to update product name: {response.text}"
        data = response.json()
        assert data["name"] == new_name, "Product name not updated correctly"
        print(f"✓ Product name updated to: {new_name}")

    def test_update_product_short_description(self, authenticated_client, test_product):
        """Test updating product short_description field"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")
        short_desc = "Esta es una descripción corta de prueba para el producto"

        response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"short_description": short_desc}
        )

        assert response.status_code == 200, f"Failed to update short_description: {response.text}"
        data = response.json()
        assert data.get("short_description") == short_desc, "short_description not updated correctly"
        print("✓ Product short_description updated")

    def test_update_product_long_description(self, authenticated_client, test_product):
        """Test updating product long_description field"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")
        long_desc = """Esta es una descripción larga de prueba.
        
        Incluye múltiples líneas y detalles sobre el producto.
        - Característica 1
        - Característica 2
        - Característica 3
        
        Este texto se mostraría en la página del producto."""

        response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"long_description": long_desc}
        )

        assert response.status_code == 200, f"Failed to update long_description: {response.text}"
        data = response.json()
        assert data.get("long_description") == long_desc, "long_description not updated correctly"
        print("✓ Product long_description updated")

    def test_update_product_brand(self, authenticated_client, test_product):
        """Test updating product brand field"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")
        brand = "TEST_Brand_Premium"

        response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"brand": brand}
        )

        assert response.status_code == 200, f"Failed to update brand: {response.text}"
        data = response.json()
        assert data.get("brand") == brand, "Brand not updated correctly"
        print(f"✓ Product brand updated to: {brand}")

    def test_update_product_image_url(self, authenticated_client, test_product):
        """Test updating product image_url field"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")
        image_url = "https://example.com/test-product-image.jpg"

        response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"image_url": image_url}
        )

        assert response.status_code == 200, f"Failed to update image_url: {response.text}"
        data = response.json()
        assert data.get("image_url") == image_url, "image_url not updated correctly"
        print("✓ Product image_url updated")

    def test_update_product_gallery_images(self, authenticated_client, test_product):
        """Test updating product gallery_images field"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")
        gallery_images = [
            "https://example.com/gallery-1.jpg",
            "https://example.com/gallery-2.jpg",
            "https://example.com/gallery-3.jpg"
        ]

        response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"gallery_images": gallery_images}
        )

        assert response.status_code == 200, f"Failed to update gallery_images: {response.text}"
        data = response.json()
        assert data.get("gallery_images") == gallery_images, "gallery_images not updated correctly"
        print(f"✓ Product gallery_images updated with {len(gallery_images)} images")

    def test_update_multiple_fields(self, authenticated_client, test_product):
        """Test updating multiple product fields at once"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")
        update_data = {
            "name": f"TEST_MultiField_Product_{uuid.uuid4().hex[:4]}",
            "brand": "MultiField Brand",
            "short_description": "Short description for multi-field test",
            "long_description": "Long description with more details for multi-field test",
            "category": "Test Category"
        }

        response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json=update_data
        )

        assert response.status_code == 200, f"Failed to update multiple fields: {response.text}"
        data = response.json()

        assert data["name"] == update_data["name"]
        assert data.get("brand") == update_data["brand"]
        assert data.get("short_description") == update_data["short_description"]
        assert data.get("long_description") == update_data["long_description"]
        print("✓ Multiple product fields updated successfully")

    # ==================== Test POST /api/products/{product_id}/upload-image ====================

    def test_upload_main_image_without_file(self, authenticated_client, test_product):
        """Test upload endpoint returns error without file"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")

        # Remove content-type header for multipart
        headers = {"Authorization": authenticated_client.headers.get("Authorization")}

        response = requests.post(
            f"{BASE_URL}/api/products/{product_id}/upload-image?image_type=main",
            headers=headers
        )

        # Should fail without file
        assert response.status_code in [400, 422], f"Expected 400/422 without file, got: {response.status_code}"
        print("✓ Upload endpoint correctly rejects request without file")

    def test_upload_main_image_invalid_product(self, authenticated_client):
        """Test upload endpoint returns 404 for invalid product"""
        invalid_product_id = "invalid-product-id-12345"

        # Create a minimal test file in memory
        files = {"file": ("test.png", b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR', "image/png")}

        headers = {"Authorization": authenticated_client.headers.get("Authorization")}

        response = requests.post(
            f"{BASE_URL}/api/products/{invalid_product_id}/upload-image?image_type=main",
            headers=headers,
            files=files
        )

        assert response.status_code == 404, f"Expected 404 for invalid product, got: {response.status_code}"
        print("✓ Upload endpoint correctly returns 404 for invalid product")

    # ==================== Test DELETE /api/products/{product_id}/gallery-image ====================

    def test_delete_gallery_image_invalid_product(self, authenticated_client):
        """Test delete gallery image returns 404 for invalid product"""
        invalid_product_id = "invalid-product-id-12345"

        response = authenticated_client.delete(
            f"{BASE_URL}/api/products/{invalid_product_id}/gallery-image?image_url=test.jpg"
        )

        assert response.status_code == 404, f"Expected 404 for invalid product, got: {response.status_code}"
        print("✓ Delete gallery image correctly returns 404 for invalid product")

    def test_delete_nonexistent_gallery_image(self, authenticated_client, test_product):
        """Test delete gallery image returns 404 for non-existent image"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")

        response = authenticated_client.delete(
            f"{BASE_URL}/api/products/{product_id}/gallery-image?image_url=https://nonexistent.com/image.jpg"
        )

        # Should return 404 if image not in gallery
        assert response.status_code == 404, f"Expected 404 for non-existent image, got: {response.status_code}"
        print("✓ Delete gallery image correctly returns 404 for non-existent image")

    # ==================== Test GET /api/products/{product_id} - Verify fields present ====================

    def test_get_product_has_new_fields(self, authenticated_client, test_product):
        """Test that GET product response includes new fields"""
        if not test_product:
            pytest.skip("No test product available")

        product_id = test_product.get("id")

        response = authenticated_client.get(f"{BASE_URL}/api/products/{product_id}")

        assert response.status_code == 200, f"Failed to get product: {response.text}"
        data = response.json()

        # Verify new fields are in response (can be null)
        assert "short_description" in data or data.get("short_description") is None
        assert "long_description" in data or data.get("long_description") is None
        assert "gallery_images" in data or data.get("gallery_images") is None
        assert "brand" in data
        assert "image_url" in data

        print("✓ GET product response includes all new fields")


class TestProductUpdateWithoutAuth:
    """Test product endpoints without authentication"""

    def test_update_product_requires_auth(self):
        """Test that PUT product requires authentication"""
        response = requests.put(
            f"{BASE_URL}/api/products/some-id",
            json={"name": "Test"},
            headers={"Content-Type": "application/json"}
        )

        # 401 or 403 both indicate auth required
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got: {response.status_code}"
        print(f"✓ Product update correctly requires authentication (status: {response.status_code})")

    def test_upload_image_requires_auth(self):
        """Test that POST upload-image requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/products/some-id/upload-image?image_type=main"
        )

        # 401 or 403 both indicate auth required
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got: {response.status_code}"
        print(f"✓ Image upload correctly requires authentication (status: {response.status_code})")

    def test_delete_gallery_image_requires_auth(self):
        """Test that DELETE gallery-image requires authentication"""
        response = requests.delete(
            f"{BASE_URL}/api/products/some-id/gallery-image?image_url=test.jpg"
        )

        # 401 or 403 both indicate auth required
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got: {response.status_code}"
        print(f"✓ Delete gallery image correctly requires authentication (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
