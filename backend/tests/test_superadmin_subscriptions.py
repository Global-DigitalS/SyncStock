"""
Test Suite: SuperAdmin Features and Subscriptions
- SuperAdmin dashboard stats endpoint
- User management with limits
- Subscription plans endpoints
- Role-based access control
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPERADMIN_EMAIL = "test@test.com"
SUPERADMIN_PASSWORD = "test123"
ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"


class TestSuperAdminDashboard:
    """Test SuperAdmin dashboard stats endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as superadmin for all tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login as superadmin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })
        assert login_res.status_code == 200, f"Superadmin login failed: {login_res.text}"
        token = login_res.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.superadmin_user = login_res.json()["user"]
    
    def test_superadmin_stats_returns_200(self):
        """GET /api/dashboard/superadmin-stats should return 200 for superadmin"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/superadmin-stats")
        assert response.status_code == 200
        data = response.json()
        # Validate response structure
        assert "users" in data
        assert "resources" in data
        assert "sync" in data
        assert "woocommerce" in data
        assert "top_users" in data
    
    def test_superadmin_stats_users_structure(self):
        """Verify users section has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/superadmin-stats")
        data = response.json()
        users = data["users"]
        assert "total" in users
        assert "by_role" in users
        assert "recent" in users
        assert isinstance(users["total"], int)
        # Check by_role has expected keys
        by_role = users["by_role"]
        assert "superadmin" in by_role
        assert "admin" in by_role
        assert "user" in by_role
        assert "viewer" in by_role
    
    def test_superadmin_stats_resources_structure(self):
        """Verify resources section has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/superadmin-stats")
        data = response.json()
        resources = data["resources"]
        assert "suppliers" in resources
        assert "products" in resources
        assert "catalogs" in resources
        assert "woocommerce_stores" in resources
    
    def test_superadmin_stats_sync_structure(self):
        """Verify sync section has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/superadmin-stats")
        data = response.json()
        sync = data["sync"]
        assert "this_week" in sync
        assert "errors_this_week" in sync
    
    def test_superadmin_stats_forbidden_for_admin(self):
        """GET /api/dashboard/superadmin-stats should return 403 for non-superadmin"""
        # Login as admin
        admin_session = requests.Session()
        admin_session.headers.update({"Content-Type": "application/json"})
        login_res = admin_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_res.status_code != 200:
            pytest.skip("Admin user not available")
        token = login_res.json()["token"]
        admin_session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = admin_session.get(f"{BASE_URL}/api/dashboard/superadmin-stats")
        assert response.status_code == 403


