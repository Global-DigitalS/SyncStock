#!/usr/bin/env python3
"""
Test suite for Odoo 17 CRM integration in SyncStock

This test suite validates the OdooClient class and its integration
with the CRM endpoints for product, supplier, and order management.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.crm_clients import OdooClient


class TestOdooClientBasics:
    """Test OdooClient instantiation and basic methods"""
    
    def test_odoo_client_init(self):
        """Test OdooClient initialization"""
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="test_token_123"
        )
        
        assert client.base_url == "https://odoo.example.com"
        assert client.api_token == "test_token_123"
        assert "Bearer test_token_123" in client.headers["Authorization"]
        client.close()
    
    def test_odoo_client_url_normalization(self):
        """Test that URLs are properly normalized (trailing slash removed)"""
        client = OdooClient(
            api_url="https://odoo.example.com/",
            api_token="token"
        )
        
        assert client.base_url == "https://odoo.example.com"
        client.close()


class TestOdooClientConnection:
    """Test connection testing methods"""
    
    @patch('routes.crm.requests.Session.request')
    def test_test_connection_success(self, mock_request):
        """Test successful connection to Odoo"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"key": "web.base.url"}]
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        result = client.test_connection()
        
        assert result["status"] == "success"
        assert "Conexión exitosa" in result["message"]
        client.close()
    
    @patch('routes.crm.requests.Session.request')
    def test_test_connection_auth_error(self, mock_request):
        """Test connection with invalid token"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="invalid_token"
        )
        
        result = client.test_connection()
        
        assert result["status"] == "error"
        assert "Token inválido" in result["message"]
        client.close()


class TestOdooClientProducts:
    """Test product-related methods"""
    
    @patch('routes.crm.requests.Session.request')
    def test_get_products(self, mock_request):
        """Test getting products from Odoo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "name": "Producto Test",
                "default_code": "TEST-001",
                "list_price": 100.0,
                "qty_available": 10
            }
        ]
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        products = client.get_products(limit=100)
        
        assert len(products) == 1
        assert products[0]["name"] == "Producto Test"
        assert products[0]["default_code"] == "TEST-001"
        client.close()
    
    @patch('routes.crm.requests.Session.request')
    def test_create_product(self, mock_request):
        """Test creating a product in Odoo"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123}
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        result = client.create_product({
            "name": "Nuevo Producto",
            "sku": "NEW-001",
            "ean": "1234567890123",
            "price": 50.0,
            "cost_price": 25.0
        })
        
        assert result["status"] == "success"
        assert result["product_id"] == 123
        client.close()
    
    @patch('routes.crm.requests.Session.request')
    def test_update_product(self, mock_request):
        """Test updating a product in Odoo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        result = client.update_product(123, {
            "name": "Producto Actualizado",
            "price": 75.0
        })
        
        assert result["status"] == "success"
        assert "actualizado" in result["message"].lower()
        client.close()


class TestOdooClientSuppliers:
    """Test supplier-related methods"""
    
    @patch('routes.crm.requests.Session.request')
    def test_get_suppliers(self, mock_request):
        """Test getting suppliers from Odoo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "name": "Proveedor Test",
                "email": "supplier@example.com",
                "phone": "+34 900 123 456"
            }
        ]
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        suppliers = client.get_suppliers(limit=100)
        
        assert len(suppliers) == 1
        assert suppliers[0]["name"] == "Proveedor Test"
        client.close()
    
    @patch('routes.crm.requests.Session.request')
    def test_create_supplier(self, mock_request):
        """Test creating a supplier in Odoo"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 456}
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        result = client.create_supplier({
            "name": "Nuevo Proveedor",
            "email": "new@supplier.com",
            "phone": "+34 900 000 000"
        })
        
        assert result["status"] == "success"
        assert result["supplier_id"] == 456
        client.close()


class TestOdooClientWarehouse:
    """Test warehouse-related methods"""
    
    @patch('routes.crm.requests.Session.request')
    def test_get_warehouses(self, mock_request):
        """Test getting warehouses from Odoo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "name": "Almacén Principal",
                "code": "MAIN"
            }
        ]
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        warehouses = client.get_warehouses()
        
        assert len(warehouses) == 1
        assert warehouses[0]["name"] == "Almacén Principal"
        client.close()


class TestOdooClientOrders:
    """Test order-related methods"""
    
    @patch('routes.crm.requests.Session.request')
    def test_get_orders(self, mock_request):
        """Test getting sales orders from Odoo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "name": "SO001",
                "partner_id": 10,
                "amount_total": 1500.0
            }
        ]
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        orders = client.get_orders(limit=100)
        
        assert len(orders) == 1
        assert orders[0]["name"] == "SO001"
        client.close()
    
    @patch('routes.crm.requests.Session.request')
    def test_get_purchase_orders(self, mock_request):
        """Test getting purchase orders from Odoo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "name": "PO001",
                "partner_id": 5,
                "amount_total": 500.0
            }
        ]
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        purchase_orders = client.get_purchase_orders(limit=100)
        
        assert len(purchase_orders) == 1
        assert purchase_orders[0]["name"] == "PO001"
        client.close()


class TestOdooClientStats:
    """Test statistics methods"""
    
    @patch('routes.crm.requests.Session.request')
    def test_get_stats(self, mock_request):
        """Test getting CRM statistics"""
        # Mock multiple requests for products, suppliers, orders
        mock_response = Mock()
        mock_response.status_code = 200
        
        # Create sequence of responses
        responses = [
            [{"id": 1}, {"id": 2}, {"id": 3}],  # products
            [{"id": 10}],  # suppliers
            [{"id": 100}],  # sales orders
            [{"id": 200}]   # purchase orders
        ]
        
        mock_response.json.side_effect = responses
        mock_request.return_value = mock_response
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        stats = client.get_stats()
        
        assert stats["products"] == 3
        assert stats["suppliers"] == 1
        assert stats["orders"] == 2  # SO + PO
        client.close()


class TestOdooClientErrors:
    """Test error handling"""
    
    @patch('routes.crm.requests.Session.request')
    def test_connection_timeout(self, mock_request):
        """Test handling of connection timeout"""
        import requests
        mock_request.side_effect = requests.exceptions.Timeout()
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        result = client.test_connection()
        
        assert result["status"] == "error"
        assert "Tiempo de espera" in result["message"]
        client.close()
    
    @patch('routes.crm.requests.Session.request')
    def test_connection_refused(self, mock_request):
        """Test handling of connection refused"""
        import requests
        mock_request.side_effect = requests.exceptions.ConnectionError()
        
        client = OdooClient(
            api_url="https://odoo.example.com",
            api_token="token"
        )
        
        result = client.test_connection()
        
        assert result["status"] == "error"
        assert "conectar" in result["message"].lower()
        client.close()


def test_rate_limiting():
    """Test that rate limiting is applied"""
    import time
    
    client = OdooClient(
        api_url="https://odoo.example.com",
        api_token="token"
    )
    
    assert client.min_delay == 0.1  # 100ms
    assert client.last_request_time == 0
    
    client.close()


def test_headers_setup():
    """Test that headers are properly configured"""
    client = OdooClient(
        api_url="https://odoo.example.com",
        api_token="my_token_123"
    )
    
    assert client.headers["Content-Type"] == "application/json"
    assert client.headers["Accept"] == "application/json"
    assert "Bearer my_token_123" in client.headers["Authorization"]
    
    client.close()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
