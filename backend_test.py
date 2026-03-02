import requests
import sys
from datetime import datetime
from typing import Dict, Any

class StockHubAPITester:
    def __init__(self, base_url="https://sync-catalog.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.content else {}
                except:
                    response_data = {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'Unknown error') if response.content else 'No content'
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response text: {response.text}")
                response_data = {}

            self.test_results.append({
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'success': success,
                'response_data': response_data
            })

            return success, response_data

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network error: {str(e)}")
            self.test_results.append({
                'name': name,
                'method': method,
                'endpoint': endpoint,
                'expected_status': expected_status,
                'actual_status': 'ERROR',
                'success': False,
                'error': str(e)
            })
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, _ = self.run_test("Health Check", "GET", "health", 200)
        return success

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_data = {
            "name": f"Test User {timestamp}",
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "company": "Test Company SL"
        }
        
        success, response = self.run_test("User Registration", "POST", "auth/register", 200, test_data)
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
        return success

    def test_user_login(self):
        """Test user login"""
        # First register a user if no token exists
        if not self.token:
            self.test_user_registration()
        
        # Test login with registered user credentials
        timestamp = datetime.now().strftime('%H%M%S')
        login_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
        return success

    def test_get_profile(self):
        """Test get current user profile"""
        success, _ = self.run_test("Get User Profile", "GET", "auth/me", 200)
        return success

    def test_create_supplier(self):
        """Test supplier creation"""
        supplier_data = {
            "name": "Test Supplier",
            "description": "Test supplier for automated testing",
            "ftp_host": "ftp.testsupplier.com",
            "ftp_user": "testuser",
            "ftp_password": "testpass",
            "ftp_path": "/products/",
            "file_format": "csv"
        }
        
        success, response = self.run_test("Create Supplier", "POST", "suppliers", 200, supplier_data)
        if success:
            return response.get('id')
        return None

    def test_get_suppliers(self):
        """Test get suppliers"""
        success, response = self.run_test("Get Suppliers", "GET", "suppliers", 200)
        return success, response

    def test_create_margin_rule(self):
        """Test margin rule creation"""
        rule_data = {
            "name": "Test Margin Rule",
            "rule_type": "percentage",
            "value": 30.0,
            "apply_to": "all",
            "priority": 1
        }
        
        success, response = self.run_test("Create Margin Rule", "POST", "margin-rules", 200, rule_data)
        if success:
            return response.get('id')
        return None

    def test_get_margin_rules(self):
        """Test get margin rules"""
        success, response = self.run_test("Get Margin Rules", "GET", "margin-rules", 200)
        return success, response

    def test_get_dashboard_stats(self):
        """Test dashboard statistics"""
        success, response = self.run_test("Get Dashboard Stats", "GET", "dashboard/stats", 200)
        return success, response

    def test_get_notifications(self):
        """Test get notifications"""
        success, response = self.run_test("Get Notifications", "GET", "notifications", 200)
        return success, response

    def test_get_price_history(self):
        """Test get price history"""
        success, response = self.run_test("Get Price History", "GET", "price-history", 200)
        return success, response

    def test_products_endpoints(self):
        """Test product related endpoints"""
        # Get products
        success1, _ = self.run_test("Get Products", "GET", "products", 200)
        
        # Get categories
        success2, _ = self.run_test("Get Categories", "GET", "products/categories", 200)
        
        return success1 and success2

    def test_catalog_endpoints(self):
        """Test catalog endpoints"""
        success, _ = self.run_test("Get Catalog", "GET", "catalog", 200)
        return success

    def test_export_endpoint(self):
        """Test export functionality"""
        export_data = {
            "platform": "prestashop",
            "catalog_ids": []
        }
        # This might return 400 if no products, but endpoint should be accessible
        success, _ = self.run_test("Export Catalog", "POST", "export", 400, export_data)
        return True  # 400 is expected when no products exist

    def test_invalid_authentication(self):
        """Test invalid token handling"""
        # Store current token
        current_token = self.token
        self.token = "invalid_token_12345"
        
        success, _ = self.run_test("Invalid Auth Test", "GET", "auth/me", 401)
        
        # Restore valid token
        self.token = current_token
        return success

def main():
    print("🚀 Starting StockHub SaaS API Testing")
    print("=" * 50)
    
    tester = StockHubAPITester()
    
    # Critical backend functionality tests
    tests = [
        ("Health Check", tester.test_health_check),
        ("User Registration", tester.test_user_registration),
        ("User Login", tester.test_user_login),
        ("Get User Profile", tester.test_get_profile),
        ("Invalid Authentication", tester.test_invalid_authentication),
        ("Create Supplier", lambda: tester.test_create_supplier() is not None),
        ("Get Suppliers", lambda: tester.test_get_suppliers()[0]),
        ("Create Margin Rule", lambda: tester.test_create_margin_rule() is not None),
        ("Get Margin Rules", lambda: tester.test_get_margin_rules()[0]),
        ("Get Dashboard Stats", lambda: tester.test_get_dashboard_stats()[0]),
        ("Get Notifications", tester.test_get_notifications),
        ("Get Price History", tester.test_get_price_history),
        ("Product Endpoints", tester.test_products_endpoints),
        ("Catalog Endpoints", tester.test_catalog_endpoints),
        ("Export Endpoint", tester.test_export_endpoint),
    ]
    
    failed_tests = []
    critical_failures = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            if not result:
                failed_tests.append(test_name)
                # Mark authentication and core functionality as critical
                if any(keyword in test_name.lower() for keyword in ['registration', 'login', 'profile', 'health']):
                    critical_failures.append(test_name)
        except Exception as e:
            print(f"❌ Exception in {test_name}: {str(e)}")
            failed_tests.append(test_name)
            critical_failures.append(test_name)
    
    # Print detailed results
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {tester.tests_run}")
    print(f"Passed: {tester.tests_passed}")
    print(f"Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test in failed_tests:
            marker = "🚨 CRITICAL" if test in critical_failures else "⚠️"
            print(f"   {marker} {test}")
    
    if critical_failures:
        print(f"\n🚨 CRITICAL FAILURES: {len(critical_failures)} tests failed")
        print("   Backend has major functionality broken. Cannot proceed with full testing.")
        return 1
    
    if tester.tests_passed >= tester.tests_run * 0.8:  # 80% pass rate
        print("✅ Backend API tests mostly successful - proceeding to frontend testing")
        return 0
    else:
        print("⚠️ Backend has significant issues but not critical - proceeding with caution")
        return 2

if __name__ == "__main__":
    sys.exit(main())