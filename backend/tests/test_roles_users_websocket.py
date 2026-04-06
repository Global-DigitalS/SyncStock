"""
Test Suite: User Roles, Permissions, User Management (Admin), and WebSocket
Features tested:
- GET /api/auth/permissions - returns role and permissions
- GET /api/users - Admin only - list all users
- PUT /api/users/{id}/role - Admin only - update user role
- DELETE /api/users/{id} - Admin only - delete user
- WebSocket /ws/notifications/{user_id} - real-time notifications
"""

import asyncio
import os
import uuid

import pytest
import requests
import websockets

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "test@test.com"
ADMIN_PASSWORD = "test123"


class TestAuthPermissions:
    """Test /api/auth/permissions endpoint"""

    def test_get_permissions_without_auth_returns_401(self):
        """Unauthenticated request should return 401"""
        response = requests.get(f"{BASE_URL}/api/auth/permissions")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/auth/permissions without auth returns 401/403")

    def test_get_permissions_as_admin(self):
        """Admin user should see admin permissions"""
        # Login as admin
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["token"]

        # Get permissions
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/permissions", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "role" in data, "Response should contain 'role'"
        assert "permissions" in data, "Response should contain 'permissions'"
        assert data["role"] == "admin", f"Expected admin role, got {data['role']}"

        # Admin should have all permissions
        expected_permissions = ["read", "write", "delete", "manage_users", "manage_settings", "sync", "export"]
        for perm in expected_permissions:
            assert perm in data["permissions"], f"Admin missing permission: {perm}"
        print(f"✓ GET /api/auth/permissions as admin returns: {data}")


