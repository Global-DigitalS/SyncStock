"""
Test cases for Product Detail feature with tabs
- GET /api/products/{product_id} returns extended fields
- PUT /api/products/{product_id} updates product with extended fields
- GET /api/products-unified returns unified products by EAN
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test user"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "test@test.com",
        "password": "test123"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestProductsUnified:
    """Tests for unified products endpoint (EAN-based)"""
    
    def test_get_products_unified_returns_list(self, authenticated_client):
        """GET /api/products-unified returns list of unified products"""
        response = authenticated_client.get(f"{BASE_URL}/api/products-unified")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1, "Expected at least one unified product"
        print(f"Found {len(data)} unified products")
    
    def test_unified_product_structure(self, authenticated_client):
        """Unified product response has correct structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/products-unified")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        product = data[0]
        # Check required fields
        assert "ean" in product
        assert "name" in product
        assert "best_price" in product
        assert "best_supplier" in product
        assert "best_supplier_id" in product
        assert "total_stock" in product
        assert "supplier_count" in product
        assert "suppliers" in product
        
        # Check suppliers structure
        assert isinstance(product["suppliers"], list)
        if len(product["suppliers"]) > 0:
            supplier = product["suppliers"][0]
            assert "supplier_id" in supplier
            assert "supplier_name" in supplier
            assert "price" in supplier
            assert "stock" in supplier
            assert "sku" in supplier
            assert "is_best_offer" in supplier
            assert "product_id" in supplier
        print(f"Unified product '{product['name']}' has {len(product['suppliers'])} suppliers")
    
    def test_unified_products_have_best_offer(self, authenticated_client):
        """Each unified product should have exactly one best offer"""
        response = authenticated_client.get(f"{BASE_URL}/api/products-unified")
        assert response.status_code == 200
        data = response.json()
        
        for product in data:
            best_offers = [s for s in product["suppliers"] if s["is_best_offer"]]
            assert len(best_offers) == 1, f"Product {product['ean']} should have exactly one best offer"
        print("All unified products have exactly one best offer")


class TestProductDetail:
    """Tests for GET /api/products/{product_id} endpoint"""
    
    def test_get_product_returns_extended_fields(self, authenticated_client):
        """GET /api/products/{product_id} returns product with extended fields"""
        # First get a product_id from unified products
        response = authenticated_client.get(f"{BASE_URL}/api/products-unified")
        assert response.status_code == 200
        unified = response.json()
        assert len(unified) >= 1
        
        # Get the product_id from the best offer
        product_id = unified[0]["suppliers"][0]["product_id"]
        
        # Get product detail
        detail_response = authenticated_client.get(f"{BASE_URL}/api/products/{product_id}")
        assert detail_response.status_code == 200
        
        product = detail_response.json()
        
        # Check base fields
        assert "id" in product
        assert "name" in product
        assert "ean" in product
        assert "sku" in product
        assert "price" in product
        assert "stock" in product
        assert "brand" in product
        assert "category" in product
        
        # Check extended fields (from ProductResponse)
        extended_fields = [
            "referencia", "part_number", "asin", "upc", "gtin", "oem", "id_erp",
            "activado", "descatalogado", "condicion", "activar_pos", "tipo_pack",
            "vender_sin_stock", "nuevo", "fecha_disponibilidad",
            "stock_disponible", "stock_fantasma", "stock_market",
            "unid_caja", "cantidad_minima", "dias_entrega", "cantidad_maxima_carrito",
            "resto_stock", "requiere_envio", "envio_gratis", "gastos_envio",
            "largo", "ancho", "alto", "tipo_peso",
            "formas_pago", "formas_envio",
            "permite_actualizar_coste", "permite_actualizar_stock", "tipo_cheque_regalo"
        ]
        
        for field in extended_fields:
            assert field in product, f"Missing extended field: {field}"
        
        print(f"Product '{product['name']}' has all {len(extended_fields)} extended fields")
    
    def test_get_product_not_found(self, authenticated_client):
        """GET /api/products/{non_existent_id} returns 404"""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.get(f"{BASE_URL}/api/products/{fake_id}")
        assert response.status_code == 404
        print("Non-existent product returns 404 as expected")


