"""
Test Admin Panel Endpoints for SuperAdmin
Tests: Branding, Plans, Email Templates, Theme Presets
"""
import os

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestAdminAuthentication:
    """Test authentication for admin endpoints"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get superadmin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "superadmin", "User is not superadmin"
        return data["token"]

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    def test_admin_endpoints_require_auth(self):
        """Admin endpoints should return 401 without authentication"""
        endpoints = [
            ("GET", "/api/admin/branding"),
            ("PUT", "/api/admin/branding"),
            ("GET", "/api/admin/theme-presets"),
            ("GET", "/api/admin/plans"),
            ("GET", "/api/admin/email-templates"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.put(f"{BASE_URL}{endpoint}", json={})

            assert response.status_code in [401, 403], f"{method} {endpoint} should require auth, got {response.status_code}"
            print(f"PASS: {method} {endpoint} requires authentication")


class TestBrandingEndpoints:
    """Test branding configuration endpoints"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def test_get_branding(self, auth_headers):
        """GET /api/admin/branding - Should return branding config"""
        response = requests.get(f"{BASE_URL}/api/admin/branding", headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Verify required fields exist
        expected_fields = ["app_name", "primary_color", "secondary_color", "accent_color"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

        print(f"PASS: GET /api/admin/branding - app_name: {data.get('app_name')}")

    def test_update_branding(self, auth_headers):
        """PUT /api/admin/branding - Should update branding config"""
        update_data = {
            "app_name": "TEST_StockHub Updated",
            "app_slogan": "TEST Slogan",
            "footer_text": "TEST Footer 2025"
        }

        response = requests.put(f"{BASE_URL}/api/admin/branding", headers=auth_headers, json=update_data)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        assert data.get("success") == True, "Update should return success: True"
        assert data.get("branding", {}).get("app_name") == "TEST_StockHub Updated", "app_name should be updated"

        print("PASS: PUT /api/admin/branding - Updated successfully")

    def test_update_branding_colors(self, auth_headers):
        """PUT /api/admin/branding - Should update colors"""
        update_data = {
            "primary_color": "#ff6600",
            "secondary_color": "#222222",
            "accent_color": "#00ff00"
        }

        response = requests.put(f"{BASE_URL}/api/admin/branding", headers=auth_headers, json=update_data)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        branding = data.get("branding", {})
        assert branding.get("primary_color") == "#ff6600", "primary_color should be updated"

        print("PASS: PUT /api/admin/branding - Colors updated")

    def test_verify_branding_persistence(self, auth_headers):
        """Verify branding changes persist after GET"""
        # GET to verify persistence
        response = requests.get(f"{BASE_URL}/api/admin/branding", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "TEST" in data.get("app_name", "") or "StockHub" in data.get("app_name", ""), "Branding should persist"

        print(f"PASS: Branding persistence verified - app_name: {data.get('app_name')}")


class TestThemePresets:
    """Test theme preset endpoints"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def test_get_theme_presets(self, auth_headers):
        """GET /api/admin/theme-presets - Should return 7 presets"""
        response = requests.get(f"{BASE_URL}/api/admin/theme-presets", headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        expected_presets = ["default", "ocean", "forest", "sunset", "royal", "slate", "rose"]
        for preset in expected_presets:
            assert preset in data, f"Missing preset: {preset}"
            assert "primary_color" in data[preset], f"Preset {preset} missing primary_color"
            assert "secondary_color" in data[preset], f"Preset {preset} missing secondary_color"

        print(f"PASS: GET /api/admin/theme-presets - {len(data)} presets returned")

    def test_apply_theme_preset(self, auth_headers):
        """POST /api/admin/branding/apply-preset/{preset_key} - Should apply theme"""
        response = requests.post(
            f"{BASE_URL}/api/admin/branding/apply-preset/ocean",
            headers=auth_headers
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        assert data.get("success") == True, "Should return success"
        branding = data.get("branding", {})
        assert branding.get("theme_preset") == "ocean", "theme_preset should be 'ocean'"

        print("PASS: Applied 'ocean' theme preset")

    def test_apply_invalid_preset(self, auth_headers):
        """POST /api/admin/branding/apply-preset/invalid - Should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/admin/branding/apply-preset/invalid_theme",
            headers=auth_headers
        )

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Invalid preset returns 404")


class TestSubscriptionPlans:
    """Test subscription plan CRUD endpoints"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    created_plan_id = None

    def test_get_plans(self, auth_headers):
        """GET /api/admin/plans - Should return list of plans"""
        response = requests.get(f"{BASE_URL}/api/admin/plans", headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert isinstance(data, list), "Should return a list"
        print(f"PASS: GET /api/admin/plans - {len(data)} plans returned")

    def test_create_plan(self, auth_headers):
        """POST /api/admin/plans - Should create new plan"""
        plan_data = {
            "name": "TEST_Plan Premium",
            "description": "Plan de prueba para testing",
            "max_suppliers": 50,
            "max_catalogs": 20,
            "max_products": 10000,
            "max_stores": 5,
            "price_monthly": 29.99,
            "price_yearly": 299.99,
            "features": ["Soporte prioritario", "API Access", "Unlimited exports"],
            "is_default": False,
            "sort_order": 99
        }

        response = requests.post(f"{BASE_URL}/api/admin/plans", headers=auth_headers, json=plan_data)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        assert data.get("success") == True, "Should return success"
        plan = data.get("plan", {})
        assert plan.get("name") == "TEST_Plan Premium", "Name should match"
        assert plan.get("max_suppliers") == 50, "max_suppliers should be 50"
        assert "id" in plan, "Plan should have an id"

        TestSubscriptionPlans.created_plan_id = plan.get("id")
        print(f"PASS: POST /api/admin/plans - Created plan with ID: {plan.get('id')}")

    def test_update_plan(self, auth_headers):
        """PUT /api/admin/plans/{plan_id} - Should update plan"""
        if not TestSubscriptionPlans.created_plan_id:
            pytest.skip("No plan created to update")

        update_data = {
            "name": "TEST_Plan Premium Updated",
            "price_monthly": 39.99,
            "features": ["Updated Feature 1", "Updated Feature 2"]
        }

        response = requests.put(
            f"{BASE_URL}/api/admin/plans/{TestSubscriptionPlans.created_plan_id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data.get("success") == True, "Should return success"
        plan = data.get("plan", {})
        assert "Updated" in plan.get("name", ""), "Name should be updated"
        assert plan.get("price_monthly") == 39.99, "Price should be updated"

        print(f"PASS: PUT /api/admin/plans/{TestSubscriptionPlans.created_plan_id} - Updated")

    def test_update_nonexistent_plan(self, auth_headers):
        """PUT /api/admin/plans/invalid-id - Should return 404"""
        response = requests.put(
            f"{BASE_URL}/api/admin/plans/invalid-plan-id-12345",
            headers=auth_headers,
            json={"name": "Test"}
        )

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Update nonexistent plan returns 404")

    def test_delete_plan(self, auth_headers):
        """DELETE /api/admin/plans/{plan_id} - Should delete plan"""
        if not TestSubscriptionPlans.created_plan_id:
            pytest.skip("No plan created to delete")

        response = requests.delete(
            f"{BASE_URL}/api/admin/plans/{TestSubscriptionPlans.created_plan_id}",
            headers=auth_headers
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        assert data.get("success") == True, "Should return success"

        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/admin/plans", headers=auth_headers)
        plans = get_response.json()
        plan_ids = [p.get("id") for p in plans]
        assert TestSubscriptionPlans.created_plan_id not in plan_ids, "Plan should be deleted"

        print(f"PASS: DELETE /api/admin/plans/{TestSubscriptionPlans.created_plan_id} - Deleted")

    def test_delete_nonexistent_plan(self, auth_headers):
        """DELETE /api/admin/plans/invalid-id - Should return 404"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/plans/invalid-plan-id-12345",
            headers=auth_headers
        )

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Delete nonexistent plan returns 404")


class TestEmailTemplates:
    """Test email template endpoints"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    created_template_id = None

    def test_get_email_templates(self, auth_headers):
        """GET /api/admin/email-templates - Should return templates"""
        response = requests.get(f"{BASE_URL}/api/admin/email-templates", headers=auth_headers)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert isinstance(data, list), "Should return a list"

        # Should have default templates
        template_keys = [t.get("key") for t in data]
        expected_keys = ["welcome", "password_reset", "subscription_change"]
        for key in expected_keys:
            assert key in template_keys, f"Missing default template: {key}"

        print(f"PASS: GET /api/admin/email-templates - {len(data)} templates returned")

    def test_template_has_required_fields(self, auth_headers):
        """Verify templates have all required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/email-templates", headers=auth_headers)
        data = response.json()

        for template in data:
            assert "id" in template, "Template should have id"
            assert "name" in template, "Template should have name"
            assert "key" in template, "Template should have key"
            assert "subject" in template, "Template should have subject"
            assert "html_content" in template, "Template should have html_content"

        print("PASS: All templates have required fields")

    def test_update_email_template(self, auth_headers):
        """PUT /api/admin/email-templates/{id} - Should update template"""
        # Get templates to find welcome template
        response = requests.get(f"{BASE_URL}/api/admin/email-templates", headers=auth_headers)
        templates = response.json()

        welcome_template = next((t for t in templates if t.get("key") == "welcome"), None)
        assert welcome_template, "Welcome template should exist"

        update_data = {
            "subject": "TEST - ¡Bienvenido a {app_name}!"
        }

        update_response = requests.put(
            f"{BASE_URL}/api/admin/email-templates/{welcome_template['id']}",
            headers=auth_headers,
            json=update_data
        )

        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        data = update_response.json()

        assert data.get("success") == True, "Should return success"
        assert "TEST" in data.get("template", {}).get("subject", ""), "Subject should be updated"

        print(f"PASS: PUT /api/admin/email-templates/{welcome_template['id']} - Updated")

    def test_preview_email_template(self, auth_headers):
        """POST /api/admin/email-templates/{id}/preview - Should return preview"""
        # Get templates
        response = requests.get(f"{BASE_URL}/api/admin/email-templates", headers=auth_headers)
        templates = response.json()

        welcome_template = next((t for t in templates if t.get("key") == "welcome"), None)
        assert welcome_template, "Welcome template should exist"

        preview_response = requests.post(
            f"{BASE_URL}/api/admin/email-templates/{welcome_template['id']}/preview",
            headers=auth_headers
        )

        assert preview_response.status_code == 200, f"Expected 200, got {preview_response.status_code}"
        data = preview_response.json()

        assert "subject" in data, "Preview should have subject"
        assert "html" in data, "Preview should have html"

        # Verify variables are replaced
        html = data.get("html", "")
        assert "{name}" not in html or "Usuario de Ejemplo" in html, "Variables should be replaced"

        print(f"PASS: POST /api/admin/email-templates/{welcome_template['id']}/preview - Preview generated")

    def test_create_custom_template(self, auth_headers):
        """POST /api/admin/email-templates - Should create custom template"""
        template_data = {
            "name": "TEST Custom Template",
            "key": "test_custom_template",
            "subject": "Test Subject - {app_name}",
            "html_content": "<html><body><h1>Test {name}</h1></body></html>",
            "variables": ["name", "app_name"],
            "is_active": True
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/email-templates",
            headers=auth_headers,
            json=template_data
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        assert data.get("success") == True, "Should return success"
        template = data.get("template", {})
        assert template.get("key") == "test_custom_template", "Key should match"

        TestEmailTemplates.created_template_id = template.get("id")
        print("PASS: POST /api/admin/email-templates - Created custom template")

    def test_delete_custom_template(self, auth_headers):
        """DELETE /api/admin/email-templates/{id} - Should delete custom template"""
        if not TestEmailTemplates.created_template_id:
            pytest.skip("No custom template created")

        response = requests.delete(
            f"{BASE_URL}/api/admin/email-templates/{TestEmailTemplates.created_template_id}",
            headers=auth_headers
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: DELETE custom template - Deleted")

    def test_cannot_delete_default_templates(self, auth_headers):
        """DELETE default template - Should return 400"""
        response = requests.get(f"{BASE_URL}/api/admin/email-templates", headers=auth_headers)
        templates = response.json()

        welcome_template = next((t for t in templates if t.get("key") == "welcome"), None)
        assert welcome_template, "Welcome template should exist"

        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/email-templates/{welcome_template['id']}",
            headers=auth_headers
        )

        assert delete_response.status_code == 400, f"Expected 400, got {delete_response.status_code}"
        print("PASS: Cannot delete default templates (returns 400)")

    def test_reset_default_templates(self, auth_headers):
        """POST /api/admin/email-templates/reset-defaults - Should reset defaults"""
        response = requests.post(
            f"{BASE_URL}/api/admin/email-templates/reset-defaults",
            headers=auth_headers
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert data.get("success") == True, "Should return success"
        print("PASS: POST /api/admin/email-templates/reset-defaults - Reset successful")


class TestPublicBranding:
    """Test public branding endpoint (no auth required)"""

    def test_get_public_branding(self):
        """GET /api/branding/public - Should work without auth"""
        response = requests.get(f"{BASE_URL}/api/branding/public")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        # Verify public fields
        expected_fields = ["app_name", "app_slogan", "primary_color"]
        for field in expected_fields:
            assert field in data, f"Missing public field: {field}"

        print(f"PASS: GET /api/branding/public - app_name: {data.get('app_name')}")


class TestCleanup:
    """Cleanup test data"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        token = response.json()["token"]
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def test_restore_branding(self, auth_headers):
        """Restore branding to default values"""
        restore_data = {
            "app_name": "StockHub",
            "app_slogan": "Gestión de Catálogos",
            "footer_text": "",
            "theme_preset": "default"
        }

        # Apply default theme
        requests.post(
            f"{BASE_URL}/api/admin/branding/apply-preset/default",
            headers=auth_headers
        )

        response = requests.put(f"{BASE_URL}/api/admin/branding", headers=auth_headers, json=restore_data)
        assert response.status_code == 200

        # Reset email templates
        requests.post(f"{BASE_URL}/api/admin/email-templates/reset-defaults", headers=auth_headers)

        print("PASS: Branding restored to defaults")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
