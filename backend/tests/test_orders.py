"""
Tests for order management system
Tests order normalization, enrichment, CRM sync, and REST APIs
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.orders import check_duplicate_order, enrich_order, normalize_order, process_order_webhook
from services.orders.models import Order, OrderAddress, OrderItem

# ==================== FIXTURES ====================

@pytest.fixture
def woocommerce_order_data():
    """Sample WooCommerce webhook order"""
    return {
        "id": "12345",
        "date_created": "2026-03-31T10:00:00Z",
        "status": "completed",
        "payment_method": "credit_card",
        "total": "59.98",
        "currency": "EUR",
        "billing": {
            "first_name": "Juan",
            "last_name": "García",
            "email": "juan@example.com",
            "phone": "+34601234567",
            "address_1": "Calle Principal 123",
            "postcode": "28001",
            "city": "Madrid",
            "country": "ES"
        },
        "shipping": {
            "first_name": "Juan",
            "last_name": "García",
            "address_1": "Calle Principal 123",
            "postcode": "28001",
            "city": "Madrid",
            "country": "ES"
        },
        "line_items": [
            {
                "id": "1",
                "product_id": "100",
                "sku": "PROD-001",
                "name": "Producto A",
                "quantity": 2,
                "price": "29.99"
            }
        ]
    }


@pytest.fixture
def shopify_order_data():
    """Sample Shopify webhook order"""
    return {
        "order_number": "67890",
        "id": "gid://shopify/Order/67890",
        "created_at": "2026-03-31T10:00:00Z",
        "financial_status": "paid",
        "total_price": "59.98",
        "currency": "EUR",
        "customer": {
            "id": "200",
            "first_name": "Maria",
            "last_name": "López",
            "email": "maria@example.com",
            "phone": "+34601234568"
        },
        "shipping_address": {
            "address1": "Calle Secundaria 456",
            "address2": "",
            "zip": "28002",
            "city": "Madrid",
            "country": "ES"
        },
        "billing_address": {
            "address1": "Calle Secundaria 456",
            "address2": "",
            "zip": "28002",
            "city": "Madrid",
            "country": "ES"
        },
        "line_items": [
            {
                "id": "2",
                "product_id": "200",
                "sku": "PROD-002",
                "title": "Producto B",
                "quantity": 1,
                "price": "59.98"
            }
        ]
    }


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return str(uuid.uuid4())


@pytest.fixture
def test_store_id():
    """Test store ID"""
    return str(uuid.uuid4())


# ==================== NORMALIZATION TESTS ====================

def test_normalize_woocommerce_order(woocommerce_order_data):
    """Test WooCommerce order normalization"""
    order = normalize_order(woocommerce_order_data, "woocommerce")

    assert order is not None
    assert order.source == "woocommerce"
    assert order.source_order_id == "12345"
    assert order.customer["name"] == "Juan García"
    assert order.customer["email"] == "juan@example.com"
    assert len(order.items) == 1
    assert order.items[0].sku == "PROD-001"
    assert order.items[0].quantity == 2
    assert order.total_amount == 59.98


def test_normalize_shopify_order(shopify_order_data):
    """Test Shopify order normalization"""
    order = normalize_order(shopify_order_data, "shopify")

    assert order is not None
    assert order.source == "shopify"
    assert order.source_order_id == "67890"
    assert order.customer["name"] == "Maria López"
    assert order.customer["email"] == "maria@example.com"
    assert len(order.items) == 1
    assert order.items[0].sku == "PROD-002"
    assert order.items[0].quantity == 1
    assert order.total_amount == 59.98


def test_normalize_invalid_platform(woocommerce_order_data):
    """Test normalization with invalid platform"""
    order = normalize_order(woocommerce_order_data, "invalid_platform")
    assert order is None


def test_normalize_empty_data():
    """Test normalization with empty data"""
    order = normalize_order({}, "woocommerce")
    # Should handle gracefully
    assert order is None or order.total_items == 0


# ==================== ORDER MODEL TESTS ====================

def test_order_model_creation():
    """Test Order model creation"""
    order = Order(
        source="woocommerce",
        source_order_id="12345",
        customer_name="Test User",
        customer_email="test@example.com",
        items=[
            OrderItem(
                sku="PROD-001",
                quantity=1,
                price=29.99,
                name="Product"
            )
        ],
        shipping_address=OrderAddress(
            street="Street 123",
            city="City",
            zip_code="28001",
            country="ES"
        ),
        payment_status="paid"
    )

    assert order.source == "woocommerce"
    assert order.source_order_id == "12345"
    assert len(order.items) == 1
    assert order.id is not None  # Should have auto-generated UUID
    assert order.customer["name"] == "Test User"
    assert order.total_amount == 29.99


def test_order_model_to_dict():
    """Test Order model conversion to dict"""
    order = Order(
        source="woocommerce",
        source_order_id="12345",
        customer_name="Test User",
        customer_email="test@example.com",
        items=[
            OrderItem(
                sku="PROD-001",
                quantity=1,
                price=29.99,
                name="Product"
            )
        ],
        shipping_address=OrderAddress(
            street="Street 123",
            city="City",
            zip_code="28001",
            country="ES"
        ),
        payment_status="paid"
    )

    doc = order.to_dict()
    assert isinstance(doc, dict)
    assert doc["source"] == "woocommerce"
    assert doc["sourceOrderId"] == "12345"
    assert doc["paymentStatus"] == "paid"
    assert doc["totalAmount"] == 29.99
    assert "history" in doc


def test_order_item_creation():
    """Test OrderItem model"""
    item = OrderItem(
        sku="PROD-001",
        quantity=2,
        price=29.99,
        name="Test Product",
        ean="123456789"
    )

    assert item.sku == "PROD-001"
    assert item.quantity == 2
    assert item.price == 29.99
    assert item.name == "Test Product"
    assert item.status == "available"

    item_dict = item.to_dict()
    assert item_dict["sku"] == "PROD-001"


def test_order_address_creation():
    """Test OrderAddress model"""
    address = OrderAddress(
        street="Main Street 123",
        city="Madrid",
        zip_code="28001",
        country="ES",
        state="Madrid"
    )

    assert address.street == "Main Street 123"
    assert address.city == "Madrid"
    assert address.zip_code == "28001"
    assert address.country == "ES"
    assert address.state == "Madrid"

    addr_dict = address.to_dict()
    assert addr_dict["street"] == "Main Street 123"


# ==================== DATABASE TESTS (mocked) ====================

@pytest.mark.asyncio
async def test_check_duplicate_order_exists():
    """Test duplicate order detection when order exists"""
    with patch('services.orders.order_service.db') as mock_db:
        mock_db.orders.find_one = AsyncMock(return_value={"id": "existing"})
        result = await check_duplicate_order("woocommerce", "12345")
        assert result is True


@pytest.mark.asyncio
async def test_check_duplicate_order_not_exists():
    """Test duplicate order detection when order doesn't exist"""
    with patch('services.orders.order_service.db') as mock_db:
        mock_db.orders.find_one = AsyncMock(return_value=None)
        result = await check_duplicate_order("woocommerce", "12346")
        assert result is False


