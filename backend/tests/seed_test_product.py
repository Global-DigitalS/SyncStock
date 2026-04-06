"""
Seed data for product edit testing
Creates a test supplier and product directly in MongoDB
"""

import asyncio
import uuid
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorClient


async def seed_test_data():
    # Connect to MongoDB
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]

    # Create test user if not exists
    test_user = await db.users.find_one({"email": "test@test.com"})
    if not test_user:
        print("Creating test user...")
        test_user_id = str(uuid.uuid4())
        await db.users.insert_one({
            "id": test_user_id,
            "email": "test@test.com",
            "name": "Test User",
            "password_hash": "hashed",  # This would be a real hash
            "role": "superadmin",
            "max_suppliers": 10,
            "max_catalogs": 5,
            "max_woocommerce_stores": 2,
            "created_at": datetime.now(UTC).isoformat()
        })
    else:
        test_user_id = test_user["id"]

    print(f"Using user_id: {test_user_id}")

    # Create test supplier
    supplier_id = f"TEST_supplier_{uuid.uuid4().hex[:8]}"
    supplier_exists = await db.suppliers.find_one({"id": supplier_id})

    if not supplier_exists:
        print("Creating test supplier...")
        await db.suppliers.insert_one({
            "id": supplier_id,
            "user_id": test_user_id,
            "name": "TEST Supplier for Product Edit",
            "description": "Test supplier for testing product editing features",
            "connection_type": "url",
            "product_count": 1,
            "last_sync": datetime.now(UTC).isoformat(),
            "created_at": datetime.now(UTC).isoformat()
        })
        print(f"Created supplier: {supplier_id}")

    # Create test product
    product_id = f"TEST_product_{uuid.uuid4().hex[:8]}"
    now = datetime.now(UTC).isoformat()

    print("Creating test product...")
    await db.products.insert_one({
        "id": product_id,
        "user_id": test_user_id,
        "supplier_id": supplier_id,
        "supplier_name": "TEST Supplier for Product Edit",
        "sku": f"TEST-SKU-{uuid.uuid4().hex[:6]}",
        "name": "TEST Product for Editing",
        "description": "Original description for testing",
        "short_description": None,
        "long_description": None,
        "price": 99.99,
        "stock": 100,
        "category": "Test Category",
        "brand": "Test Brand",
        "ean": "1234567890123",
        "weight": 1.5,
        "image_url": None,
        "gallery_images": [],
        "is_selected": True,
        "activado": True,
        "envio_gratis": False,
        "created_at": now,
        "updated_at": now
    })

    print(f"Created product: {product_id}")

    # Verify creation
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    print(f"Product created successfully: {product['name']}")

    # Count products for user
    count = await db.products.count_documents({"user_id": test_user_id})
    print(f"Total products for user: {count}")

    client.close()
    return product_id

if __name__ == "__main__":
    product_id = asyncio.run(seed_test_data())
    print(f"\n\nTest product ID for testing: {product_id}")
