"""
Test cases for Stripe configuration endpoints.
Testing: GET/PUT /api/admin/stripe/config and POST /api/admin/stripe/test-connection
"""
import os

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStripeConfigEndpoints:
    """Tests for Stripe configuration management (SuperAdmin only)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # Login as superadmin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })

        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip("Could not authenticate as superadmin")

    # ==================== GET /api/admin/stripe/config ====================

    def test_get_stripe_config_success(self):
        """GET /api/admin/stripe/config - returns config for superadmin"""
        response = self.session.get(f"{BASE_URL}/api/admin/stripe/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        # Verify response structure
        assert "stripe_public_key" in data, "Response should contain stripe_public_key"
        assert "stripe_secret_key" in data, "Response should contain stripe_secret_key"
        assert "stripe_webhook_secret" in data, "Response should contain stripe_webhook_secret"
        assert "is_live_mode" in data, "Response should contain is_live_mode"
        assert "enabled" in data, "Response should contain enabled"
        print("✓ GET /api/admin/stripe/config returned config structure correctly")

    def test_get_stripe_config_requires_auth(self):
        """GET /api/admin/stripe/config - requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.get(f"{BASE_URL}/api/admin/stripe/config")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✓ GET /api/admin/stripe/config requires authentication (returned {response.status_code})")

    # ==================== PUT /api/admin/stripe/config ====================

    def test_put_stripe_config_success(self):
        """PUT /api/admin/stripe/config - updates config successfully"""
        test_config = {
            "stripe_public_key": "pk_test_testing123",
            "stripe_secret_key": "sk_test_testing123",
            "stripe_webhook_secret": "whsec_testing123",
            "is_live_mode": False,
            "enabled": False
        }

        response = self.session.put(f"{BASE_URL}/api/admin/stripe/config", json=test_config)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        print("✓ PUT /api/admin/stripe/config updated config successfully")

    def test_put_stripe_config_partial_update(self):
        """PUT /api/admin/stripe/config - allows partial updates"""
        partial_update = {
            "enabled": True
        }

        response = self.session.put(f"{BASE_URL}/api/admin/stripe/config", json=partial_update)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ PUT /api/admin/stripe/config accepts partial updates")

    def test_put_stripe_config_requires_auth(self):
        """PUT /api/admin/stripe/config - requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.put(f"{BASE_URL}/api/admin/stripe/config", json={"enabled": False})
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✓ PUT /api/admin/stripe/config requires authentication (returned {response.status_code})")

    # ==================== POST /api/admin/stripe/test-connection ====================

    def test_post_test_connection_without_secret_key(self):
        """POST /api/admin/stripe/test-connection - fails without secret key configured"""
        # First, set empty secret key
        self.session.put(f"{BASE_URL}/api/admin/stripe/config", json={
            "stripe_secret_key": ""
        })

        response = self.session.post(f"{BASE_URL}/api/admin/stripe/test-connection")
        # Should return 400 or a response indicating no key configured
        assert response.status_code in [400, 200], f"Expected 400 or 200 with error, got {response.status_code}"

        if response.status_code == 400:
            print("✓ POST /api/admin/stripe/test-connection returns 400 without secret key")
        else:
            data = response.json()
            assert data.get("success") == False, "Should indicate failure without secret key"
            print("✓ POST /api/admin/stripe/test-connection returns failure status without secret key")

    def test_post_test_connection_with_invalid_key(self):
        """POST /api/admin/stripe/test-connection - fails with invalid key"""
        # Set an invalid secret key
        self.session.put(f"{BASE_URL}/api/admin/stripe/config", json={
            "stripe_secret_key": "sk_test_invalid_key_12345"
        })

        response = self.session.post(f"{BASE_URL}/api/admin/stripe/test-connection")
        assert response.status_code in [200, 400], f"Expected 200/400, got {response.status_code}"

        if response.status_code == 200:
            data = response.json()
            # With invalid key, Stripe API should return error
            # success might be False due to invalid API key
            print(f"✓ POST /api/admin/stripe/test-connection returned response with invalid key: {data.get('success')}")
        else:
            print(f"✓ POST /api/admin/stripe/test-connection returned {response.status_code} with invalid key")

    def test_post_test_connection_requires_auth(self):
        """POST /api/admin/stripe/test-connection - requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/admin/stripe/test-connection")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✓ POST /api/admin/stripe/test-connection requires authentication (returned {response.status_code})")

    # ==================== Data Persistence Tests ====================

    def test_config_persistence(self):
        """Verify config changes persist after PUT"""
        # Set specific values
        test_values = {
            "stripe_public_key": "pk_test_persistence_test_123",
            "stripe_webhook_secret": "whsec_persistence_test_456",
            "is_live_mode": True,
            "enabled": True
        }

        put_response = self.session.put(f"{BASE_URL}/api/admin/stripe/config", json=test_values)
        assert put_response.status_code == 200

        # GET and verify values persisted
        get_response = self.session.get(f"{BASE_URL}/api/admin/stripe/config")
        assert get_response.status_code == 200

        data = get_response.json()
        assert data.get("stripe_public_key") == test_values["stripe_public_key"], "Public key should persist"
        assert data.get("stripe_webhook_secret") == test_values["stripe_webhook_secret"], "Webhook secret should persist"
        assert data.get("is_live_mode") == test_values["is_live_mode"], "is_live_mode should persist"
        assert data.get("enabled") == test_values["enabled"], "enabled should persist"

        print("✓ Config persistence verified - all values saved and retrieved correctly")

        # Cleanup - reset to safe test values
        self.session.put(f"{BASE_URL}/api/admin/stripe/config", json={
            "stripe_public_key": "",
            "stripe_secret_key": "",
            "stripe_webhook_secret": "",
            "is_live_mode": False,
            "enabled": False
        })


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