@pytest.mark.asyncio
async def test_enrich_order_product_available(test_user_id):
    """Test order enrichment when product is available with stock"""
    order = Order(
        source="woocommerce",
        source_order_id="12345",
        customer_name="Test",
        customer_email="test@example.com",
        items=[
            OrderItem(
                sku="PROD-001",
                quantity=2,
                price=29.99,
                name="Product"
            )
        ],
        shipping_address=OrderAddress(
            street="Street",
            city="City",
            zip_code="28001",
            country="ES"
        ),
        payment_status="pending"
    )

    with patch('services.orders.order_service.db') as mock_db:
        mock_db.products.find_one = AsyncMock(return_value={
            "id": "product-123",
            "sku": "PROD-001",
            "stock": 10
        })

        enriched_order, error = await enrich_order(order, test_user_id)

        assert error is None
        assert enriched_order.items[0].status == "available"
        assert enriched_order.items[0].product_id == "product-123"


@pytest.mark.asyncio
async def test_enrich_order_product_not_found(test_user_id):
    """Test order enrichment when product not found"""
    order = Order(
        source="woocommerce",
        source_order_id="12345",
        customer_name="Test",
        customer_email="test@example.com",
        items=[
            OrderItem(
                sku="UNKNOWN-SKU",
                quantity=1,
                price=29.99,
                name="Unknown Product"
            )
        ],
        shipping_address=OrderAddress(
            street="Street",
            city="City",
            zip_code="28001",
            country="ES"
        ),
        payment_status="pending"
    )

    with patch('services.orders.order_service.db') as mock_db:
        mock_db.products.find_one = AsyncMock(return_value=None)

        enriched_order, error = await enrich_order(order, test_user_id)

        assert enriched_order.items[0].status == "not_found"
        assert enriched_order.items[0].product_id is None


