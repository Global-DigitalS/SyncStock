"""
Database models and schemas for order management
"""
import uuid
from datetime import UTC, datetime


class OrderItem:
    """Represents a line item in an order"""
    def __init__(self, sku: str, quantity: int, price: float, name: str,
                 ean: str | None = None, product_id: str | None = None):
        self.sku = sku
        self.ean = ean
        self.quantity = quantity
        self.price = price
        self.name = name
        self.product_id = product_id
        self.status = "available"  # "available", "backorder", "not_found"

    def to_dict(self):
        return {
            "sku": self.sku,
            "ean": self.ean,
            "quantity": self.quantity,
            "price": self.price,
            "name": self.name,
            "product_id": self.product_id,
            "status": self.status
        }


class OrderAddress:
    """Represents a shipping/billing address"""
    def __init__(self, street: str, city: str, zip_code: str, country: str,
                 state: str | None = None):
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.country = country

    def to_dict(self):
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zipCode": self.zip_code,
            "country": self.country
        }


class Order:
    """Represents a normalized order from any platform"""
    def __init__(self, source: str, source_order_id: str, customer_name: str,
                 customer_email: str, items: list[OrderItem],
                 shipping_address: OrderAddress, payment_status: str = "pending",
                 customer_phone: str | None = None,
                 billing_address: OrderAddress | None = None):
        self.id = str(uuid.uuid4())
        self.source = source  # "woocommerce", "shopify", "prestashop"
        self.source_order_id = source_order_id
        self.customer = {
            "name": customer_name,
            "email": customer_email,
            "phone": customer_phone
        }
        self.items = items
        self.addresses = {
            "shipping": shipping_address.to_dict(),
            "billing": (billing_address or shipping_address).to_dict()
        }
        self.payment_status = payment_status  # "paid", "pending", "failed"
        self.total_amount = sum(item.quantity * item.price for item in items)
        self.total_items = len(items)
        self.status = "pending"  # "pending", "processing", "completed", "backorder", "error"
        self.created_at = datetime.now(UTC).isoformat()
        self.processed_at = None
        self.completed_at = None
        self.error = None
        self.crm_data = {}  # Will store CRM-specific data (CRM ID, etc.)

        # Retry tracking for failed orders
        self.retry_count = 0
        self.max_retries = 5
        self.next_retry_at = None
        self.retry_history = []  # List of previous retry attempts with timestamps and errors

    def to_dict(self):
        """Convert to MongoDB document"""
        return {
            "id": self.id,
            "source": self.source,
            "sourceOrderId": self.source_order_id,
            "customer": self.customer,
            "items": [item.to_dict() for item in self.items],
            "addresses": self.addresses,
            "paymentStatus": self.payment_status,
            "totalAmount": self.total_amount,
            "totalItems": self.total_items,
            "status": self.status,
            "crmData": self.crm_data,
            "createdAt": self.created_at,
            "processedAt": self.processed_at,
            "completedAt": self.completed_at,
            "error": self.error,
            "history": [],
            "retryCount": self.retry_count,
            "maxRetries": self.max_retries,
            "nextRetryAt": self.next_retry_at,
            "retryHistory": self.retry_history
        }


def create_order_indexes():
    """Create MongoDB indexes for orders collection"""
    return [
        {
            "name": "idx_source_sourceOrderId",
            "fields": [("sourceOrderId", 1), ("source", 1)],
            "unique": True
        },
        {
            "name": "idx_createdAt",
            "fields": [("createdAt", -1)]
        },
        {
            "name": "idx_status",
            "fields": [("status", 1)]
        },
        {
            "name": "idx_customer_email",
            "fields": [("customer.email", 1)]
        }
    ]
