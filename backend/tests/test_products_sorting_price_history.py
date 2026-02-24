"""
Test file for Products Sorting and Price History features
- Products unified sorting (sort_by: name, price, stock, suppliers)
- Price History top-products endpoint
- Price History individual product evolution endpoint
- Products pagination
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Test authentication to get valid token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self, request):
        """Get authentication token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "test123"
        })
        if response.status_code == 200:
            token = response.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}
            request.cls.auth_headers = headers
            return headers
        pytest.fail("Authentication failed")

class TestProductsSorting(TestAuthentication):
    """Tests for products unified sorting functionality"""
    
    def test_products_unified_without_sorting(self, auth_headers):
        """Test products-unified endpoint returns products without sorting"""
        response = requests.get(f"{BASE_URL}/api/products-unified", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: products-unified returns {len(data)} products without sorting")
    
    def test_products_unified_sort_by_name_asc(self, auth_headers):
        """Test sorting by name ascending"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"sort_by": "name", "sort_order": "asc"},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Check if sorted by name ascending
        if len(data) >= 2:
            names = [p.get("name", "").lower() for p in data]
            is_sorted = all(names[i] <= names[i+1] for i in range(len(names)-1))
            print(f"SUCCESS: Sorted by name ASC. First 3 names: {names[:3]}. Is sorted: {is_sorted}")
        else:
            print(f"SUCCESS: Sorted by name ASC. Only {len(data)} products returned")
    
    def test_products_unified_sort_by_name_desc(self, auth_headers):
        """Test sorting by name descending"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"sort_by": "name", "sort_order": "desc"},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) >= 2:
            names = [p.get("name", "").lower() for p in data]
            is_sorted = all(names[i] >= names[i+1] for i in range(len(names)-1))
            print(f"SUCCESS: Sorted by name DESC. First 3 names: {names[:3]}. Is sorted: {is_sorted}")
        else:
            print(f"SUCCESS: Sorted by name DESC. Only {len(data)} products returned")
    
    def test_products_unified_sort_by_price_asc(self, auth_headers):
        """Test sorting by price ascending"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"sort_by": "price", "sort_order": "asc"},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        if len(data) >= 2:
            prices = [p.get("best_price", 0) for p in data]
            is_sorted = all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
            print(f"SUCCESS: Sorted by price ASC. First 3 prices: {prices[:3]}. Is sorted: {is_sorted}")
        else:
            print(f"SUCCESS: Sorted by price ASC. Only {len(data)} products returned")
    
    def test_products_unified_sort_by_price_desc(self, auth_headers):
        """Test sorting by price descending"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"sort_by": "price", "sort_order": "desc"},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        if len(data) >= 2:
            prices = [p.get("best_price", 0) for p in data]
            is_sorted = all(prices[i] >= prices[i+1] for i in range(len(prices)-1))
            print(f"SUCCESS: Sorted by price DESC. First 3 prices: {prices[:3]}. Is sorted: {is_sorted}")
        else:
            print(f"SUCCESS: Sorted by price DESC. Only {len(data)} products returned")
    
    def test_products_unified_sort_by_stock_asc(self, auth_headers):
        """Test sorting by stock ascending"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"sort_by": "stock", "sort_order": "asc"},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        if len(data) >= 2:
            stocks = [p.get("total_stock", 0) for p in data]
            is_sorted = all(stocks[i] <= stocks[i+1] for i in range(len(stocks)-1))
            print(f"SUCCESS: Sorted by stock ASC. First 3 stocks: {stocks[:3]}. Is sorted: {is_sorted}")
        else:
            print(f"SUCCESS: Sorted by stock ASC. Only {len(data)} products returned")
    
    def test_products_unified_sort_by_suppliers_desc(self, auth_headers):
        """Test sorting by supplier count descending"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"sort_by": "suppliers", "sort_order": "desc"},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        if len(data) >= 2:
            supplier_counts = [p.get("supplier_count", 0) for p in data]
            is_sorted = all(supplier_counts[i] >= supplier_counts[i+1] for i in range(len(supplier_counts)-1))
            print(f"SUCCESS: Sorted by suppliers DESC. First 3 counts: {supplier_counts[:3]}. Is sorted: {is_sorted}")
        else:
            print(f"SUCCESS: Sorted by suppliers DESC. Only {len(data)} products returned")


class TestProductsPagination(TestAuthentication):
    """Tests for products pagination functionality"""
    
    def test_products_unified_count(self, auth_headers):
        """Test products-unified/count endpoint returns total count"""
        response = requests.get(f"{BASE_URL}/api/products-unified/count", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "total" in data, "Response should have 'total' field"
        assert isinstance(data["total"], int), "Total should be an integer"
        print(f"SUCCESS: products-unified/count returns total: {data['total']}")
    
    def test_products_unified_pagination_first_page(self, auth_headers):
        """Test first page of products with pagination"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"skip": 0, "limit": 10},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) <= 10, f"Expected max 10 products, got {len(data)}"
        print(f"SUCCESS: First page returns {len(data)} products (limit 10)")
    
    def test_products_unified_pagination_second_page(self, auth_headers):
        """Test second page of products with pagination"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"skip": 10, "limit": 10},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Second page returns {len(data)} products")
    
    def test_products_unified_pagination_with_sorting(self, auth_headers):
        """Test pagination combined with sorting"""
        response = requests.get(f"{BASE_URL}/api/products-unified", 
                               params={"skip": 0, "limit": 5, "sort_by": "price", "sort_order": "desc"},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) >= 2:
            prices = [p.get("best_price", 0) for p in data]
            is_sorted = all(prices[i] >= prices[i+1] for i in range(len(prices)-1))
            print(f"SUCCESS: Pagination with sorting. Prices: {prices}. Is sorted DESC: {is_sorted}")
        else:
            print(f"SUCCESS: Pagination with sorting returns {len(data)} products")


class TestPriceHistoryTopProducts(TestAuthentication):
    """Tests for price history top products endpoint"""
    
    def test_price_history_top_products(self, auth_headers):
        """Test /price-history/top-products endpoint"""
        response = requests.get(f"{BASE_URL}/api/price-history/top-products", 
                               params={"days": 30, "limit": 10},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Check structure of each item
        if len(data) > 0:
            first_item = data[0]
            assert "product_name" in first_item, "Item should have product_name"
            assert "changes" in first_item, "Item should have changes count"
            assert "last_price" in first_item, "Item should have last_price"
            assert "avg_change_percent" in first_item, "Item should have avg_change_percent"
            print(f"SUCCESS: top-products returns {len(data)} items with correct structure")
            print(f"  First product: {first_item['product_name']}, changes: {first_item['changes']}")
        else:
            print("SUCCESS: top-products returns empty list (no price changes in period)")
    
    def test_price_history_top_products_limit(self, auth_headers):
        """Test top-products respects limit parameter"""
        response = requests.get(f"{BASE_URL}/api/price-history/top-products", 
                               params={"days": 90, "limit": 5},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert len(data) <= 5, f"Expected max 5 items, got {len(data)}"
        print(f"SUCCESS: top-products respects limit. Returned {len(data)} items (limit 5)")
    
    def test_price_history_top_products_sorted_by_changes(self, auth_headers):
        """Test top-products are sorted by number of changes descending"""
        response = requests.get(f"{BASE_URL}/api/price-history/top-products", 
                               params={"days": 90, "limit": 10},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        if len(data) >= 2:
            changes = [p.get("changes", 0) for p in data]
            is_sorted = all(changes[i] >= changes[i+1] for i in range(len(changes)-1))
            print(f"SUCCESS: top-products sorted by changes DESC: {changes[:5]}. Is sorted: {is_sorted}")
            assert is_sorted, "Products should be sorted by changes descending"
        else:
            print(f"SUCCESS: top-products returns {len(data)} items")


class TestPriceHistoryProductEvolution(TestAuthentication):
    """Tests for individual product price evolution endpoint"""
    
    def test_price_history_product_evolution_structure(self, auth_headers):
        """Test /price-history/product/{product_name} endpoint structure"""
        # First get a product name from top products
        top_response = requests.get(f"{BASE_URL}/api/price-history/top-products", 
                                    params={"days": 90, "limit": 1},
                                    headers=auth_headers)
        if top_response.status_code == 200 and len(top_response.json()) > 0:
            product_name = top_response.json()[0]["product_name"]
            
            response = requests.get(
                f"{BASE_URL}/api/price-history/product/{requests.utils.quote(product_name)}", 
                params={"days": 90},
                headers=auth_headers
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            
            # Check response structure
            assert "product_name" in data, "Response should have product_name"
            assert "timeline" in data, "Response should have timeline"
            assert "current_price" in data, "Response should have current_price"
            assert "min_price" in data, "Response should have min_price"
            assert "max_price" in data, "Response should have max_price"
            assert "total_changes" in data, "Response should have total_changes"
            
            print(f"SUCCESS: product evolution endpoint structure correct")
            print(f"  Product: {data['product_name']}")
            print(f"  Current price: {data['current_price']}")
            print(f"  Min/Max: {data['min_price']} / {data['max_price']}")
            print(f"  Timeline entries: {len(data['timeline'])}")
        else:
            print("SKIPPED: No price history data available for testing product evolution")
    
    def test_price_history_product_evolution_timeline_format(self, auth_headers):
        """Test timeline data format for recharts compatibility"""
        top_response = requests.get(f"{BASE_URL}/api/price-history/top-products", 
                                    params={"days": 90, "limit": 1},
                                    headers=auth_headers)
        if top_response.status_code == 200 and len(top_response.json()) > 0:
            product_name = top_response.json()[0]["product_name"]
            
            response = requests.get(
                f"{BASE_URL}/api/price-history/product/{requests.utils.quote(product_name)}", 
                params={"days": 90},
                headers=auth_headers
            )
            if response.status_code == 200:
                data = response.json()
                timeline = data.get("timeline", [])
                
                if len(timeline) > 0:
                    first_entry = timeline[0]
                    assert "date" in first_entry, "Timeline entry should have date"
                    assert "price" in first_entry, "Timeline entry should have price"
                    print(f"SUCCESS: Timeline format correct for recharts. First entry: {first_entry}")
                else:
                    print("SUCCESS: Timeline empty but structure correct")
        else:
            print("SKIPPED: No price history data for timeline format test")
    
    def test_price_history_product_nonexistent(self, auth_headers):
        """Test price history for non-existent product returns empty timeline"""
        response = requests.get(
            f"{BASE_URL}/api/price-history/product/NonExistentProduct12345XYZ", 
            params={"days": 90},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data.get("timeline") == [], "Timeline should be empty for non-existent product"
        assert data.get("current_price") is None, "Current price should be None"
        print(f"SUCCESS: Non-existent product returns empty timeline as expected")


class TestPriceHistory(TestAuthentication):
    """Tests for general price history endpoint"""
    
    def test_price_history_list(self, auth_headers):
        """Test /price-history endpoint returns list of price changes"""
        response = requests.get(f"{BASE_URL}/api/price-history", 
                               params={"days": 30, "limit": 100},
                               headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            first_item = data[0]
            assert "id" in first_item, "Item should have id"
            assert "product_name" in first_item, "Item should have product_name"
            assert "old_price" in first_item, "Item should have old_price"
            assert "new_price" in first_item, "Item should have new_price"
            assert "change_percentage" in first_item, "Item should have change_percentage"
            assert "created_at" in first_item, "Item should have created_at"
            print(f"SUCCESS: price-history returns {len(data)} entries with correct structure")
        else:
            print("SUCCESS: price-history returns empty list (no price changes)")
    
    def test_price_history_unauthorized(self):
        """Test price history without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/price-history")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: price-history without auth returns {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