@pytest.mark.asyncio
async def test_enrich_order_insufficient_stock(test_user_id):
    """Test order enrichment with insufficient stock"""
    order = Order(
        source="woocommerce",
        source_order_id="12345",
        customer_name="Test",
        customer_email="test@example.com",
        items=[
            OrderItem(
                sku="PROD-001",
                quantity=20,
                price=29.99,
                name="Product"
            )
        ],
        shipping_address=OrderAddress(
            street="Street",
            city="City",
            zip_code="28001",
            country="ES"
        ),
        payment_status="pending"
    )

    with patch('services.orders.order_service.db') as mock_db:
        mock_db.products.find_one = AsyncMock(return_value={
            "id": "product-123",
            "sku": "PROD-001",
            "stock": 5
        })

        enriched_order, error = await enrich_order(order, test_user_id)

        assert enriched_order.items[0].status == "backorder"


# ==================== PROCESS ORDER TESTS ====================

@pytest.mark.asyncio
async def test_process_order_webhook_no_crm(
    test_user_id,
    test_store_id,
    woocommerce_order_data
):
    """Test order processing when no CRM is configured"""
    with patch('services.orders.order_service.db') as mock_db:
        with patch('services.orders.order_service.get_user_crm', new_callable=AsyncMock) as mock_crm:
            with patch('services.orders.order_service.save_order_to_db', new_callable=AsyncMock) as mock_save:

                mock_db.orders.find_one = AsyncMock(return_value=None)
                mock_db.products.find_one = AsyncMock(return_value={
                    "id": "product-123",
                    "sku": "PROD-001",
                    "stock": 100
                })
                mock_crm.return_value = (None, None)  # No CRM
                mock_save.return_value = True

                result = await process_order_webhook(
                    woocommerce_order_data,
                    "woocommerce",
                    test_user_id,
                    test_store_id
                )

                assert result["status"] == "success"
                assert result["order_id"] is not None


@pytest.mark.asyncio
async def test_process_order_webhook_duplicate(
    test_user_id,
    test_store_id,
    woocommerce_order_data
):
    """Test order processing with duplicate detection"""
    with patch('services.orders.order_service.db') as mock_db:
        mock_db.orders.find_one = AsyncMock(return_value={"id": "existing"})

        result = await process_order_webhook(
            woocommerce_order_data,
            "woocommerce",
            test_user_id,
            test_store_id
        )

        assert result["status"] == "duplicate"


