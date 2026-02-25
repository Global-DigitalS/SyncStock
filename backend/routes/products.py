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
    min_stock: Optional[int] = None, skip: int = 0, limit: int = 50,
    sort_by: Optional[str] = None, sort_order: Optional[str] = "asc",
    include_all: Optional[bool] = False,
    user: dict = Depends(get_current_user)
):
    # Solo mostrar productos seleccionados (is_selected=True) a menos que include_all=True
    match_query = {"user_id": user["id"], "ean": {"$ne": None, "$ne": ""}}
    if not include_all:
        match_query["is_selected"] = True
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
            "supplier_count": {"$sum": 1},
            "min_price": {"$min": "$price"},
            "first_name": {"$first": "$name"}
        }},
        {"$match": {"_id": {"$ne": None, "$ne": ""}}}
    ]
    if min_stock is not None:
        pipeline.append({"$match": {"total_stock": {"$gte": min_stock}}})
    
    # Add sorting
    if sort_by:
        sort_field_map = {
            "name": "first_name",
            "price": "min_price",
            "stock": "total_stock",
            "suppliers": "supplier_count"
        }
        if sort_by in sort_field_map:
            sort_direction = 1 if sort_order == "asc" else -1
            pipeline.append({"$sort": {sort_field_map[sort_by]: sort_direction}})
    
    # Add pagination at the end
    pipeline.append({"$skip": skip})
    pipeline.append({"$limit": limit})
    
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


@router.get("/products-unified/count")
async def get_unified_products_count(
    category: Optional[str] = None, search: Optional[str] = None,
    min_stock: Optional[int] = None,
    include_all: Optional[bool] = False,
    user: dict = Depends(get_current_user)
):
    """Obtener el total de productos unificados para paginación"""
    match_query = {"user_id": user["id"], "ean": {"$ne": None, "$ne": ""}}
    if not include_all:
        match_query["is_selected"] = True
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
            "total_stock": {"$sum": "$stock"}
        }},
        {"$match": {"_id": {"$ne": None, "$ne": ""}}}
    ]
    if min_stock is not None:
        pipeline.append({"$match": {"total_stock": {"$gte": min_stock}}})
    pipeline.append({"$count": "total"})
    
    result = await db.products.aggregate(pipeline).to_list(1)
    return {"total": result[0]["total"] if result else 0}


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


# ==================== PRODUCT SELECTION (Supplier -> Products flow) ====================

@router.post("/products/select")
async def select_products(
    data: dict, user: dict = Depends(get_current_user)
):
    """
    Seleccionar productos de un proveedor para que aparezcan en la sección Productos.
    Los productos seleccionados podrán ser añadidos a catálogos posteriormente.
    """
    product_ids = data.get("product_ids", [])
    if not product_ids:
        raise HTTPException(status_code=400, detail="No se han proporcionado productos")
    
    result = await db.products.update_many(
        {"id": {"$in": product_ids}, "user_id": user["id"]},
        {"$set": {"is_selected": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "selected": result.modified_count,
        "message": f"{result.modified_count} productos seleccionados"
    }


@router.post("/products/deselect")
async def deselect_products(
    data: dict, user: dict = Depends(get_current_user)
):
    """
    Deseleccionar productos para que no aparezcan en la sección Productos.
    """
    product_ids = data.get("product_ids", [])
    if not product_ids:
        raise HTTPException(status_code=400, detail="No se han proporcionado productos")
    
    result = await db.products.update_many(
        {"id": {"$in": product_ids}, "user_id": user["id"]},
        {"$set": {"is_selected": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "deselected": result.modified_count,
        "message": f"{result.modified_count} productos deseleccionados"
    }


@router.post("/products/select-by-supplier")
async def select_products_by_supplier(
    data: dict, user: dict = Depends(get_current_user)
):
    """
    Seleccionar todos los productos de un proveedor o solo los de una categoría específica.
    """
    supplier_id = data.get("supplier_id")
    category = data.get("category")  # Opcional: filtrar por categoría
    select_all = data.get("select_all", True)  # True para seleccionar, False para deseleccionar
    
    if not supplier_id:
        raise HTTPException(status_code=400, detail="Se requiere el ID del proveedor")
    
    # Verificar que el proveedor pertenece al usuario
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    query = {"supplier_id": supplier_id, "user_id": user["id"]}
    if category:
        query["category"] = category
    
    result = await db.products.update_many(
        query,
        {"$set": {"is_selected": select_all, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    action = "seleccionados" if select_all else "deseleccionados"
    category_msg = f" de la categoría '{category}'" if category else ""
    
    return {
        "modified": result.modified_count,
        "message": f"{result.modified_count} productos{category_msg} {action}"
    }


@router.get("/products/selected-count")
async def get_selected_products_count(
    supplier_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Obtener el conteo de productos seleccionados, opcionalmente filtrado por proveedor.
    """
    query = {"user_id": user["id"], "is_selected": True}
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    count = await db.products.count_documents(query)
    total = await db.products.count_documents({"user_id": user["id"]} if not supplier_id else {"user_id": user["id"], "supplier_id": supplier_id})
    
    return {
        "selected": count,
        "total": total,
        "percentage": round((count / total * 100) if total > 0 else 0, 1)
    }


@router.get("/supplier/{supplier_id}/products", response_model=List[ProductResponse])
async def get_supplier_products(
    supplier_id: str,
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_selected: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """
    Obtener productos de un proveedor específico con filtros opcionales.
    Incluye el estado de selección (is_selected) de cada producto.
    """
    # Verificar que el proveedor pertenece al usuario
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    query = {"supplier_id": supplier_id, "user_id": user["id"]}
    
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"ean": {"$regex": search, "$options": "i"}}
        ]
    if is_selected is not None:
        query["is_selected"] = is_selected
    
    products = await db.products.find(query, {"_id": 0, "user_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    return [ProductResponse(**p) for p in products]


@router.get("/supplier/{supplier_id}/products/count")
async def get_supplier_products_count(
    supplier_id: str,
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_selected: Optional[bool] = None,
    user: dict = Depends(get_current_user)
):
    """
    Obtener el conteo de productos de un proveedor con los mismos filtros.
    """
    query = {"supplier_id": supplier_id, "user_id": user["id"]}
    
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"ean": {"$regex": search, "$options": "i"}}
        ]
    if is_selected is not None:
        query["is_selected"] = is_selected
    
    count = await db.products.count_documents(query)
    return {"total": count}


@router.get("/supplier/{supplier_id}/categories")
async def get_supplier_categories(
    supplier_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Obtener las categorías disponibles para un proveedor específico.
    Incluye el conteo de productos por categoría.
    """
    # Verificar que el proveedor pertenece al usuario
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    pipeline = [
        {"$match": {"supplier_id": supplier_id, "user_id": user["id"], "category": {"$ne": None}}},
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1},
            "selected_count": {"$sum": {"$cond": [{"$eq": ["$is_selected", True]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    results = await db.products.aggregate(pipeline).to_list(1000)
    
    return [
        {
            "category": r["_id"],
            "count": r["count"],
            "selected_count": r["selected_count"]
        }
        for r in results
    ]