class TestUserManagement:
    """Test user management endpoints for superadmin"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as superadmin for all tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.superadmin_id = login_res.json()["user"]["id"]
    
    def test_list_users_returns_200(self):
        """GET /api/users should return list of users"""
        response = self.session.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        if len(users) > 0:
            user = users[0]
            assert "id" in user
            assert "email" in user
            assert "name" in user
            assert "role" in user
            assert "password" not in user  # Password should be excluded
    
    def test_get_user_with_usage(self):
        """GET /api/users/{user_id} should return user with resource usage"""
        # Get list of users first
        users_res = self.session.get(f"{BASE_URL}/api/users")
        users = users_res.json()
        if not users:
            pytest.skip("No users available")
        
        # Get first user's details
        user_id = users[0]["id"]
        response = self.session.get(f"{BASE_URL}/api/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert "usage" in data
    
    def test_update_user_limits_superadmin_only(self):
        """PUT /api/users/{user_id}/limits should work for superadmin only"""
        # Get a non-superadmin user
        users_res = self.session.get(f"{BASE_URL}/api/users")
        users = users_res.json()
        target_user = None
        for u in users:
            if u["role"] != "superadmin" and u["id"] != self.superadmin_id:
                target_user = u
                break
        
        if not target_user:
            pytest.skip("No non-superadmin user available for testing")
        
        # Update limits
        new_limits = {
            "max_suppliers": 15,
            "max_catalogs": 8,
            "max_woocommerce_stores": 3
        }
        response = self.session.put(f"{BASE_URL}/api/users/{target_user['id']}/limits", json=new_limits)
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Verify the limits were updated
        verify_res = self.session.get(f"{BASE_URL}/api/users/{target_user['id']}")
        assert verify_res.status_code == 200
        updated_user = verify_res.json()
        assert updated_user["max_suppliers"] == 15
        assert updated_user["max_catalogs"] == 8
        assert updated_user["max_woocommerce_stores"] == 3
    
    def test_update_role_changes_limits(self):
        """PUT /api/users/{user_id}/role should update role and set default limits"""
        # Get a non-superadmin user
        users_res = self.session.get(f"{BASE_URL}/api/users")
        users = users_res.json()
        target_user = None
        for u in users:
            if u["role"] not in ["superadmin"] and u["id"] != self.superadmin_id:
                target_user = u
                break
        
        if not target_user:
            pytest.skip("No suitable user available for role change test")
        
        # Change role to user
        response = self.session.put(f"{BASE_URL}/api/users/{target_user['id']}/role?role=user")
        assert response.status_code == 200


class TestSubscriptionPlans:
    """Test subscription plans endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as superadmin for all tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_get_plans_returns_4_plans(self):
        """GET /api/subscriptions/plans should return 4 default plans"""
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        plans = response.json()
        assert len(plans) == 4
        plan_names = [p["name"] for p in plans]
        assert "Free" in plan_names
        assert "Starter" in plan_names
        assert "Professional" in plan_names
        assert "Enterprise" in plan_names
    
    def test_plans_have_correct_structure(self):
        """Verify each plan has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = response.json()
        for plan in plans:
            assert "id" in plan
            assert "name" in plan
            assert "description" in plan
            assert "max_suppliers" in plan
            assert "max_catalogs" in plan
            assert "max_woocommerce_stores" in plan
            assert "price_monthly" in plan
            assert "price_yearly" in plan
            assert "features" in plan
            assert "is_active" in plan
            assert isinstance(plan["features"], list)
    
    def test_free_plan_prices(self):
        """Verify Free plan has zero prices"""
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = response.json()
        free_plan = next((p for p in plans if p["name"] == "Free"), None)
        assert free_plan is not None
        assert free_plan["price_monthly"] == 0
        assert free_plan["price_yearly"] == 0
    
    def test_professional_plan_limits(self):
        """Verify Professional plan limits"""
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = response.json()
        pro_plan = next((p for p in plans if p["name"] == "Professional"), None)
        assert pro_plan is not None
        assert pro_plan["max_suppliers"] == 50
        assert pro_plan["max_catalogs"] == 20
        assert pro_plan["max_woocommerce_stores"] == 10
        assert pro_plan["price_monthly"] == 49.99
        assert pro_plan["price_yearly"] == 499.99
    
    def test_enterprise_plan_unlimited(self):
        """Verify Enterprise plan has unlimited (999999) limits"""
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = response.json()
        enterprise = next((p for p in plans if p["name"] == "Enterprise"), None)
        assert enterprise is not None
        assert enterprise["max_suppliers"] >= 999999
        assert enterprise["max_catalogs"] >= 999999
        assert enterprise["max_woocommerce_stores"] >= 999999
    
    def test_get_my_subscription(self):
        """GET /api/subscriptions/my should return current subscription"""
        response = self.session.get(f"{BASE_URL}/api/subscriptions/my")
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert "is_free" in data


class TestSubscriptionActions:
    """Test subscription actions (subscribe/cancel)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin for subscription tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Use admin for subscription tests (not superadmin)
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_res.status_code != 200:
            pytest.skip("Admin user not available")
        token = login_res.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_subscribe_to_plan(self):
        """POST /api/subscriptions/subscribe/{plan_id} should create subscription"""
        # Get plans
        plans_res = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = plans_res.json()
        starter_plan = next((p for p in plans if p["name"] == "Starter"), None)
        if not starter_plan:
            pytest.skip("Starter plan not available")
        
        # Subscribe to starter plan
        response = self.session.post(f"{BASE_URL}/api/subscriptions/subscribe/{starter_plan['id']}?billing_cycle=monthly")
        assert response.status_code == 200
        data = response.json()
        assert "subscription" in data
        assert "plan" in data
        assert data["plan"]["name"] == "Starter"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