class TestProductUpdate:
    """Tests for PUT /api/products/{product_id} endpoint"""
    
    def test_update_product_name(self, authenticated_client):
        """PUT /api/products/{product_id} updates product name"""
        # Get a product_id
        response = authenticated_client.get(f"{BASE_URL}/api/products-unified")
        unified = response.json()
        product_id = unified[0]["suppliers"][0]["product_id"]
        
        # Get original name
        original = authenticated_client.get(f"{BASE_URL}/api/products/{product_id}").json()
        original_name = original["name"]
        
        # Update name
        new_name = f"TEST_Updated_{uuid.uuid4().hex[:8]}"
        update_response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json={"name": new_name}
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == new_name
        
        # Verify persistence with GET
        verify_response = authenticated_client.get(f"{BASE_URL}/api/products/{product_id}")
        assert verify_response.status_code == 200
        assert verify_response.json()["name"] == new_name
        
        # Revert name
        authenticated_client.put(f"{BASE_URL}/api/products/{product_id}", json={"name": original_name})
        print(f"Product name update and persistence verified")
    
    def test_update_product_extended_fields(self, authenticated_client):
        """PUT /api/products/{product_id} updates extended fields"""
        # Get a product_id
        response = authenticated_client.get(f"{BASE_URL}/api/products-unified")
        unified = response.json()
        product_id = unified[0]["suppliers"][0]["product_id"]
        
        # Get original values
        original = authenticated_client.get(f"{BASE_URL}/api/products/{product_id}").json()
        
        # Update multiple extended fields
        test_ref = f"TEST_REF_{uuid.uuid4().hex[:8]}"
        update_data = {
            "referencia": test_ref,
            "part_number": "PN-12345",
            "activado": True,
            "descatalogado": False,
            "stock_disponible": 100,
            "dias_entrega": 3,
            "envio_gratis": True,
            "largo": 50.5,
            "ancho": 30.2,
            "alto": 10.0,
            "tipo_peso": "kilogram"
        }
        
        update_response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        
        # Verify updated fields
        assert updated["referencia"] == test_ref
        assert updated["part_number"] == "PN-12345"
        assert updated["activado"] == True
        assert updated["descatalogado"] == False
        assert updated["stock_disponible"] == 100
        assert updated["dias_entrega"] == 3
        assert updated["envio_gratis"] == True
        assert updated["largo"] == 50.5
        assert updated["ancho"] == 30.2
        assert updated["alto"] == 10.0
        
        # Verify persistence with GET
        verify = authenticated_client.get(f"{BASE_URL}/api/products/{product_id}").json()
        assert verify["referencia"] == test_ref
        assert verify["envio_gratis"] == True
        
        # Revert changes
        revert_data = {
            "referencia": original.get("referencia"),
            "part_number": original.get("part_number"),
            "stock_disponible": original.get("stock_disponible"),
            "dias_entrega": original.get("dias_entrega"),
            "envio_gratis": original.get("envio_gratis", False),
            "largo": original.get("largo", 0),
            "ancho": original.get("ancho", 0),
            "alto": original.get("alto", 0)
        }
        authenticated_client.put(f"{BASE_URL}/api/products/{product_id}", json=revert_data)
        print("Extended fields update and persistence verified")
    
    def test_update_product_toggle_fields(self, authenticated_client):
        """PUT /api/products/{product_id} handles boolean toggle fields"""
        # Get a product_id
        response = authenticated_client.get(f"{BASE_URL}/api/products-unified")
        unified = response.json()
        product_id = unified[0]["suppliers"][0]["product_id"]
        
        # Get original values
        original = authenticated_client.get(f"{BASE_URL}/api/products/{product_id}").json()
        
        # Test boolean toggles
        toggle_fields = {
            "activado": not original.get("activado", True),
            "descatalogado": not original.get("descatalogado", False),
            "activar_pos": not original.get("activar_pos", False),
            "tipo_pack": not original.get("tipo_pack", False),
            "vender_sin_stock": not original.get("vender_sin_stock", False),
            "resto_stock": not original.get("resto_stock", True),
            "requiere_envio": not original.get("requiere_envio", True),
            "envio_gratis": not original.get("envio_gratis", False),
            "permite_actualizar_coste": not original.get("permite_actualizar_coste", True),
            "permite_actualizar_stock": not original.get("permite_actualizar_stock", True),
            "tipo_cheque_regalo": not original.get("tipo_cheque_regalo", False)
        }
        
        update_response = authenticated_client.put(
            f"{BASE_URL}/api/products/{product_id}",
            json=toggle_fields
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        
        # Verify all toggles were updated
        for field, expected_value in toggle_fields.items():
            assert updated[field] == expected_value, f"{field} should be {expected_value}"
        
        # Revert to original values
        revert_data = {k: original.get(k) for k in toggle_fields.keys()}
        authenticated_client.put(f"{BASE_URL}/api/products/{product_id}", json=revert_data)
        print(f"All {len(toggle_fields)} boolean toggle fields update verified")
    
    def test_update_product_not_found(self, authenticated_client):
        """PUT /api/products/{non_existent_id} returns 404"""
        fake_id = str(uuid.uuid4())
        response = authenticated_client.put(
            f"{BASE_URL}/api/products/{fake_id}",
            json={"name": "Test"}
        )
        assert response.status_code == 404
        print("Update non-existent product returns 404 as expected")


class TestProductDetailPermissions:
    """Tests for product update permissions"""
    
    def test_update_product_unauthorized(self, api_client):
        """PUT /api/products/{product_id} without auth returns 401/403"""
        fake_id = str(uuid.uuid4())
        api_client.headers.pop("Authorization", None)
        response = api_client.put(
            f"{BASE_URL}/api/products/{fake_id}",
            json={"name": "Test"}
        )
        assert response.status_code in [401, 403]
        print("Unauthorized update returns 401/403 as expected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
