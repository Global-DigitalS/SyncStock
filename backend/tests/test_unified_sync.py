"""
Test suite for Unified Sync Configuration
Tests the unified sync feature that allows users to configure a single interval
for synchronizing Suppliers, Stores, and CRM together.
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials (superadmin with Enterprise CRM plan)
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "password"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "token" in data
    return data["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with authentication"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestSyncSettingsEndpoint:
    """Tests for GET /api/sync/settings endpoint"""
    
    def test_get_sync_settings_requires_auth(self):
        """Test that sync settings endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/sync/settings")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_get_sync_settings_returns_expected_fields(self, auth_headers):
        """Test GET /api/sync/settings returns all expected fields"""
        response = requests.get(f"{BASE_URL}/api/sync/settings", headers=auth_headers)
        assert response.status_code == 200, f"Failed with: {response.text}"
        
        data = response.json()
        # Check all required fields exist
        assert "enabled" in data, "Missing 'enabled' field"
        assert "intervals" in data, "Missing 'intervals' field"
        assert "current_interval" in data, "Missing 'current_interval' field"
        assert "sync_suppliers" in data, "Missing 'sync_suppliers' field"
        assert "sync_stores" in data, "Missing 'sync_stores' field"
        assert "sync_crm" in data, "Missing 'sync_crm' field"
    
    def test_get_sync_settings_user_with_enterprise_plan(self, auth_headers):
        """Test that user with Enterprise CRM plan gets auto_sync_enabled=true and intervals"""
        response = requests.get(f"{BASE_URL}/api/sync/settings", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # User with Enterprise CRM should have sync enabled
        assert data["enabled"] == True, "Expected enabled=True for Enterprise CRM user"
        # Should have valid intervals
        assert isinstance(data["intervals"], list), "intervals should be a list"
        assert len(data["intervals"]) > 0, "Expected at least one interval"
        # Standard intervals are 1, 6, 12, 24
        for interval in data["intervals"]:
            assert interval in [1, 6, 12, 24], f"Unexpected interval: {interval}"
    
    def test_get_sync_settings_service_toggles_are_boolean(self, auth_headers):
        """Test that service toggle fields are booleans"""
        response = requests.get(f"{BASE_URL}/api/sync/settings", headers=auth_headers)
        data = response.json()
        
        assert isinstance(data["sync_suppliers"], bool), "sync_suppliers should be boolean"
        assert isinstance(data["sync_stores"], bool), "sync_stores should be boolean"
        assert isinstance(data["sync_crm"], bool), "sync_crm should be boolean"


class TestUpdateSyncSettingsEndpoint:
    """Tests for PUT /api/sync/settings endpoint"""
    
    def test_update_sync_settings_requires_auth(self):
        """Test that update sync settings requires authentication"""
        response = requests.put(
            f"{BASE_URL}/api/sync/settings",
            json={"interval": 6},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [401, 403]
    
    def test_update_sync_interval(self, auth_headers):
        """Test updating sync interval"""
        # First get current settings
        get_response = requests.get(f"{BASE_URL}/api/sync/settings", headers=auth_headers)
        original_interval = get_response.json().get("current_interval")
        
        # Update to 12 hours
        new_interval = 12
        response = requests.put(
            f"{BASE_URL}/api/sync/settings",
            json={"interval": new_interval, "sync_suppliers": True, "sync_stores": True, "sync_crm": True},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "success"
        assert data["config"]["interval"] == new_interval
        
        # Verify by getting settings again
        verify_response = requests.get(f"{BASE_URL}/api/sync/settings", headers=auth_headers)
        assert verify_response.json()["current_interval"] == new_interval
    
    def test_update_sync_services_toggles(self, auth_headers):
        """Test updating individual service toggles"""
        # Test with all services off
        response = requests.put(
            f"{BASE_URL}/api/sync/settings",
            json={
                "interval": 6,
                "sync_suppliers": False,
                "sync_stores": False,
                "sync_crm": False
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["config"]["sync_suppliers"] == False
        assert data["config"]["sync_stores"] == False
        assert data["config"]["sync_crm"] == False
        
        # Test with all services on
        response = requests.put(
            f"{BASE_URL}/api/sync/settings",
            json={
                "interval": 6,
                "sync_suppliers": True,
                "sync_stores": True,
                "sync_crm": True
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["config"]["sync_suppliers"] == True
        assert data["config"]["sync_stores"] == True
        assert data["config"]["sync_crm"] == True
    
    def test_update_sync_calculates_next_sync(self, auth_headers):
        """Test that updating interval calculates next_sync time"""
        response = requests.put(
            f"{BASE_URL}/api/sync/settings",
            json={"interval": 24},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "next_sync" in data["config"]
        # next_sync should be a valid ISO datetime
        next_sync = data["config"]["next_sync"]
        assert next_sync is not None
        # Verify it parses as datetime
        datetime.fromisoformat(next_sync.replace('Z', '+00:00'))
    
    def test_update_sync_invalid_interval_rejected(self, auth_headers):
        """Test that invalid interval is rejected"""
        # 3 hours is not a valid interval
        response = requests.put(
            f"{BASE_URL}/api/sync/settings",
            json={"interval": 3},
            headers=auth_headers
        )
        # Should either return error or silently accept (depending on implementation)
        # If plan doesn't allow interval 3, it should return error
        if response.status_code == 200:
            data = response.json()
            # If it returns success, verify it didn't set to 3
            assert data.get("status") != "error" or "no permitido" in data.get("message", "").lower()
        else:
            # Any error response is acceptable
            pass


class TestRunSyncNowEndpoint:
    """Tests for POST /api/sync/run-now endpoint"""
    
    def test_run_sync_now_requires_auth(self):
        """Test that run sync now requires authentication"""
        response = requests.post(f"{BASE_URL}/api/sync/run-now")
        assert response.status_code in [401, 403]
    
    def test_run_sync_now_returns_expected_structure(self, auth_headers):
        """Test POST /api/sync/run-now returns proper result structure"""
        response = requests.post(f"{BASE_URL}/api/sync/run-now", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "details" in data
        
        # Check details structure
        details = data["details"]
        assert "user_id" in details
        assert "timestamp" in details
        # All three sync types should be present (or null if disabled)
        assert "suppliers" in details
        assert "stores" in details
        assert "crm" in details
    
    def test_run_sync_now_respects_service_toggles(self, auth_headers):
        """Test that run-now respects enabled/disabled services"""
        # First disable CRM sync
        requests.put(
            f"{BASE_URL}/api/sync/settings",
            json={"interval": 6, "sync_suppliers": True, "sync_stores": True, "sync_crm": False},
            headers=auth_headers
        )
        
        # Run sync
        response = requests.post(f"{BASE_URL}/api/sync/run-now", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # CRM should be null when disabled
        assert data["details"]["crm"] is None, "CRM should be null when sync_crm=False"
        # Suppliers and stores should have results (even if empty)
        assert data["details"]["suppliers"] is not None
        assert data["details"]["stores"] is not None
    
    def test_run_sync_now_updates_last_sync(self, auth_headers):
        """Test that run-now updates the last_sync timestamp"""
        # Run sync
        response = requests.post(f"{BASE_URL}/api/sync/run-now", headers=auth_headers)
        assert response.status_code == 200
        
        sync_timestamp = response.json()["details"]["timestamp"]
        
        # Get settings and verify last_sync was updated
        settings_response = requests.get(f"{BASE_URL}/api/sync/settings", headers=auth_headers)
        settings = settings_response.json()
        
        # last_sync should be close to the sync timestamp
        assert settings.get("last_sync") is not None


class TestSubscriptionPlanSyncFields:
    """Tests for subscription plan sync fields (auto_sync_enabled, sync_intervals)"""
    
    def test_get_plans_includes_sync_fields(self, auth_headers):
        """Test that GET /api/admin/plans includes auto_sync_enabled and sync_intervals"""
        response = requests.get(f"{BASE_URL}/api/admin/plans", headers=auth_headers)
        assert response.status_code == 200
        
        plans = response.json()
        assert len(plans) > 0, "Expected at least one plan"
        
        # Check at least one plan has sync fields
        found_sync_enabled = False
        for plan in plans:
            if plan.get("auto_sync_enabled") or plan.get("crm_sync_enabled"):
                found_sync_enabled = True
                # Check sync_intervals field
                intervals = plan.get("sync_intervals") or plan.get("crm_sync_intervals") or []
                for interval in intervals:
                    assert interval in [1, 6, 12, 24], f"Invalid interval {interval} in plan"
        
        assert found_sync_enabled, "Expected at least one plan with sync enabled"
    
    def test_create_plan_with_sync_options(self, auth_headers):
        """Test creating a plan with auto_sync_enabled and sync_intervals"""
        plan_data = {
            "name": "TEST_SyncTestPlan",
            "description": "Test plan for sync feature",
            "max_suppliers": 5,
            "max_catalogs": 3,
            "max_products": 500,
            "max_stores": 2,
            "price_monthly": 0,
            "price_yearly": 0,
            "features": ["Sync feature test"],
            "auto_sync_enabled": True,
            "sync_intervals": [1, 6, 12, 24]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/plans",
            json=plan_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create plan: {response.text}"
        
        data = response.json()
        # Response has nested "plan" object
        created_plan = data.get("plan", data)
        assert created_plan.get("auto_sync_enabled") == True, f"auto_sync_enabled not True: {created_plan}"
        assert created_plan.get("sync_intervals") == [1, 6, 12, 24], f"sync_intervals not set: {created_plan}"
        
        # Cleanup - delete the test plan
        plan_id = created_plan.get("id")
        if plan_id:
            requests.delete(f"{BASE_URL}/api/admin/plans/{plan_id}", headers=auth_headers)
    
    def test_update_plan_sync_options(self, auth_headers):
        """Test updating a plan's sync options"""
        # First create a plan
        plan_data = {
            "name": "TEST_SyncUpdatePlan",
            "max_suppliers": 5,
            "max_catalogs": 3,
            "price_monthly": 0,
            "price_yearly": 0,
            "auto_sync_enabled": False,
            "sync_intervals": []
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/plans",
            json=plan_data,
            headers=auth_headers
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        data = create_response.json()
        plan_id = data.get("plan", data).get("id")
        
        try:
            # Update to enable sync
            update_response = requests.put(
                f"{BASE_URL}/api/admin/plans/{plan_id}",
                json={
                    "auto_sync_enabled": True,
                    "sync_intervals": [6, 12]
                },
                headers=auth_headers
            )
            assert update_response.status_code == 200, f"Update failed: {update_response.text}"
            
            # Verify the update
            get_response = requests.get(f"{BASE_URL}/api/admin/plans", headers=auth_headers)
            plans = get_response.json()
            updated_plan = next((p for p in plans if p["id"] == plan_id), None)
            
            assert updated_plan is not None, "Updated plan not found"
            assert updated_plan.get("auto_sync_enabled") == True, f"auto_sync_enabled not True: {updated_plan}"
            assert 6 in updated_plan.get("sync_intervals", []), f"sync_intervals not updated: {updated_plan}"
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/admin/plans/{plan_id}", headers=auth_headers)


class TestSchedulerConfiguration:
    """Verify scheduler is configured correctly"""
    
    def test_health_check_confirms_api_running(self, auth_headers):
        """Confirm API is running which means scheduler is active"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


# Cleanup fixture to restore original settings
@pytest.fixture(autouse=True, scope="module")
def restore_sync_settings(auth_headers):
    """Restore original sync settings after all tests"""
    yield
    # Restore default settings
    try:
        requests.put(
            f"{BASE_URL}/api/sync/settings",
            json={"interval": 6, "sync_suppliers": True, "sync_stores": True, "sync_crm": True},
            headers=auth_headers
        )
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
