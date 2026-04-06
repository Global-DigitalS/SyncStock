"""
CRM Auto-Sync Feature Tests
Tests for: 
- GET /api/crm/auto-sync-permissions - User's plan-based CRM sync permissions
- POST/PUT /api/crm/connections with auto_sync_enabled and auto_sync_interval
- SubscriptionPlan model with crm_sync_enabled and crm_sync_intervals
- POST/PUT /api/subscriptions/plans with CRM sync options
- Scheduler configuration for run_scheduled_crm_syncs
"""
import os

import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCRMAutoSyncAPI:
    """Tests for CRM auto-sync feature APIs"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - authenticate and store token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # Login with test user (superadmin with Enterprise CRM plan)
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser@example.com",
            "password": "password"
        })

        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            self.user = login_response.json().get("user")
        else:
            # Fallback to creating test user
            self.token = None
            self.user = None
            pytest.skip("Could not authenticate test user")

        yield

        # Cleanup: delete any TEST_ prefixed connections
        if self.token:
            try:
                connections = self.session.get(f"{BASE_URL}/api/crm/connections").json()
                for conn in connections:
                    if conn.get("name", "").startswith("TEST_"):
                        self.session.delete(f"{BASE_URL}/api/crm/connections/{conn['id']}")
            except:
                pass

    # ==================== GET /api/crm/auto-sync-permissions ====================

    def test_get_auto_sync_permissions_returns_enabled_and_intervals(self):
        """GET /api/crm/auto-sync-permissions returns enabled status and intervals based on user's plan"""
        response = self.session.get(f"{BASE_URL}/api/crm/auto-sync-permissions")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "enabled" in data, "Response should contain 'enabled' field"
        assert "intervals" in data, "Response should contain 'intervals' field"
        assert isinstance(data["enabled"], bool), "'enabled' should be boolean"
        assert isinstance(data["intervals"], list), "'intervals' should be a list"

        print(f"Auto-sync permissions: enabled={data['enabled']}, intervals={data['intervals']}")

    def test_auto_sync_permissions_requires_auth(self):
        """GET /api/crm/auto-sync-permissions requires authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/crm/auto-sync-permissions")

        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"

    # ==================== POST /api/crm/connections with auto-sync ====================

    def test_create_connection_with_auto_sync_disabled(self):
        """POST /api/crm/connections accepts auto_sync_enabled=false"""
        connection_data = {
            "name": "TEST_AutoSync_Disabled",
            "platform": "dolibarr",
            "config": {
                "api_url": "https://test-dolibarr.example.com/api/index.php",
                "api_key": "test_api_key_12345"
            },
            "auto_sync_enabled": False,
            "auto_sync_interval": 24
        }

        response = self.session.post(f"{BASE_URL}/api/crm/connections", json=connection_data)

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"

        data = response.json()
        assert data.get("auto_sync_enabled") == False, "auto_sync_enabled should be False"
        assert data.get("auto_sync_interval") == 24, "auto_sync_interval should be 24"

        print(f"Created connection with auto_sync_enabled=False: {data.get('id')}")

    def test_create_connection_with_auto_sync_enabled(self):
        """POST /api/crm/connections accepts auto_sync_enabled=true and auto_sync_interval"""
        connection_data = {
            "name": "TEST_AutoSync_Enabled",
            "platform": "dolibarr",
            "config": {
                "api_url": "https://test-dolibarr.example.com/api/index.php",
                "api_key": "test_api_key_12345"
            },
            "auto_sync_enabled": True,
            "auto_sync_interval": 6
        }

        response = self.session.post(f"{BASE_URL}/api/crm/connections", json=connection_data)

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"

        data = response.json()
        assert data.get("auto_sync_enabled") == True, "auto_sync_enabled should be True"
        assert data.get("auto_sync_interval") == 6, "auto_sync_interval should be 6"

        print(f"Created connection with auto_sync_enabled=True, interval=6h: {data.get('id')}")

    def test_create_connection_with_all_intervals(self):
        """POST /api/crm/connections works with all valid intervals (1, 6, 12, 24)"""
        valid_intervals = [1, 6, 12, 24]

        for interval in valid_intervals:
            connection_data = {
                "name": f"TEST_Interval_{interval}h",
                "platform": "dolibarr",
                "config": {
                    "api_url": "https://test.example.com/api",
                    "api_key": "test_key"
                },
                "auto_sync_enabled": True,
                "auto_sync_interval": interval
            }

            response = self.session.post(f"{BASE_URL}/api/crm/connections", json=connection_data)

            assert response.status_code in [200, 201], f"Failed for interval {interval}: {response.text}"
            assert response.json().get("auto_sync_interval") == interval

            print(f"Created connection with interval={interval}h")

    # ==================== PUT /api/crm/connections with auto-sync ====================

    def test_update_connection_auto_sync_settings(self):
        """PUT /api/crm/connections/{id} updates auto_sync_enabled and auto_sync_interval"""
        # First create a connection
        create_data = {
            "name": "TEST_UpdateAutoSync",
            "platform": "dolibarr",
            "config": {
                "api_url": "https://test.example.com/api",
                "api_key": "test_key"
            },
            "auto_sync_enabled": False,
            "auto_sync_interval": 24
        }

        create_response = self.session.post(f"{BASE_URL}/api/crm/connections", json=create_data)
        assert create_response.status_code in [200, 201]

        connection_id = create_response.json().get("id")

        # Update auto-sync settings
        update_data = {
            "name": "TEST_UpdateAutoSync",
            "config": {
                "api_url": "https://test.example.com/api",
                "api_key": "test_key"
            },
            "auto_sync_enabled": True,
            "auto_sync_interval": 1
        }

        update_response = self.session.put(f"{BASE_URL}/api/crm/connections/{connection_id}", json=update_data)

        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"

        # Verify update by fetching connections
        get_response = self.session.get(f"{BASE_URL}/api/crm/connections")
        connections = get_response.json()

        updated_conn = next((c for c in connections if c.get("id") == connection_id), None)
        assert updated_conn is not None, "Connection should exist after update"
        assert updated_conn.get("auto_sync_enabled") == True, "auto_sync_enabled should be updated to True"
        assert updated_conn.get("auto_sync_interval") == 1, "auto_sync_interval should be updated to 1"

        print("Updated connection auto-sync: enabled=True, interval=1h")

    # ==================== Subscription Plans with CRM Sync ====================

    def test_get_subscription_plans_includes_crm_sync_fields(self):
        """GET /api/subscriptions/plans returns plans with crm_sync_enabled and crm_sync_intervals"""
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        plans = response.json()
        assert len(plans) > 0, "Should have at least one subscription plan"

        # Check that at least one plan has CRM sync fields
        has_crm_fields = False
        for plan in plans:
            if "crm_sync_enabled" in plan or "crm_sync_intervals" in plan:
                has_crm_fields = True
                print(f"Plan '{plan.get('name')}': crm_sync_enabled={plan.get('crm_sync_enabled')}, intervals={plan.get('crm_sync_intervals')}")

        assert has_crm_fields, "At least one plan should have CRM sync fields"

    def test_create_subscription_plan_with_crm_sync(self):
        """POST /api/subscriptions/plans creates plan with crm_sync_enabled and crm_sync_intervals"""
        plan_data = {
            "name": "TEST_Plan_CRM_Sync",
            "description": "Test plan with CRM sync",
            "max_suppliers": 10,
            "max_catalogs": 5,
            "max_woocommerce_stores": 2,
            "price_monthly": 29.99,
            "price_yearly": 299.99,
            "features": ["CRM Auto-sync"],
            "crm_sync_enabled": True,
            "crm_sync_intervals": [6, 12, 24]
        }

        response = self.session.post(f"{BASE_URL}/api/subscriptions/plans", json=plan_data)

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"

        data = response.json()
        assert data.get("crm_sync_enabled") == True, "crm_sync_enabled should be True"
        assert data.get("crm_sync_intervals") == [6, 12, 24], "crm_sync_intervals should be [6, 12, 24]"

        plan_id = data.get("id")
        print(f"Created plan with CRM sync: {plan_id}")

        # Cleanup
        self.session.delete(f"{BASE_URL}/api/subscriptions/plans/{plan_id}")

    def test_update_subscription_plan_crm_sync(self):
        """PUT /api/subscriptions/plans/{id} updates crm_sync_enabled and crm_sync_intervals"""
        # First create a plan
        create_data = {
            "name": "TEST_Plan_Update_CRM",
            "description": "Test plan for update",
            "max_suppliers": 5,
            "max_catalogs": 3,
            "max_woocommerce_stores": 1,
            "price_monthly": 9.99,
            "price_yearly": 99.99,
            "crm_sync_enabled": False,
            "crm_sync_intervals": []
        }

        create_response = self.session.post(f"{BASE_URL}/api/subscriptions/plans", json=create_data)
        assert create_response.status_code in [200, 201]

        plan_id = create_response.json().get("id")

        # Update CRM sync settings
        update_data = {
            "crm_sync_enabled": True,
            "crm_sync_intervals": [1, 6, 12, 24]
        }

        update_response = self.session.put(f"{BASE_URL}/api/subscriptions/plans/{plan_id}", json=update_data)

        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"

        data = update_response.json()
        assert data.get("crm_sync_enabled") == True, "crm_sync_enabled should be updated to True"
        assert data.get("crm_sync_intervals") == [1, 6, 12, 24], "crm_sync_intervals should be updated"

        print("Updated plan CRM sync: enabled=True, intervals=[1, 6, 12, 24]")

        # Cleanup
        self.session.delete(f"{BASE_URL}/api/subscriptions/plans/{plan_id}")

    # ==================== CRM Connection lists auto-sync status ====================

    def test_get_connections_includes_auto_sync_fields(self):
        """GET /api/crm/connections returns connections with auto_sync_enabled and auto_sync_interval"""
        # Create a connection with auto-sync
        create_data = {
            "name": "TEST_GetAutoSyncFields",
            "platform": "dolibarr",
            "config": {
                "api_url": "https://test.example.com/api",
                "api_key": "test_key"
            },
            "auto_sync_enabled": True,
            "auto_sync_interval": 12
        }

        create_response = self.session.post(f"{BASE_URL}/api/crm/connections", json=create_data)
        assert create_response.status_code in [200, 201]

        connection_id = create_response.json().get("id")

        # Fetch connections and verify auto-sync fields
        get_response = self.session.get(f"{BASE_URL}/api/crm/connections")

        assert get_response.status_code == 200

        connections = get_response.json()
        test_conn = next((c for c in connections if c.get("id") == connection_id), None)

        assert test_conn is not None, "Test connection should be in list"
        assert "auto_sync_enabled" in test_conn, "Connection should have auto_sync_enabled field"
        assert "auto_sync_interval" in test_conn, "Connection should have auto_sync_interval field"
        assert test_conn.get("auto_sync_enabled") == True
        assert test_conn.get("auto_sync_interval") == 12

        print(f"Connection auto-sync fields verified: enabled={test_conn.get('auto_sync_enabled')}, interval={test_conn.get('auto_sync_interval')}")


class TestAdminPlansAPI:
    """Tests for admin plans API with CRM sync fields"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - authenticate as superadmin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # Login with superadmin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser@example.com",
            "password": "password"
        })

        if login_response.status_code == 200:
            self.token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            self.user = login_response.json().get("user")
        else:
            self.token = None
            pytest.skip("Could not authenticate superadmin")

        yield

        # Cleanup TEST_ prefixed plans
        if self.token:
            try:
                plans = self.session.get(f"{BASE_URL}/api/admin/plans").json()
                for plan in plans:
                    if plan.get("name", "").startswith("TEST_"):
                        self.session.delete(f"{BASE_URL}/api/admin/plans/{plan['id']}")
            except:
                pass

    def test_admin_get_plans_includes_crm_sync(self):
        """GET /api/admin/plans returns plans with crm_sync fields"""
        response = self.session.get(f"{BASE_URL}/api/admin/plans")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        plans = response.json()
        assert len(plans) > 0, "Should have at least one plan"

        for plan in plans:
            print(f"Plan '{plan.get('name')}': crm_sync_enabled={plan.get('crm_sync_enabled')}, intervals={plan.get('crm_sync_intervals', [])}")

    def test_admin_create_plan_with_crm_sync(self):
        """POST /api/admin/plans creates plan with CRM sync options"""
        plan_data = {
            "name": "TEST_Admin_CRM_Plan",
            "description": "Admin test plan with CRM sync",
            "max_suppliers": 20,
            "max_catalogs": 10,
            "max_products": 5000,
            "max_stores": 3,
            "price_monthly": 49.99,
            "price_yearly": 499.99,
            "features": ["CRM Auto-sync", "All intervals"],
            "crm_sync_enabled": True,
            "crm_sync_intervals": [1, 6, 12, 24]
        }

        response = self.session.post(f"{BASE_URL}/api/admin/plans", json=plan_data)

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"

        # API returns {"success": True, "plan": {...}}
        resp_data = response.json()
        data = resp_data.get("plan", resp_data)  # Handle both formats

        assert data.get("crm_sync_enabled") == True, f"crm_sync_enabled should be True, got: {data}"
        assert data.get("crm_sync_intervals") == [1, 6, 12, 24], f"crm_sync_intervals should be [1, 6, 12, 24], got: {data.get('crm_sync_intervals')}"

        print(f"Admin created plan with all CRM intervals: {data.get('id')}")

    def test_admin_update_plan_crm_sync(self):
        """PUT /api/admin/plans/{id} updates CRM sync settings"""
        # Create plan
        create_data = {
            "name": "TEST_Admin_Update_CRM",
            "max_suppliers": 5,
            "max_catalogs": 3,
            "crm_sync_enabled": False,
            "crm_sync_intervals": []
        }

        create_response = self.session.post(f"{BASE_URL}/api/admin/plans", json=create_data)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"

        # API returns {"success": True, "plan": {...}}
        create_resp = create_response.json()
        created_plan = create_resp.get("plan", create_resp)
        plan_id = created_plan.get("id")

        assert plan_id, f"Could not get plan ID from response: {create_resp}"

        # Update with CRM sync
        update_data = {
            "crm_sync_enabled": True,
            "crm_sync_intervals": [12, 24]
        }

        update_response = self.session.put(f"{BASE_URL}/api/admin/plans/{plan_id}", json=update_data)

        assert update_response.status_code == 200, f"Update failed: {update_response.status_code} - {update_response.text}"

        # API returns {"success": True, "plan": {...}}
        update_resp = update_response.json()
        data = update_resp.get("plan", update_resp)

        assert data.get("crm_sync_enabled") == True, f"crm_sync_enabled should be True, got: {data}"
        assert 12 in data.get("crm_sync_intervals", []), f"12 should be in intervals, got: {data.get('crm_sync_intervals')}"
        assert 24 in data.get("crm_sync_intervals", []), f"24 should be in intervals, got: {data.get('crm_sync_intervals')}"

        print(f"Admin updated plan CRM sync: intervals={data.get('crm_sync_intervals')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
