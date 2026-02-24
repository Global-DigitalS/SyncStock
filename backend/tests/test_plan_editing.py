"""
Test Suite: SuperAdmin Plan Editing Feature
Tests for editing subscription plans - PUT /api/subscriptions/plans/{plan_id}
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


class TestSuperAdminPlanEditing:
    """Test SuperAdmin subscription plan editing functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def login(self, email, password):
        """Helper to login and get token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return response.json()
        return None
    
    def test_get_plans_returns_list(self):
        """Test GET /api/subscriptions/plans returns list of plans"""
        login_result = self.login(SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD)
        assert login_result is not None, "SuperAdmin login failed"
        
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200, f"Failed to get plans: {response.text}"
        
        plans = response.json()
        assert isinstance(plans, list), "Plans should be a list"
        assert len(plans) >= 4, f"Expected at least 4 plans, got {len(plans)}"
        
        # Verify plan structure
        for plan in plans:
            assert "id" in plan, "Plan should have id"
            assert "name" in plan, "Plan should have name"
            assert "price_monthly" in plan, "Plan should have price_monthly"
            assert "price_yearly" in plan, "Plan should have price_yearly"
            assert "max_suppliers" in plan, "Plan should have max_suppliers"
            assert "max_catalogs" in plan, "Plan should have max_catalogs"
            assert "max_woocommerce_stores" in plan, "Plan should have max_woocommerce_stores"
        
        print(f"✓ GET /api/subscriptions/plans returned {len(plans)} plans with correct structure")
    
    def test_update_plan_as_superadmin(self):
        """Test PUT /api/subscriptions/plans/{plan_id} as SuperAdmin"""
        login_result = self.login(SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD)
        assert login_result is not None, "SuperAdmin login failed"
        
        # Get existing plans
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        plans = response.json()
        assert len(plans) > 0, "No plans found"
        
        # Pick the Starter plan or first plan
        test_plan = next((p for p in plans if p["name"] == "Starter"), plans[0])
        plan_id = test_plan["id"]
        original_price = test_plan["price_monthly"]
        
        # Update the plan
        update_data = {
            "name": test_plan["name"],
            "description": "Test updated description",
            "price_monthly": original_price + 5.0,
            "price_yearly": test_plan["price_yearly"] + 50.0,
            "max_suppliers": test_plan["max_suppliers"] + 5,
            "max_catalogs": test_plan["max_catalogs"] + 2,
            "max_woocommerce_stores": test_plan["max_woocommerce_stores"] + 1,
            "features": ["Updated feature 1", "Updated feature 2", "Updated feature 3"]
        }
        
        response = self.session.put(f"{BASE_URL}/api/subscriptions/plans/{plan_id}", json=update_data)
        assert response.status_code == 200, f"Failed to update plan: {response.text}"
        
        updated_plan = response.json()
        assert updated_plan["description"] == "Test updated description"
        assert updated_plan["price_monthly"] == original_price + 5.0
        assert "Updated feature 1" in updated_plan["features"]
        
        # Verify persistence - GET the plan again
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        plans = response.json()
        verified_plan = next((p for p in plans if p["id"] == plan_id), None)
        assert verified_plan is not None, "Plan not found after update"
        assert verified_plan["description"] == "Test updated description"
        
        # Revert changes for other tests
        revert_data = {
            "description": test_plan.get("description", "Para pequeños negocios"),
            "price_monthly": original_price,
            "price_yearly": test_plan["price_yearly"],
            "max_suppliers": test_plan["max_suppliers"],
            "max_catalogs": test_plan["max_catalogs"],
            "max_woocommerce_stores": test_plan["max_woocommerce_stores"],
            "features": test_plan.get("features", [])
        }
        self.session.put(f"{BASE_URL}/api/subscriptions/plans/{plan_id}", json=revert_data)
        
        print(f"✓ PUT /api/subscriptions/plans/{plan_id} successfully updated plan as SuperAdmin")
    
    def test_update_plan_rejected_for_non_superadmin(self):
        """Test PUT /api/subscriptions/plans/{plan_id} returns 403 for non-SuperAdmin"""
        # First get a plan ID as superadmin
        superadmin_login = self.login(SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD)
        assert superadmin_login is not None, "SuperAdmin login failed"
        
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        plans = response.json()
        plan_id = plans[0]["id"]
        
        # Now login as admin (non-superadmin)
        admin_login = self.login(ADMIN_EMAIL, ADMIN_PASSWORD)
        assert admin_login is not None, "Admin login failed"
        
        # Try to update plan as admin
        update_data = {"name": "Hacked Plan", "price_monthly": 0}
        response = self.session.put(f"{BASE_URL}/api/subscriptions/plans/{plan_id}", json=update_data)
        
        assert response.status_code == 403, f"Expected 403 for non-superadmin, got {response.status_code}"
        print(f"✓ PUT /api/subscriptions/plans/{plan_id} correctly returns 403 for non-superadmin")
    
    def test_update_nonexistent_plan_returns_404(self):
        """Test PUT /api/subscriptions/plans/{invalid_id} returns 404"""
        login_result = self.login(SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD)
        assert login_result is not None, "SuperAdmin login failed"
        
        fake_plan_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"name": "Test", "price_monthly": 10}
        response = self.session.put(f"{BASE_URL}/api/subscriptions/plans/{fake_plan_id}", json=update_data)
        
        assert response.status_code == 404, f"Expected 404 for nonexistent plan, got {response.status_code}"
        print(f"✓ PUT /api/subscriptions/plans/{fake_plan_id} correctly returns 404")
    
    def test_update_plan_partial_fields(self):
        """Test PUT /api/subscriptions/plans/{plan_id} with partial fields"""
        login_result = self.login(SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD)
        assert login_result is not None, "SuperAdmin login failed"
        
        # Get existing plans
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        plans = response.json()
        test_plan = next((p for p in plans if p["name"] == "Professional"), plans[0])
        plan_id = test_plan["id"]
        original_description = test_plan.get("description", "")
        
        # Update only description
        update_data = {"description": "Partially updated description"}
        response = self.session.put(f"{BASE_URL}/api/subscriptions/plans/{plan_id}", json=update_data)
        assert response.status_code == 200, f"Failed partial update: {response.text}"
        
        updated_plan = response.json()
        assert updated_plan["description"] == "Partially updated description"
        # Other fields should remain unchanged
        assert updated_plan["price_monthly"] == test_plan["price_monthly"]
        
        # Revert
        self.session.put(f"{BASE_URL}/api/subscriptions/plans/{plan_id}", json={"description": original_description})
        
        print(f"✓ PUT /api/subscriptions/plans/{plan_id} supports partial field updates")
    
    def test_superadmin_user_has_correct_role(self):
        """Verify test@test.com has superadmin role"""
        login_result = self.login(SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD)
        assert login_result is not None, "SuperAdmin login failed"
        
        user = login_result.get("user", {})
        assert user.get("role") == "superadmin", f"Expected superadmin role, got {user.get('role')}"
        print(f"✓ User {SUPERADMIN_EMAIL} has correct superadmin role")
    
    def test_admin_user_has_correct_role(self):
        """Verify admin@test.com has admin role (not superadmin)"""
        login_result = self.login(ADMIN_EMAIL, ADMIN_PASSWORD)
        assert login_result is not None, "Admin login failed"
        
        user = login_result.get("user", {})
        assert user.get("role") == "admin", f"Expected admin role, got {user.get('role')}"
        print(f"✓ User {ADMIN_EMAIL} has correct admin role")


class TestSubscriptionPlansAPIValidation:
    """Additional API validation tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def login_superadmin(self):
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return True
        return False
    
    def test_all_plan_names_present(self):
        """Verify all expected plans exist: Free, Starter, Professional, Enterprise"""
        assert self.login_superadmin(), "Login failed"
        
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        plans = response.json()
        
        plan_names = [p["name"] for p in plans]
        expected_names = ["Free", "Starter", "Professional", "Enterprise"]
        
        for name in expected_names:
            assert name in plan_names, f"Missing expected plan: {name}"
        
        print(f"✓ All expected plans present: {expected_names}")
    
    def test_free_plan_has_zero_prices(self):
        """Verify Free plan has zero prices"""
        assert self.login_superadmin(), "Login failed"
        
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = response.json()
        free_plan = next((p for p in plans if p["name"] == "Free"), None)
        
        assert free_plan is not None, "Free plan not found"
        assert free_plan["price_monthly"] == 0, f"Free plan monthly price should be 0, got {free_plan['price_monthly']}"
        assert free_plan["price_yearly"] == 0, f"Free plan yearly price should be 0, got {free_plan['price_yearly']}"
        
        print("✓ Free plan has zero prices")
    
    def test_enterprise_plan_has_unlimited_limits(self):
        """Verify Enterprise plan has 'unlimited' limits (999999)"""
        assert self.login_superadmin(), "Login failed"
        
        response = self.session.get(f"{BASE_URL}/api/subscriptions/plans")
        plans = response.json()
        enterprise_plan = next((p for p in plans if p["name"] == "Enterprise"), None)
        
        assert enterprise_plan is not None, "Enterprise plan not found"
        assert enterprise_plan["max_suppliers"] == 999999, "Enterprise max_suppliers should be 999999"
        assert enterprise_plan["max_catalogs"] == 999999, "Enterprise max_catalogs should be 999999"
        assert enterprise_plan["max_woocommerce_stores"] == 999999, "Enterprise max_woocommerce_stores should be 999999"
        
        print("✓ Enterprise plan has unlimited (999999) limits")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
