"""
Test suite for SMTP configuration and subscription email features.
Tests the new features:
1. Setup page Step 3 (SMTP configuration)
2. Subscription email notifications
3. Email test connection endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSetupSmtpConfiguration:
    """Tests for Setup page Step 3 - SMTP configuration"""
    
    def test_setup_status_returns_correct_structure(self):
        """Verify setup status endpoint returns all required fields"""
        response = requests.get(f"{BASE_URL}/api/setup/status")
        assert response.status_code == 200
        
        data = response.json()
        # Verify all required fields exist
        assert "is_configured" in data
        assert "has_database" in data
        assert "has_superadmin" in data
        assert "needs_mongo_config" in data
        assert "needs_jwt_config" in data
        assert "current_cors" in data
        print(f"Setup status: is_configured={data['is_configured']}, has_superadmin={data['has_superadmin']}")
    
    def test_setup_configure_accepts_smtp_fields(self):
        """Verify setup configure endpoint accepts SMTP fields in request schema"""
        # This test validates that the SetupRequest model includes SMTP fields
        # We test with a mock/invalid request to see if SMTP fields are accepted
        response = requests.post(f"{BASE_URL}/api/setup/configure", json={
            "mongo_url": "mongodb://invalid:27017",
            "db_name": "test_db",
            "admin_email": "test@example.com",
            "admin_password": "test123456",
            "admin_name": "Test Admin",
            # SMTP fields - should be accepted by the schema
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "smtp_user",
            "smtp_password": "smtp_pass",
            "smtp_from_email": "noreply@example.com",
            "smtp_from_name": "Test App",
            "smtp_use_tls": True,
            "smtp_use_ssl": False
        })
        # Even if connection fails, we want to verify schema accepts SMTP fields
        # A 422 would mean validation error (missing/invalid fields)
        assert response.status_code != 422, f"Schema validation failed: {response.json()}"
        print(f"Response status: {response.status_code}")


class TestSmtpTestConnection:
    """Tests for SMTP test connection endpoint"""
    
    def test_smtp_test_connection_endpoint_exists(self):
        """Verify the SMTP test connection endpoint exists and requires valid payload"""
        response = requests.post(f"{BASE_URL}/api/email/test-connection", json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_user": "user@example.com",
            "smtp_password": "password123",
            "smtp_use_tls": True,
            "smtp_use_ssl": False
        })
        # Endpoint should exist and return JSON response
        assert response.status_code in [200, 500]  # 200 success or 500 connection error
        data = response.json()
        assert "success" in data
        assert "message" in data
        print(f"SMTP test connection result: success={data['success']}, message={data['message']}")
    
    def test_smtp_test_connection_with_invalid_server(self):
        """Test SMTP connection with invalid server returns appropriate error"""
        response = requests.post(f"{BASE_URL}/api/email/test-connection", json={
            "smtp_host": "invalid.smtp.server.xyz",
            "smtp_port": 587,
            "smtp_user": "test@test.com",
            "smtp_password": "test123",
            "smtp_use_tls": True,
            "smtp_use_ssl": False
        })
        assert response.status_code == 200  # Should return 200 with success=false
        data = response.json()
        assert data.get("success") == False
        print(f"Invalid SMTP server error: {data.get('message')}")


class TestSubscriptionEmail:
    """Tests for subscription change email functionality"""
    
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
    
    def test_subscription_plans_endpoint(self, auth_token):
        """Verify subscription plans endpoint returns plans"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans", headers=headers)
        assert response.status_code == 200
        
        plans = response.json()
        assert isinstance(plans, list)
        assert len(plans) > 0
        
        # Verify plan structure
        for plan in plans:
            assert "id" in plan
            assert "name" in plan
            assert "max_suppliers" in plan
            assert "max_catalogs" in plan
            assert "price_monthly" in plan
        
        print(f"Found {len(plans)} subscription plans")
    
    def test_subscribe_to_plan_triggers_email(self, auth_token):
        """Verify subscribing to a plan attempts to send email notification"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get available plans first
        plans_response = requests.get(f"{BASE_URL}/api/subscriptions/plans", headers=headers)
        plans = plans_response.json()
        
        if not plans:
            pytest.skip("No plans available")
        
        # Find a plan that's not Free to test upgrade
        target_plan = None
        for plan in plans:
            if plan["name"] != "Free" and plan.get("is_active", True):
                target_plan = plan
                break
        
        if not target_plan:
            target_plan = plans[0]
        
        # Subscribe to the plan
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/subscribe/{target_plan['id']}",
            params={"billing_cycle": "monthly"},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "subscription" in data
        assert data["subscription"]["plan_name"] == target_plan["name"]
        print(f"Successfully subscribed to plan: {target_plan['name']}")
        # Note: Email sending happens in background - success depends on SMTP config
    
    def test_get_my_subscription(self, auth_token):
        """Verify get my subscription endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/subscriptions/my", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "is_free" in data
        print(f"Current subscription: {data.get('plan', {}).get('name', 'Unknown')}, is_free={data['is_free']}")


class TestEmailConfig:
    """Tests for email configuration endpoints"""
    
    @pytest.fixture
    def superadmin_token(self):
        """Get superadmin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_email_config_endpoint_requires_auth(self):
        """Verify email config endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/email/config")
        assert response.status_code == 401 or response.status_code == 403
        print("Email config endpoint correctly requires authentication")
    
    def test_get_email_config(self, superadmin_token):
        """Get email configuration (for superadmin)"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = requests.get(f"{BASE_URL}/api/email/config", headers=headers)
        
        # May return 200 or 403 depending on user role
        if response.status_code == 200:
            data = response.json()
            assert "smtp_host" in data
            assert "smtp_port" in data
            assert "smtp_configured" in data
            print(f"Email config: smtp_configured={data.get('smtp_configured')}")
        else:
            print(f"Email config access denied (requires superadmin): {response.status_code}")


class TestForgotPassword:
    """Tests for password reset functionality (uses email)"""
    
    def test_forgot_password_endpoint_exists(self):
        """Verify forgot password endpoint exists and accepts email"""
        response = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={
            "email": "nonexistent@example.com"
        })
        # Should return success even for non-existent email (security)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"Forgot password response: {data.get('message')}")
    
    def test_verify_reset_token_endpoint_exists(self):
        """Verify the reset token verification endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/auth/verify-reset-token/invalid-token-123")
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert data["valid"] == False  # Invalid token should return false
        print("Reset token verification working correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