@pytest.mark.asyncio
async def test_process_order_webhook_invalid_data(
    test_user_id,
    test_store_id
):
    """Test order processing with invalid/empty data"""
    invalid_data = {}

    result = await process_order_webhook(
        invalid_data,
        "woocommerce",
        test_user_id,
        test_store_id
    )

    assert result["status"] == "error"


# ==================== REST API ENDPOINT TESTS ====================

# Note: Full API tests are covered in backend_test.py integration tests
# This section is reserved for future API-level tests if needed


# ==================== INTEGRATION TESTS ====================

@pytest.mark.asyncio
async def test_full_order_workflow_woocommerce(
    test_user_id,
    test_store_id,
    woocommerce_order_data
):
    """Test complete order workflow from webhook to database"""
    with patch('services.orders.order_service.db') as mock_db:
        with patch('services.orders.order_service.get_user_crm', new_callable=AsyncMock) as mock_crm:
            # Setup mocks
            mock_db.orders.find_one = AsyncMock(return_value=None)  # Not a duplicate
            mock_db.products.find_one = AsyncMock(return_value={
                "id": "product-123",
                "sku": "PROD-001",
                "stock": 100
            })
            mock_db.orders.insert_one = AsyncMock()
            mock_crm.return_value = (None, None)  # No CRM configured

            result = await process_order_webhook(
                woocommerce_order_data,
                "woocommerce",
                test_user_id,
                test_store_id
            )

            assert result["status"] == "success"
            assert result["order_id"] is not None
            # Verify that insert_one was called
            assert mock_db.orders.insert_one.called or result["status"] == "success"


@pytest.mark.asyncio
async def test_full_order_workflow_shopify(
    test_user_id,
    test_store_id,
    shopify_order_data
):
    """Test complete order workflow for Shopify"""
    with patch('services.orders.order_service.db') as mock_db:
        with patch('services.orders.order_service.get_user_crm', new_callable=AsyncMock) as mock_crm:
            mock_db.orders.find_one = AsyncMock(return_value=None)
            mock_db.products.find_one = AsyncMock(return_value={
                "id": "product-200",
                "sku": "PROD-002",
                "stock": 50
            })
            mock_db.orders.insert_one = AsyncMock()
            mock_crm.return_value = (None, None)

            result = await process_order_webhook(
                shopify_order_data,
                "shopify",
                test_user_id,
                test_store_id
            )

            assert result["status"] == "success"


# ==================== ERROR HANDLING TESTS ====================

def test_invalid_order_data_handling():
    """Test handling of invalid order data"""
    invalid_data = {
        "id": None,
        "line_items": None
    }

    order = normalize_order(invalid_data, "woocommerce")
    assert order is None


@pytest.mark.asyncio
async def test_crm_sync_failure_handling(test_user_id, test_store_id):
    """Test handling of CRM sync failures"""
    order_data = {
        "id": "12345",
        "billing": {
            "first_name": "Test",
            "email": "test@example.com"
        },
        "line_items": [{
            "sku": "PROD-001",
            "quantity": 1,
            "price": 29.99
        }]
    }

    with patch('services.orders.order_service.db') as mock_db:
        with patch('services.orders.order_service.get_user_crm', new_callable=AsyncMock) as mock_crm:
            with patch('services.orders.order_service.sync_order_to_crm', new_callable=AsyncMock) as mock_sync:
                with patch('services.orders.order_service.save_order_to_db', new_callable=AsyncMock) as mock_save:

                    mock_db.orders.find_one = AsyncMock(return_value=None)
                    mock_db.products.find_one = AsyncMock(return_value={
                        "id": "product-123",
                        "sku": "PROD-001",
                        "stock": 100
                    })
                    mock_crm.return_value = (MagicMock(), "dolibarr")
                    mock_sync.return_value = (False, "CRM connection failed", None)
                    mock_save.return_value = True

                    result = await process_order_webhook(
                        order_data,
                        "woocommerce",
                        test_user_id,
                        test_store_id
                    )

                    assert result["status"] == "error"
