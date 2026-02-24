"""
Test suite for Sync History API endpoints (P2 and P3 tasks)
Tests:
- GET /api/sync-history - List synchronization history
- GET /api/sync-history/stats - Get sync statistics for charts
- Filtering by supplier, status, and days range
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSyncHistoryEndpoints:
    """Test sync history list and stats endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get authentication token before each test"""
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
            pytest.skip("Authentication failed - skipping tests")

    def test_sync_history_list_success(self):
        """Test GET /api/sync-history returns list of sync records"""
        response = self.session.get(f"{BASE_URL}/api/sync-history")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            record = data[0]
            # Validate required fields
            assert "id" in record, "Record should have 'id'"
            assert "supplier_id" in record, "Record should have 'supplier_id'"
            assert "supplier_name" in record, "Record should have 'supplier_name'"
            assert "sync_type" in record, "Record should have 'sync_type'"
            assert "status" in record, "Record should have 'status'"
            assert "imported" in record, "Record should have 'imported'"
            assert "updated" in record, "Record should have 'updated'"
            assert "errors" in record, "Record should have 'errors'"
            assert "duration_seconds" in record, "Record should have 'duration_seconds'"
            assert "created_at" in record, "Record should have 'created_at'"
            
            # Validate sync_type values
            assert record["sync_type"] in ["manual", "scheduled"], f"Invalid sync_type: {record['sync_type']}"
            
            # Validate status values
            assert record["status"] in ["success", "error", "partial"], f"Invalid status: {record['status']}"
            
            print(f"✓ sync-history returns {len(data)} records with valid structure")

    def test_sync_history_filter_by_status(self):
        """Test filtering sync history by status"""
        # Test filter by error status
        response = self.session.get(f"{BASE_URL}/api/sync-history?status=error")
        
        assert response.status_code == 200
        data = response.json()
        
        for record in data:
            assert record["status"] == "error", f"Expected status 'error', got '{record['status']}'"
        
        print(f"✓ sync-history filter by status=error returns {len(data)} error records")
        
        # Test filter by success status
        response_success = self.session.get(f"{BASE_URL}/api/sync-history?status=success")
        assert response_success.status_code == 200
        data_success = response_success.json()
        
        for record in data_success:
            assert record["status"] == "success", f"Expected status 'success', got '{record['status']}'"
        
        print(f"✓ sync-history filter by status=success returns {len(data_success)} success records")

    def test_sync_history_filter_by_days(self):
        """Test filtering sync history by days range"""
        # Test 7 days filter
        response_7d = self.session.get(f"{BASE_URL}/api/sync-history?days=7")
        assert response_7d.status_code == 200
        data_7d = response_7d.json()
        
        # Test 30 days filter (should return more or equal records)
        response_30d = self.session.get(f"{BASE_URL}/api/sync-history?days=30")
        assert response_30d.status_code == 200
        data_30d = response_30d.json()
        
        assert len(data_30d) >= len(data_7d), "30-day filter should return >= records than 7-day filter"
        print(f"✓ sync-history days filter: 7d={len(data_7d)}, 30d={len(data_30d)}")

    def test_sync_history_stats_success(self):
        """Test GET /api/sync-history/stats returns valid statistics"""
        response = self.session.get(f"{BASE_URL}/api/sync-history/stats")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Validate required fields for stats
        assert "total" in data, "Stats should have 'total'"
        assert "success" in data, "Stats should have 'success'"
        assert "errors" in data, "Stats should have 'errors'"
        assert "partial" in data, "Stats should have 'partial'"
        assert "total_imported" in data, "Stats should have 'total_imported'"
        assert "total_updated" in data, "Stats should have 'total_updated'"
        assert "total_errors" in data, "Stats should have 'total_errors'"
        assert "avg_duration" in data, "Stats should have 'avg_duration'"
        assert "daily_stats" in data, "Stats should have 'daily_stats'"
        
        # Validate types
        assert isinstance(data["total"], int), "total should be int"
        assert isinstance(data["success"], int), "success should be int"
        assert isinstance(data["errors"], int), "errors should be int"
        assert isinstance(data["partial"], int), "partial should be int"
        assert isinstance(data["total_imported"], int), "total_imported should be int"
        assert isinstance(data["total_updated"], int), "total_updated should be int"
        assert isinstance(data["total_errors"], int), "total_errors should be int"
        assert isinstance(data["avg_duration"], (int, float)), "avg_duration should be numeric"
        assert isinstance(data["daily_stats"], list), "daily_stats should be list"
        
        # Validate total matches sum of statuses
        assert data["total"] == data["success"] + data["errors"] + data["partial"], \
            f"total ({data['total']}) should equal sum of success ({data['success']}) + errors ({data['errors']}) + partial ({data['partial']})"
        
        print(f"✓ sync-history/stats returns valid data: total={data['total']}, success={data['success']}, errors={data['errors']}")

    def test_sync_history_stats_daily_format(self):
        """Test daily_stats in sync-history/stats has correct format for charts"""
        response = self.session.get(f"{BASE_URL}/api/sync-history/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        daily_stats = data.get("daily_stats", [])
        
        if len(daily_stats) > 0:
            day_record = daily_stats[0]
            
            # Validate daily stat structure (used for chart)
            assert "date" in day_record, "daily_stat should have 'date'"
            assert "count" in day_record, "daily_stat should have 'count'"
            assert "success" in day_record, "daily_stat should have 'success'"
            assert "errors" in day_record, "daily_stat should have 'errors'"
            
            # Validate date format (YYYY-MM-DD)
            import re
            date_pattern = r"^\d{4}-\d{2}-\d{2}$"
            assert re.match(date_pattern, day_record["date"]), f"Date format should be YYYY-MM-DD, got {day_record['date']}"
            
            print(f"✓ daily_stats has {len(daily_stats)} days with valid format for chart")
        else:
            print("ℹ No daily_stats available (may be empty data)")

    def test_sync_history_stats_filter_by_days(self):
        """Test stats endpoint respects days filter"""
        response_7d = self.session.get(f"{BASE_URL}/api/sync-history/stats?days=7")
        response_30d = self.session.get(f"{BASE_URL}/api/sync-history/stats?days=30")
        
        assert response_7d.status_code == 200
        assert response_30d.status_code == 200
        
        stats_7d = response_7d.json()
        stats_30d = response_30d.json()
        
        # 30 days should have >= total than 7 days
        assert stats_30d["total"] >= stats_7d["total"], \
            f"30-day stats total ({stats_30d['total']}) should be >= 7-day ({stats_7d['total']})"
        
        print(f"✓ stats days filter works: 7d total={stats_7d['total']}, 30d total={stats_30d['total']}")

    def test_sync_history_unauthorized(self):
        """Test sync-history endpoint requires authentication"""
        # Use session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/sync-history")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ sync-history requires authentication")

    def test_sync_history_stats_unauthorized(self):
        """Test sync-history/stats endpoint requires authentication"""
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/sync-history/stats")
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ sync-history/stats requires authentication")


class TestSyncHistoryRecording:
    """Test that sync operations record history correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get authentication token before each test"""
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
            pytest.skip("Authentication failed - skipping tests")

    def test_sync_record_contains_supplier_info(self):
        """Test that sync history records contain proper supplier information"""
        response = self.session.get(f"{BASE_URL}/api/sync-history")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            # Verify first record has both supplier_id and supplier_name
            record = data[0]
            
            assert record.get("supplier_id"), "Record should have non-empty supplier_id"
            assert record.get("supplier_name"), "Record should have non-empty supplier_name"
            assert isinstance(record.get("imported"), int), "imported should be int"
            assert isinstance(record.get("updated"), int), "updated should be int"
            assert isinstance(record.get("errors"), int), "errors should be int"
            assert isinstance(record.get("duration_seconds"), (int, float)), "duration_seconds should be numeric"
            
            print(f"✓ sync record has supplier info: {record['supplier_name']} ({record['supplier_id'][:8]}...)")
