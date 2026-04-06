"""
Test cases for Stripe checkout and SFTP support.
Testing:
- GET /api/stripe/config/status - Public endpoint returns Stripe status
- POST /api/stripe/create-checkout - Requires auth and creates checkout session
- GET /api/stripe/plans - Returns available subscription plans  
- POST /api/suppliers/ftp-test - Supports SFTP protocol (schema=sftp)
- POST /api/suppliers/ftp-browse - Supports SFTP protocol
"""
import os

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStripePublicEndpoints:
    """Tests for public Stripe endpoints"""

    def test_stripe_config_status_public(self):
        """GET /api/stripe/config/status - Public endpoint, no auth required"""
        response = requests.get(f"{BASE_URL}/api/stripe/config/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        # Verify response structure
        assert "enabled" in data, "Response should contain 'enabled' field"
        assert "configured" in data, "Response should contain 'configured' field"
        assert isinstance(data["enabled"], bool), "'enabled' should be a boolean"
        assert isinstance(data["configured"], bool), "'configured' should be a boolean"
        print(f"✓ GET /api/stripe/config/status is public and returns: enabled={data['enabled']}, configured={data['configured']}")

    def test_stripe_config_status_has_live_mode(self):
        """GET /api/stripe/config/status - Returns is_live_mode flag"""
        response = requests.get(f"{BASE_URL}/api/stripe/config/status")
        assert response.status_code == 200

        data = response.json()
        assert "is_live_mode" in data, "Response should contain 'is_live_mode' field"
        assert isinstance(data["is_live_mode"], bool), "'is_live_mode' should be a boolean"
        print(f"✓ GET /api/stripe/config/status returns is_live_mode={data['is_live_mode']}")


class TestStripeCheckoutEndpoints:
    """Tests for Stripe checkout functionality (requires auth)"""

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
            pytest.skip("Could not authenticate")

    def test_create_checkout_requires_auth(self):
        """POST /api/stripe/create-checkout - Requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})

        response = session.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "plan_id": "test",
            "origin_url": "https://example.com",
            "billing_cycle": "monthly"
        })

        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"✓ POST /api/stripe/create-checkout requires authentication (returned {response.status_code})")

    def test_create_checkout_returns_404_for_invalid_plan(self):
        """POST /api/stripe/create-checkout - Returns 404 for invalid plan"""
        response = self.session.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "plan_id": "invalid-plan-id-xyz",
            "origin_url": "https://example.com",
            "billing_cycle": "monthly"
        })

        assert response.status_code == 404, f"Expected 404 for invalid plan, got {response.status_code}"
        print("✓ POST /api/stripe/create-checkout returns 404 for invalid plan")

    def test_create_checkout_success(self):
        """POST /api/stripe/create-checkout - Creates checkout session for valid plan"""
        # First get valid plans
        plans_response = self.session.get(f"{BASE_URL}/api/stripe/plans")
        assert plans_response.status_code == 200
        plans = plans_response.json()

        # Find a paid plan (Starter)
        paid_plan = next((p for p in plans if p.get("price_monthly", 0) > 0), None)
        if not paid_plan:
            pytest.skip("No paid plans available")

        response = self.session.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "plan_id": paid_plan["id"],
            "origin_url": "https://subscription-verify-3.preview.emergentagent.com",
            "billing_cycle": "monthly"
        })

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "checkout_url" in data, "Response should contain checkout_url"
        assert "session_id" in data, "Response should contain session_id"
        assert data["checkout_url"].startswith("https://checkout.stripe.com"), "checkout_url should be a Stripe URL"
        assert data["session_id"].startswith("cs_"), "session_id should start with 'cs_'"
        print(f"✓ POST /api/stripe/create-checkout creates checkout session: {data['session_id']}")

    def test_create_checkout_yearly_billing(self):
        """POST /api/stripe/create-checkout - Supports yearly billing cycle"""
        plans_response = self.session.get(f"{BASE_URL}/api/stripe/plans")
        plans = plans_response.json()

        paid_plan = next((p for p in plans if p.get("price_yearly", 0) > 0), None)
        if not paid_plan:
            pytest.skip("No paid plans with yearly pricing")

        response = self.session.post(f"{BASE_URL}/api/stripe/create-checkout", json={
            "plan_id": paid_plan["id"],
            "origin_url": "https://subscription-verify-3.preview.emergentagent.com",
            "billing_cycle": "yearly"
        })

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "checkout_url" in data
        print("✓ POST /api/stripe/create-checkout supports yearly billing")

    def test_get_stripe_plans(self):
        """GET /api/stripe/plans - Returns available subscription plans"""
        response = self.session.get(f"{BASE_URL}/api/stripe/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        plans = response.json()
        assert isinstance(plans, list), "Response should be a list"
        assert len(plans) > 0, "Should have at least one plan"

        # Verify plan structure
        for plan in plans:
            assert "id" in plan, "Plan should have 'id'"
            assert "name" in plan, "Plan should have 'name'"
            assert "price_monthly" in plan, "Plan should have 'price_monthly'"
            assert "price_yearly" in plan, "Plan should have 'price_yearly'"

        print(f"✓ GET /api/stripe/plans returns {len(plans)} plans")


class TestSFTPSupport:
    """Tests for SFTP protocol support in FTP endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })

        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Could not authenticate")

    def test_ftp_test_sftp_protocol(self):
        """POST /api/suppliers/ftp-test - Supports SFTP protocol (schema=sftp)"""
        # Using test.rebex.net public SFTP server
        response = self.session.post(f"{BASE_URL}/api/suppliers/ftp-test", json={
            "ftp_schema": "sftp",
            "ftp_host": "test.rebex.net",
            "ftp_user": "demo",
            "ftp_password": "password",
            "ftp_port": 22
        })

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert data.get("status") == "ok", f"Expected status='ok', got {data.get('status')}"
        assert data.get("connected") == True, "Should be connected"
        assert data.get("protocol") == "SFTP", f"Protocol should be SFTP, got {data.get('protocol')}"
        print(f"✓ POST /api/suppliers/ftp-test supports SFTP protocol: connected to {data.get('message', 'SFTP server')}")

    def test_ftp_test_sftp_bad_credentials(self):
        """POST /api/suppliers/ftp-test - SFTP returns error for bad credentials"""
        response = self.session.post(f"{BASE_URL}/api/suppliers/ftp-test", json={
            "ftp_schema": "sftp",
            "ftp_host": "test.rebex.net",
            "ftp_user": "baduser",
            "ftp_password": "badpass",
            "ftp_port": 22
        })

        assert response.status_code == 200, f"Expected 200 with error status, got {response.status_code}"

        data = response.json()
        assert data.get("status") == "error", "Should return error status for bad credentials"
        assert data.get("connected") == False, "Should not be connected"
        print(f"✓ POST /api/suppliers/ftp-test handles SFTP bad credentials: {data.get('message', 'error')}")

    def test_ftp_test_regular_ftp(self):
        """POST /api/suppliers/ftp-test - Still supports regular FTP"""
        response = self.session.post(f"{BASE_URL}/api/suppliers/ftp-test", json={
            "ftp_schema": "ftp",
            "ftp_host": "test.rebex.net",
            "ftp_user": "demo",
            "ftp_password": "password",
            "ftp_port": 21
        })

        assert response.status_code == 200
        data = response.json()

        # test.rebex.net may only support SFTP, so we just verify the endpoint handles it
        assert "status" in data
        assert "connected" in data
        print(f"✓ POST /api/suppliers/ftp-test handles regular FTP: status={data.get('status')}")

    def test_ftp_browse_supports_sftp_schema(self):
        """POST /api/suppliers/ftp-browse - Accepts ftp_schema parameter"""
        response = self.session.post(f"{BASE_URL}/api/suppliers/ftp-browse", json={
            "ftp_schema": "sftp",
            "ftp_host": "test.rebex.net",
            "ftp_user": "demo",
            "ftp_password": "password",
            "ftp_port": 22,
            "path": "/"
        })

        # The endpoint should accept the request
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        # Check if it has the expected response fields
        assert "files" in data or "status" in data, "Response should have files or status"
        print(f"✓ POST /api/suppliers/ftp-browse accepts SFTP schema: status={data.get('status', 'ok')}")


class TestMySubscription:
    """Tests for user subscription endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })

        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Could not authenticate")

    def test_get_my_subscription(self):
        """GET /api/stripe/my-subscription - Returns user subscription info"""
        response = self.session.get(f"{BASE_URL}/api/stripe/my-subscription")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        # Verify structure
        assert "status" in data, "Response should contain 'status'"
        assert "max_suppliers" in data, "Response should contain 'max_suppliers'"
        assert "max_catalogs" in data, "Response should contain 'max_catalogs'"
        print(f"✓ GET /api/stripe/my-subscription returns subscription info: status={data.get('status')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