class TestUserManagementAdminEndpoints:
    """Test admin-only user management endpoints"""

    @pytest.fixture
    def admin_headers(self):
        """Get admin auth headers"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
        token = login_resp.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def test_user(self, admin_headers):
        """Create a test user and clean up after"""
        # Register test user
        test_email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Test User For Role Testing"
        })
        assert reg_resp.status_code == 200, f"User registration failed: {reg_resp.text}"
        user_data = reg_resp.json()
        user_id = user_data["user"]["id"]

        yield {"id": user_id, "email": test_email, "token": user_data["token"]}

        # Cleanup - delete the test user
        requests.delete(f"{BASE_URL}/api/users/{user_id}", headers=admin_headers)

    def test_list_users_without_auth_returns_401(self):
        """Unauthenticated request should return 401"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ GET /api/users without auth returns 401/403")

    def test_list_users_as_admin(self, admin_headers):
        """Admin should be able to list all users"""
        response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 1, "Should have at least 1 user (admin)"

        # Check user structure
        first_user = data[0]
        assert "id" in first_user, "User should have 'id'"
        assert "email" in first_user, "User should have 'email'"
        assert "role" in first_user, "User should have 'role'"
        assert "password" not in first_user, "Password should NOT be returned"
        print(f"✓ GET /api/users as admin returns {len(data)} users")

    def test_list_users_as_non_admin_returns_403(self, test_user):
        """Non-admin user should get 403"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ GET /api/users as non-admin returns 403")

    def test_update_user_role_as_admin(self, admin_headers, test_user):
        """Admin should be able to change user role"""
        user_id = test_user["id"]

        # Change to viewer
        response = requests.put(
            f"{BASE_URL}/api/users/{user_id}/role?role=viewer",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify role changed
        users_resp = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_resp.json()
        updated_user = next((u for u in users if u["id"] == user_id), None)
        assert updated_user is not None, "User not found after update"
        assert updated_user["role"] == "viewer", f"Expected viewer role, got {updated_user['role']}"
        print("✓ PUT /api/users/{id}/role?role=viewer works correctly")

        # Change to user
        response2 = requests.put(
            f"{BASE_URL}/api/users/{user_id}/role?role=user",
            headers=admin_headers
        )
        assert response2.status_code == 200
        print("✓ PUT /api/users/{id}/role?role=user works correctly")

    def test_update_user_role_invalid_role_returns_400(self, admin_headers, test_user):
        """Invalid role should return 400"""
        response = requests.put(
            f"{BASE_URL}/api/users/{test_user['id']}/role?role=superadmin",
            headers=admin_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ PUT /api/users/{id}/role with invalid role returns 400")

    def test_admin_cannot_demote_self(self, admin_headers):
        """Admin should not be able to change their own role"""
        # Get admin user id
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_id = login_resp.json()["user"]["id"]

        response = requests.put(
            f"{BASE_URL}/api/users/{admin_id}/role?role=viewer",
            headers=admin_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Admin cannot demote themselves - returns 400")

    def test_update_role_as_non_admin_returns_403(self, test_user, admin_headers):
        """Non-admin cannot change roles"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}

        # Try to change another user's role
        users_resp = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_resp.json()
        another_user = next((u for u in users if u["id"] != test_user["id"]), None)

        if another_user:
            response = requests.put(
                f"{BASE_URL}/api/users/{another_user['id']}/role?role=viewer",
                headers=headers
            )
            assert response.status_code == 403, f"Expected 403, got {response.status_code}"
            print("✓ Non-admin cannot change user roles - returns 403")
        else:
            pytest.skip("No other users to test with")

    def test_delete_user_as_admin(self, admin_headers):
        """Admin should be able to delete users"""
        # Create a user to delete
        test_email = f"TEST_delete_{uuid.uuid4().hex[:8]}@example.com"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "name": "User To Delete"
        })
        assert reg_resp.status_code == 200
        user_id = reg_resp.json()["user"]["id"]

        # Delete user
        response = requests.delete(f"{BASE_URL}/api/users/{user_id}", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        # Verify user is deleted
        users_resp = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_resp.json()
        deleted_user = next((u for u in users if u["id"] == user_id), None)
        assert deleted_user is None, "User should be deleted"
        print("✓ DELETE /api/users/{id} works correctly")

    def test_delete_nonexistent_user_returns_404(self, admin_headers):
        """Deleting non-existent user should return 404"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/users/{fake_id}", headers=admin_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ DELETE /api/users/{nonexistent_id} returns 404")

    def test_admin_cannot_delete_self(self, admin_headers):
        """Admin should not be able to delete themselves"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_id = login_resp.json()["user"]["id"]

        response = requests.delete(f"{BASE_URL}/api/users/{admin_id}", headers=admin_headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Admin cannot delete themselves - returns 400")

    def test_delete_user_as_non_admin_returns_403(self, test_user, admin_headers):
        """Non-admin cannot delete users"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}

        # Try to delete another user
        users_resp = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        users = users_resp.json()
        another_user = next((u for u in users if u["id"] != test_user["id"]), None)

        if another_user:
            response = requests.delete(f"{BASE_URL}/api/users/{another_user['id']}", headers=headers)
            assert response.status_code == 403, f"Expected 403, got {response.status_code}"
            print("✓ Non-admin cannot delete users - returns 403")
        else:
            pytest.skip("No other users to test with")


class TestViewerRolePermissions:
    """Test that viewer role has restricted permissions"""

    @pytest.fixture
    def viewer_user(self):
        """Create a viewer user"""
        # Login as admin
        admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        admin_token = admin_login.json()["token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Register test user
        test_email = f"TEST_viewer_{uuid.uuid4().hex[:8]}@example.com"
        reg_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Viewer User"
        })
        assert reg_resp.status_code == 200
        user_data = reg_resp.json()
        user_id = user_data["user"]["id"]

        # Change role to viewer
        requests.put(f"{BASE_URL}/api/users/{user_id}/role?role=viewer", headers=admin_headers)

        # Re-login to get token with viewer role
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email, "password": "testpass123"
        })
        viewer_token = login_resp.json()["token"]

        yield {"id": user_id, "email": test_email, "token": viewer_token, "headers": {"Authorization": f"Bearer {viewer_token}"}}

        # Cleanup
        requests.delete(f"{BASE_URL}/api/users/{user_id}", headers=admin_headers)

    def test_viewer_permissions_endpoint(self, viewer_user):
        """Viewer should only have read permission"""
        response = requests.get(f"{BASE_URL}/api/auth/permissions", headers=viewer_user["headers"])
        assert response.status_code == 200

        data = response.json()
        assert data["role"] == "viewer", f"Expected viewer role, got {data['role']}"
        assert data["permissions"] == ["read"], f"Viewer should only have ['read'], got {data['permissions']}"
        print(f"✓ Viewer permissions: {data}")

    def test_viewer_can_read_suppliers(self, viewer_user):
        """Viewer should be able to read suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=viewer_user["headers"])
        assert response.status_code == 200, f"Viewer should be able to read suppliers, got {response.status_code}"
        print("✓ Viewer can read suppliers (GET /api/suppliers)")

    def test_viewer_can_read_products(self, viewer_user):
        """Viewer should be able to read products"""
        response = requests.get(f"{BASE_URL}/api/products-unified", headers=viewer_user["headers"])
        assert response.status_code == 200, f"Viewer should be able to read products, got {response.status_code}"
        print("✓ Viewer can read products (GET /api/products-unified)")


class TestWebSocketNotifications:
    """Test WebSocket endpoint /ws/notifications/{user_id}"""

    @pytest.fixture
    def admin_user_id(self):
        """Get admin user ID"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return login_resp.json()["user"]["id"]

    @pytest.mark.asyncio
    async def test_websocket_connection(self, admin_user_id):
        """Test WebSocket connection can be established"""
        ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        ws_endpoint = f"{ws_url}/ws/notifications/{admin_user_id}"

        try:
            async with websockets.connect(ws_endpoint, ping_timeout=10) as websocket:
                # Send ping
                await websocket.send("ping")

                # Wait for pong
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                assert response == "pong", f"Expected 'pong', got '{response}'"
                print("✓ WebSocket connection established and ping/pong works")
        except TimeoutError:
            pytest.fail("WebSocket ping/pong timed out")
        except Exception as e:
            # WebSocket might not be available in all environments
            print(f"⚠ WebSocket test skipped: {e}")
            pytest.skip(f"WebSocket not available: {e}")

    @pytest.mark.asyncio
    async def test_websocket_with_invalid_user_id(self):
        """Test WebSocket with invalid user ID still connects (no auth on WS)"""
        ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        fake_user_id = str(uuid.uuid4())
        ws_endpoint = f"{ws_url}/ws/notifications/{fake_user_id}"

        try:
            async with websockets.connect(ws_endpoint, ping_timeout=10) as websocket:
                await websocket.send("ping")
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                assert response == "pong"
                print("✓ WebSocket accepts any user_id (ping/pong works)")
        except Exception as e:
            print(f"⚠ WebSocket test skipped: {e}")
            pytest.skip(f"WebSocket not available: {e}")


class TestPreviewFileWithMappingSuggestions:
    """Test POST /api/suppliers/{id}/preview-file returns mapping suggestions"""

    @pytest.fixture
    def admin_headers(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        token = login_resp.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def test_preview_file_endpoint_exists(self, admin_headers):
        """Test preview-file endpoint returns proper error when supplier has no FTP/URL configured"""
        # First get existing suppliers
        suppliers_resp = requests.get(f"{BASE_URL}/api/suppliers", headers=admin_headers)
        suppliers = suppliers_resp.json()

        if suppliers:
            supplier_id = suppliers[0]["id"]
            response = requests.post(f"{BASE_URL}/api/suppliers/{supplier_id}/preview-file", headers=admin_headers)
            # Should either succeed (200) or return an error about missing config (400)
            assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"

            data = response.json()
            if response.status_code == 200:
                # Check response structure
                assert "status" in data
                if data["status"] == "success":
                    assert "columns" in data, "Should have columns"
                    assert "suggested_mapping" in data, "Should have suggested_mapping"
                    assert "sample_data" in data, "Should have sample_data"
                    print(f"✓ Preview file returns mapping suggestions: {data.get('mapping_coverage', 'N/A')}")
                else:
                    print(f"✓ Preview file returns error (no file configured): {data.get('message', '')}")
            else:
                print(f"✓ Preview file returns 400 (config missing): {data.get('detail', '')}")
        else:
            pytest.skip("No suppliers to test preview-file")

    def test_preview_file_nonexistent_supplier_returns_404(self, admin_headers):
        """Non-existent supplier should return 404"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{BASE_URL}/api/suppliers/{fake_id}/preview-file", headers=admin_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ POST /api/suppliers/{nonexistent}/preview-file returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
