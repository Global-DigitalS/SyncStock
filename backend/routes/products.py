from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from services.database import db
from services.auth import get_current_user
from models.schemas import (
    ProductResponse, ProductUpdate, SupplierOffer, UnifiedProductResponse
)

router = APIRouter()


@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    supplier_id: Optional[str] = None, category: Optional[str] = None,
    search: Optional[str] = None, min_stock: Optional[int] = None,
    max_stock: Optional[int] = None, min_price: Optional[float] = None,
    max_price: Optional[float] = None, skip: int = 0, limit: int = 100,
    user: dict = Depends(get_current_user)
):
    query = {"user_id": user["id"]}
    if supplier_id:
        query["supplier_id"] = supplier_id
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"ean": {"$regex": search, "$options": "i"}}
        ]
    if min_stock is not None:
        query["stock"] = {"$gte": min_stock}
    if max_stock is not None:
        query.setdefault("stock", {})["$lte"] = max_stock
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    products = await db.products.find(query, {"_id": 0, "user_id": 0}).skip(skip).limit(limit).to_list(limit)
    return [ProductResponse(**p) for p in products]


@router.get("/products/categories")
async def get_categories(user: dict = Depends(get_current_user)):
    return await db.products.distinct("category", {"user_id": user["id"], "category": {"$ne": None}})


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, user: dict = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user["id"]}, {"_id": 0, "user_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductResponse(**product)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, update: ProductUpdate, user: dict = Depends(get_current_user)):
    existing = await db.products.find_one({"id": product_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.products.update_one({"id": product_id}, {"$set": update_data})
    updated = await db.products.find_one({"id": product_id}, {"_id": 0, "user_id": 0})
    return ProductResponse(**updated)



@router.post("/products/add-to-catalogs")
async def add_products_to_multiple_catalogs(
    data: dict, user: dict = Depends(get_current_user)
):
    product_ids = data.get("product_ids", [])
    catalog_ids = data.get("catalog_ids", [])
    added = 0
    for catalog_id in catalog_ids:
        catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
        if not catalog:
            continue
        for product_id in product_ids:
            existing = await db.catalog_items.find_one({"catalog_id": catalog_id, "product_id": product_id})
            if existing:
                continue
            await db.catalog_items.insert_one({
                "id": str(uuid.uuid4()), "catalog_id": catalog_id,
                "product_id": product_id, "user_id": user["id"],
                "custom_price": None, "custom_name": None, "active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            added += 1
    return {"added": added, "message": f"{added} productos añadidos"}


# ==================== UNIFIED PRODUCTS (EAN-based) ====================

@router.get("/products-unified", response_model=List[UnifiedProductResponse])
async def get_unified_products(
    category: Optional[str] = None, search: Optional[str] = None,
    min_stock: Optional[int] = None, skip: int = 0, limit: int = 100,
    user: dict = Depends(get_current_user)
):
    match_query = {"user_id": user["id"], "ean": {"$ne": None, "$ne": ""}}
    if category:
        match_query["category"] = category
    if search:
        match_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"ean": {"$regex": search, "$options": "i"}}
        ]
    pipeline = [
        {"$match": match_query},
        {"$group": {
            "_id": "$ean",
            "products": {"$push": {
                "id": "$id", "name": "$name", "description": "$description",
                "category": "$category", "brand": "$brand", "image_url": "$image_url",
                "price": "$price", "stock": "$stock", "sku": "$sku",
                "supplier_id": "$supplier_id", "supplier_name": "$supplier_name", "weight": "$weight"
            }},
            "total_stock": {"$sum": "$stock"},
            "supplier_count": {"$sum": 1}
        }},
        {"$match": {"_id": {"$ne": None, "$ne": ""}}},
        {"$skip": skip},
        {"$limit": limit}
    ]
    if min_stock is not None:
        pipeline.insert(-2, {"$match": {"total_stock": {"$gte": min_stock}}})
    results = await db.products.aggregate(pipeline).to_list(limit)
    unified_products = []
    for item in results:
        ean = item["_id"]
        products = item["products"]
        offers_with_stock = [p for p in products if p.get("stock", 0) > 0]
        best = min(offers_with_stock, key=lambda x: x.get("price", float('inf'))) if offers_with_stock else min(products, key=lambda x: x.get("price", float('inf')))
        suppliers = []
        for p in sorted(products, key=lambda x: (x.get("stock", 0) <= 0, x.get("price", float('inf')))):
            suppliers.append(SupplierOffer(
                supplier_id=p.get("supplier_id", ""), supplier_name=p.get("supplier_name", "Desconocido"),
                price=p.get("price", 0), stock=p.get("stock", 0), sku=p.get("sku", ""),
                is_best_offer=(p["id"] == best["id"]), product_id=p.get("id", "")
            ))
        unified_products.append(UnifiedProductResponse(
            ean=ean, name=best.get("name", ""), description=best.get("description"),
            category=best.get("category"), brand=best.get("brand"),
            image_url=best.get("image_url"), best_price=best.get("price", 0),
            best_supplier=best.get("supplier_name", ""), best_supplier_id=best.get("supplier_id", ""),
            total_stock=item["total_stock"], supplier_count=item["supplier_count"],
            suppliers=suppliers, weight=best.get("weight")
        ))
    return unified_products


@router.get("/products-unified/{ean}", response_model=UnifiedProductResponse)
async def get_unified_product(ean: str, user: dict = Depends(get_current_user)):
    products = await db.products.find({"user_id": user["id"], "ean": ean}, {"_id": 0}).to_list(100)
    if not products:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    offers_with_stock = [p for p in products if p.get("stock", 0) > 0]
    best = min(offers_with_stock, key=lambda x: x.get("price", float('inf'))) if offers_with_stock else min(products, key=lambda x: x.get("price", float('inf')))
    suppliers = []
    total_stock = 0
    for p in sorted(products, key=lambda x: (x.get("stock", 0) <= 0, x.get("price", float('inf')))):
        total_stock += p.get("stock", 0)
        suppliers.append(SupplierOffer(
            supplier_id=p.get("supplier_id", ""), supplier_name=p.get("supplier_name", "Desconocido"),
            price=p.get("price", 0), stock=p.get("stock", 0), sku=p.get("sku", ""),
            is_best_offer=(p["id"] == best["id"]), product_id=p.get("id", "")
        ))
    return UnifiedProductResponse(
        ean=ean, name=best.get("name", ""), description=best.get("description"),
        category=best.get("category"), brand=best.get("brand"),
        image_url=best.get("image_url"), best_price=best.get("price", 0),
        best_supplier=best.get("supplier_name", ""), best_supplier_id=best.get("supplier_id", ""),
        total_stock=total_stock, supplier_count=len(products), suppliers=suppliers,
        weight=best.get("weight")
    )
