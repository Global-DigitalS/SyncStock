"""
Test Notifications System
Tests for the improved notifications feature: filters, stats, CRUD operations
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://supplier-portal-30.preview.emergentagent.com').rstrip('/')

# Test credentials from the request
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"

@pytest.fixture(scope="module")
def auth_token():
    """Get auth token using test credentials"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Login failed: {response.text}")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Auth headers for authenticated requests"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDashboardStats:
    """Test dashboard stats endpoint with MongoDB"""
    
    def test_dashboard_stats_returns_expected_fields(self, auth_headers):
        """Test GET /api/dashboard/stats returns all expected fields"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify all expected fields exist
        expected_fields = [
            "total_suppliers", "total_products", "total_catalog_items",
            "total_catalogs", "low_stock_count", "out_of_stock_count",
            "unread_notifications", "recent_price_changes", "woocommerce_stores",
            "woocommerce_connected", "woocommerce_auto_sync", "woocommerce_total_synced"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], int), f"Field {field} should be int, got {type(data[field])}"
        
        print(f"Dashboard stats: suppliers={data['total_suppliers']}, products={data['total_products']}, notifications={data['unread_notifications']}")


class TestNotificationsSystem:
    """Test notifications endpoints: list, filter, mark read, delete"""
    
    def test_get_all_notifications(self, auth_headers):
        """Test GET /api/notifications returns list of notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} notifications")
        
        # Check structure if there are notifications
        if data:
            notif = data[0]
            assert "id" in notif, "Notification should have id"
            assert "type" in notif, "Notification should have type"
            assert "message" in notif, "Notification should have message"
            assert "read" in notif, "Notification should have read status"
            assert "created_at" in notif, "Notification should have created_at"
            print(f"First notification type: {notif['type']}, message: {notif['message'][:50]}...")
    
    def test_get_unread_only_notifications(self, auth_headers):
        """Test GET /api/notifications?unread_only=true filters unread notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications?unread_only=true", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        # All returned notifications should be unread
        for notif in data:
            assert notif["read"] == False, f"Notification {notif['id']} should be unread"
        
        print(f"Found {len(data)} unread notifications")
    
    def test_get_notification_stats(self, auth_headers):
        """Test GET /api/notifications/stats returns statistics by type"""
        response = requests.get(f"{BASE_URL}/api/notifications/stats", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check expected fields
        assert "total" in data, "Stats should have total"
        assert "unread" in data, "Stats should have unread count"
        assert "by_type" in data, "Stats should have by_type breakdown"
        
        # Check by_type structure
        expected_types = ["sync_complete", "sync_error", "stock_out", "stock_low", "price_change", "woocommerce_export"]
        for type_key in expected_types:
            assert type_key in data["by_type"], f"Missing type: {type_key}"
            assert "total" in data["by_type"][type_key], f"Type {type_key} should have total"
            assert "unread" in data["by_type"][type_key], f"Type {type_key} should have unread"
        
        print(f"Stats: total={data['total']}, unread={data['unread']}, by_type={data['by_type']}")


class TestNotificationCRUD:
    """Test notification CRUD operations"""
    
    @pytest.fixture
    def test_notification_id(self, auth_headers):
        """Get an existing notification ID for testing"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        if response.status_code == 200:
            notifications = response.json()
            if notifications:
                return notifications[0]["id"]
        return None
    
    def test_mark_notification_read(self, auth_headers, test_notification_id):
        """Test PUT /api/notifications/{id}/read marks notification as read"""
        if not test_notification_id:
            pytest.skip("No notifications available to test")
        
        response = requests.put(f"{BASE_URL}/api/notifications/{test_notification_id}/read", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"Marked notification {test_notification_id} as read: {data['message']}")
        
        # Verify it's actually marked as read
        get_response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        notifications = get_response.json()
        notif = next((n for n in notifications if n["id"] == test_notification_id), None)
        if notif:
            assert notif["read"] == True, "Notification should be marked as read"
            print("Verified notification is now read")
    
    def test_mark_notification_read_not_found(self, auth_headers):
        """Test PUT /api/notifications/{fake_id}/read returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/notifications/{fake_id}/read", headers=auth_headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Non-existent notification correctly returns 404")
    
    def test_mark_all_notifications_read(self, auth_headers):
        """Test PUT /api/notifications/read-all marks all as read"""
        response = requests.put(f"{BASE_URL}/api/notifications/read-all", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"Marked all notifications as read: {data['message']}")
        
        # Verify all are now read
        get_response = requests.get(f"{BASE_URL}/api/notifications?unread_only=true", headers=auth_headers)
        unread = get_response.json()
        assert len(unread) == 0, f"Expected 0 unread, got {len(unread)}"
        print("Verified all notifications are now read")
    
    def test_delete_notification_not_found(self, auth_headers):
        """Test DELETE /api/notifications/{fake_id} returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/notifications/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Delete non-existent notification correctly returns 404")
    
    def test_delete_read_notifications(self, auth_headers):
        """Test DELETE /api/notifications?read_only=true deletes read notifications"""
        response = requests.delete(f"{BASE_URL}/api/notifications?read_only=true", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"Deleted read notifications: {data['message']}")


class TestNotificationsUnauthorized:
    """Test notifications endpoints require authentication"""
    
    def test_notifications_unauthorized(self):
        """Test GET /api/notifications without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/notifications")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Unauthorized access correctly rejected")
    
    def test_notification_stats_unauthorized(self):
        """Test GET /api/notifications/stats without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/notifications/stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Unauthorized stats access correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
