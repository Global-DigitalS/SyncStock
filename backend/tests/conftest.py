"""
Shared pytest fixtures for SyncStock backend tests.
Provides authentication, test data factories, and resource cleanup helpers.
"""
import os
import uuid

import pytest
import requests

# ==================== ENVIRONMENT ====================

@pytest.fixture(scope="session")
def base_url():
    """Base URL for the backend API."""
    return os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


@pytest.fixture(scope="session")
def test_credentials():
    """Standard test user credentials."""
    return {
        "email": "test@test.com",
        "password": "test123",
        "name": "Test User",
    }


# ==================== AUTHENTICATION ====================

@pytest.fixture(scope="session")
def auth_token(base_url, test_credentials):
    """JWT token obtained via login."""
    resp = requests.post(
        f"{base_url}/api/auth/login",
        json={
            "email": test_credentials["email"],
            "password": test_credentials["password"],
        },
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json().get("token")


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Authorization headers dict ready for requests."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def api_session(auth_headers):
    """Authenticated requests.Session with pooled connections."""
    session = requests.Session()
    session.headers.update(auth_headers)
    yield session
    session.close()


# ==================== UNIQUE IDS ====================

@pytest.fixture
def unique_id():
    """Short unique hex string for test data isolation."""
    return uuid.uuid4().hex[:8]


@pytest.fixture
def test_prefix(unique_id):
    """TEST_ prefixed unique name for easy cleanup identification."""
    return f"TEST_{unique_id}"


# ==================== TEST DATA FACTORIES ====================

@pytest.fixture
def catalog_data(test_prefix):
    """Sample catalog creation payload."""
    return {
        "name": f"{test_prefix}_Catalog",
        "description": "Catálogo de prueba",
        "is_default": False,
    }


@pytest.fixture
def supplier_data(test_prefix):
    """Sample FTP supplier creation payload."""
    return {
        "name": f"{test_prefix}_Supplier",
        "description": "Proveedor de prueba",
        "ftp_schema": "ftp",
        "ftp_host": "test.ftp.example.com",
        "ftp_user": "testuser",
        "ftp_password": "testpass",
        "ftp_port": 21,
        "ftp_path": "/catalogo/test.csv",
        "ftp_mode": "passive",
        "file_format": "csv",
        "csv_separator": ";",
    }


@pytest.fixture
def woocommerce_store_data(test_prefix):
    """Sample WooCommerce store creation payload."""
    return {
        "name": f"{test_prefix}_WooCommerce",
        "platform": "woocommerce",
        "store_url": "https://test-woocommerce.example.com",
        "consumer_key": "ck_test123456789",
        "consumer_secret": "cs_test987654321",
    }


@pytest.fixture
def shopify_store_data(test_prefix):
    """Sample Shopify store creation payload."""
    return {
        "name": f"{test_prefix}_Shopify",
        "platform": "shopify",
        "store_url": "https://test-shopify.myshopify.com",
        "api_key": "shpat_test123456789",
    }


@pytest.fixture
def prestashop_store_data(test_prefix):
    """Sample PrestaShop store creation payload."""
    return {
        "name": f"{test_prefix}_PrestaShop",
        "platform": "prestashop",
        "store_url": "https://test-prestashop.example.com",
        "api_key": "PS_TEST_KEY_123456789",
    }


@pytest.fixture
def margin_rule_percentage():
    """Percentage-based margin rule payload."""
    return {
        "name": "TEST_Margen_Porcentaje",
        "rule_type": "percentage",
        "value": 15.0,
        "apply_to": "all",
        "priority": 1,
    }


@pytest.fixture
def margin_rule_fixed():
    """Fixed-amount margin rule payload."""
    return {
        "name": "TEST_Margen_Fijo",
        "rule_type": "fixed",
        "value": 5.00,
        "apply_to": "all",
        "priority": 2,
    }


@pytest.fixture
def dolibarr_config():
    """Dolibarr CRM test configuration."""
    return {
        "api_url": "https://demo.dolibarr.org/api/index.php",
        "api_key": "test_invalid_key_for_testing",
    }


@pytest.fixture
def odoo_config():
    """Odoo CRM test configuration."""
    return {
        "api_url": "https://demo.odoo.com",
        "api_token": "test_invalid_token",
    }


# ==================== RESOURCE CLEANUP ====================

@pytest.fixture
def created_resources():
    """Track resource IDs for cleanup. Usage: created_resources['catalogs'].append(id)"""
    return {
        "catalogs": [],
        "suppliers": [],
        "stores": [],
        "crm_connections": [],
    }


@pytest.fixture
def cleanup_resources(base_url, auth_headers, created_resources):
    """Yield the tracker, then delete all tracked resources after the test."""
    yield created_resources

    endpoints = {
        "catalogs": "/api/catalogs",
        "suppliers": "/api/suppliers",
        "stores": "/api/stores",
        "crm_connections": "/api/crm/connections",
    }
    for resource_type, ids in created_resources.items():
        endpoint = endpoints.get(resource_type, "")
        for resource_id in ids:
            try:
                requests.delete(
                    f"{base_url}{endpoint}/{resource_id}",
                    headers=auth_headers,
                )
            except Exception:
                pass


# ==================== VALIDATION HELPERS ====================

def assert_valid_id(obj, label="object"):
    """Assert the object has a non-empty 'id' field."""
    assert "id" in obj, f"{label} missing 'id'"
    assert obj["id"], f"{label} has empty 'id'"


def assert_no_mongo_id(obj, label="object"):
    """Assert MongoDB _id is not exposed."""
    assert "_id" not in obj, f"{label} exposes MongoDB _id"


def assert_has_fields(obj, fields, label="object"):
    """Assert all listed fields are present in the object."""
    for field in fields:
        assert field in obj, f"{label} missing field '{field}'"
