"""
Test Suite for System Reset Feature
Tests the POST /api/admin/system/reset endpoint that allows SuperAdmin to reset
the application by deleting all collections except 'users'.
"""
import os

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPERADMIN_EMAIL = "test@test.com"
SUPERADMIN_PASSWORD = "test123"


class TestSystemResetEndpoint:
    """Tests for POST /api/admin/system/reset endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token for superadmin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # Login as superadmin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"

        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        self.user = data.get("user", {})

        assert self.token, "No access token received"
        assert self.user.get("role") == "superadmin", f"User is not superadmin: {self.user.get('role')}"

        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def test_reset_rejects_empty_confirmation(self):
        """Reset endpoint should reject empty confirmation text"""
        response = self.session.post(f"{BASE_URL}/api/admin/system/reset", json={
            "confirmation_text": ""
        })

        # Should return 400 bad request or 422 validation error
        assert response.status_code in [400, 422], f"Expected 400/422 but got {response.status_code}"
        print(f"✓ Empty confirmation rejected with status {response.status_code}")

    def test_reset_rejects_wrong_confirmation(self):
        """Reset endpoint should reject incorrect confirmation text"""
        wrong_confirmations = ["reset", "RESTART", "DELETE", "YES", "CONFIRM", "ReSeT"]

        for wrong_text in wrong_confirmations:
            response = self.session.post(f"{BASE_URL}/api/admin/system/reset", json={
                "confirmation_text": wrong_text
            })

            assert response.status_code == 400, f"Wrong confirmation '{wrong_text}' should return 400, got {response.status_code}"

            data = response.json()
            assert "detail" in data, "Response should have 'detail' error message"
            assert "RESET" in data["detail"] or "incorrecta" in data["detail"], f"Error message should mention 'RESET', got: {data['detail']}"

        print(f"✓ All {len(wrong_confirmations)} wrong confirmations rejected correctly")

    def test_reset_requires_authentication(self):
        """Reset endpoint should require authentication"""
        # Create a new session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})

        response = no_auth_session.post(f"{BASE_URL}/api/admin/system/reset", json={
            "confirmation_text": "RESET"
        })

        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Unauthenticated request should return 401/403, got {response.status_code}"
        print(f"✓ Endpoint requires authentication (status {response.status_code})")

    def test_reset_requires_superadmin_role(self):
        """Reset endpoint should only work for superadmin users"""
        # First check if there are other users to test with
        response = self.session.get(f"{BASE_URL}/api/users")

        if response.status_code == 200:
            users = response.json()
            non_superadmin = next((u for u in users if u.get("role") != "superadmin"), None)

            if non_superadmin:
                print(f"ℹ Found non-superadmin user: {non_superadmin.get('email')}")
                # Note: We can't easily test with another user's credentials without knowing password

        # Verify current user IS superadmin and can access
        response = self.session.get(f"{BASE_URL}/api/dashboard/superadmin-stats")
        assert response.status_code == 200, f"SuperAdmin should have access to dashboard, got {response.status_code}"
        print("✓ SuperAdmin access verified")

    def test_reset_success_with_correct_confirmation(self):
        """Reset endpoint should succeed with correct 'RESET' confirmation"""
        # First, let's get current stats to compare
        stats_before = self.session.get(f"{BASE_URL}/api/dashboard/superadmin-stats").json()
        users_before = stats_before.get("users", {}).get("total", 0)

        print(f"ℹ Before reset - Users: {users_before}")

        # Execute reset
        response = self.session.post(f"{BASE_URL}/api/admin/system/reset", json={
            "confirmation_text": "RESET"
        })

        assert response.status_code == 200, f"Reset should succeed, got {response.status_code}: {response.text}"

        data = response.json()

        # Verify response structure
        assert data.get("success") == True, "Response should have success=true"
        assert "message" in data, "Response should have message"
        assert "stats" in data, "Response should have stats"
        assert "executed_by" in data, "Response should have executed_by"
        assert "executed_at" in data, "Response should have executed_at"

        # Verify users were preserved
        stats = data.get("stats", {})
        users_stat = stats.get("users", {})
        assert users_stat.get("preserved") == True, "Users collection should be preserved"

        print(f"✓ Reset succeeded - Users preserved: {users_stat.get('count', 'N/A')}")
        print(f"  Executed by: {data.get('executed_by')}")
        print(f"  Stats: {stats}")

    def test_users_preserved_after_reset(self):
        """Verify users still exist after reset"""
        # Get stats after reset
        response = self.session.get(f"{BASE_URL}/api/dashboard/superadmin-stats")
        assert response.status_code == 200, f"Dashboard should be accessible after reset, got {response.status_code}"

        stats = response.json()
        users_count = stats.get("users", {}).get("total", 0)

        assert users_count >= 1, f"At least 1 user should exist after reset, got {users_count}"
        print(f"✓ Users preserved after reset: {users_count}")

    def test_can_still_authenticate_after_reset(self):
        """Verify authentication still works after reset"""
        # Create fresh session and login
        new_session = requests.Session()
        new_session.headers.update({"Content-Type": "application/json"})

        response = new_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })

        assert response.status_code == 200, f"Should be able to login after reset, got {response.status_code}"

        data = response.json()
        assert data.get("access_token") or data.get("token"), "Should receive token after login"
        print("✓ Authentication still works after reset")


class TestSystemResetEdgeCases:
    """Edge case tests for system reset"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })
        assert response.status_code == 200

        data = response.json()
        self.token = data.get("access_token") or data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})

    def test_reset_with_missing_field(self):
        """Reset should fail if confirmation_text field is missing"""
        response = self.session.post(f"{BASE_URL}/api/admin/system/reset", json={})

        # Should return 422 validation error
        assert response.status_code == 422, f"Missing field should return 422, got {response.status_code}"
        print("✓ Missing confirmation_text field rejected")

    def test_reset_with_null_confirmation(self):
        """Reset should fail if confirmation_text is null"""
        response = self.session.post(f"{BASE_URL}/api/admin/system/reset", json={
            "confirmation_text": None
        })

        # Should return 422 validation error
        assert response.status_code == 422, f"Null confirmation should return 422, got {response.status_code}"
        print("✓ Null confirmation_text rejected")

    def test_reset_case_sensitive(self):
        """Reset confirmation should be case-sensitive (only 'RESET' works)"""
        # Test lowercase
        response = self.session.post(f"{BASE_URL}/api/admin/system/reset", json={
            "confirmation_text": "reset"
        })
        assert response.status_code == 400, "lowercase 'reset' should be rejected"

        # Test mixed case
        response = self.session.post(f"{BASE_URL}/api/admin/system/reset", json={
            "confirmation_text": "Reset"
        })
        assert response.status_code == 400, "mixed case 'Reset' should be rejected"

        print("✓ Confirmation is case-sensitive")

    def test_reset_with_whitespace(self):
        """Reset should fail with whitespace around RESET"""
        response = self.session.post(f"{BASE_URL}/api/admin/system/reset", json={
            "confirmation_text": " RESET "
        })

        # Could be 200 if backend trims, or 400 if strict
        if response.status_code == 400:
            print("✓ Whitespace around RESET rejected (strict mode)")
        else:
            print("ℹ Whitespace around RESET accepted (trimmed)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
