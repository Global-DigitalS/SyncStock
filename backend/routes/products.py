import os
import re
import uuid
from datetime import UTC, datetime

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.schemas import ProductResponse, ProductUpdate, SupplierOffer, UnifiedProductResponse
from services.auth import get_current_user
from services.database import db

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# Directory for product images - use path relative to this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "products")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Magic bytes (file signatures) for allowed image types
_IMAGE_MAGIC: dict[bytes, str] = {
    b"\xff\xd8\xff": "jpg",          # JPEG
    b"\x89PNG\r\n\x1a\n": "png",     # PNG
    b"GIF87a": "gif",                # GIF87
    b"GIF89a": "gif",                # GIF89
    b"RIFF": "webp",                 # WebP (needs extra check)
}


def _detect_image_type(data: bytes) -> str | None:
    """Return image type from magic bytes, or None if not a recognised image."""
    for magic, img_type in _IMAGE_MAGIC.items():
        if data[:len(magic)] == magic:
            # WebP: bytes 8-12 must be b"WEBP"
            if img_type == "webp" and data[8:12] != b"WEBP":
                return None
            return img_type
    return None


@router.get("/products", response_model=list[ProductResponse])
async def get_products(
    supplier_id: str | None = None, category: str | None = None,
    search: str | None = None, min_stock: int | None = None,
    max_stock: int | None = None, min_price: float | None = None,
    max_price: float | None = None, skip: int = Query(0, ge=0, le=100000), limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user)
):
    query = {"user_id": user["id"]}
    if supplier_id:
        query["supplier_id"] = supplier_id
    if category:
        query["category"] = category
    if search:
        _s = re.escape(search[:100])
        query["$or"] = [
            {"name": {"$regex": _s, "$options": "i"}},
            {"sku": {"$regex": _s, "$options": "i"}},
            {"ean": {"$regex": _s, "$options": "i"}},
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


@router.get("/products/brands")
async def get_brands(
    supplier_id: str | None = None,
    user: dict = Depends(get_current_user)
):
    """Obtener las marcas únicas disponibles, opcionalmente filtradas por proveedor."""
    query = {"user_id": user["id"], "brand": {"$nin": [None, ""]}}
    if supplier_id:
        query["supplier_id"] = supplier_id
    brands = await db.products.distinct("brand", query)
    return sorted([b for b in brands if b])


@router.get("/products/search/global")
@limiter.limit("100/minute")
async def search_products_global(
    request: Request,
    q: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock: bool | None = None,
    limit_per_supplier: int = Query(10, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """
    Búsqueda global de productos en todos los proveedores.
    Devuelve resultados agrupados por proveedor con conteo total.
    """
    if not q and not category and not brand and min_price is None and max_price is None and in_stock is None:
        return {"total": 0, "results": []}

    query: dict = {"user_id": user["id"]}
    if q:
        _s = re.escape(q[:100])
        query["$or"] = [
            {"name": {"$regex": _s, "$options": "i"}},
            {"sku": {"$regex": _s, "$options": "i"}},
            {"ean": {"$regex": _s, "$options": "i"}},
            {"brand": {"$regex": _s, "$options": "i"}},
            {"part_number": {"$regex": _s, "$options": "i"}},
        ]
    if category:
        query["category"] = category
    if brand:
        query["brand"] = {"$regex": re.escape(brand[:100]), "$options": "i"}
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    if in_stock:
        query["stock"] = {"$gt": 0}

    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$supplier_id",
            "supplier_name": {"$first": "$supplier_name"},
            "count": {"$sum": 1},
            "products": {"$push": {
                "id": "$id",
                "name": "$name",
                "sku": "$sku",
                "ean": "$ean",
                "part_number": "$part_number",
                "price": "$price",
                "stock": "$stock",
                "brand": "$brand",
                "category": "$category",
                "image_url": "$image_url",
            }}
        }},
        {"$sort": {"count": -1}},
        {"$project": {
            "_id": 0,
            "supplier": {"id": "$_id", "name": "$supplier_name"},
            "count": 1,
            "products": {"$slice": ["$products", limit_per_supplier]}
        }}
    ]

    results = await db.products.aggregate(pipeline).to_list(500)
    total = sum(r["count"] for r in results)
    return {"total": total, "results": results}


@router.get("/products/category-hierarchy")
async def get_category_hierarchy(
    supplier_id: str | None = None,
    user: dict = Depends(get_current_user)
):
    """
    Obtener la jerarquía completa de categorías con subcategorías.
    Devuelve un árbol de categorías con sus conteos.
    """
    query = {"user_id": user["id"]}
    if supplier_id:
        query["supplier_id"] = supplier_id

    # Agregación para obtener la jerarquía
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": {
                "category": "$category",
                "subcategory": "$subcategory",
                "subcategory2": "$subcategory2"
            },
            "count": {"$sum": 1},
            "selected_count": {"$sum": {"$cond": ["$is_selected", 1, 0]}}
        }},
        {"$sort": {"_id.category": 1, "_id.subcategory": 1, "_id.subcategory2": 1}},
        {"$limit": 2000},
    ]

    results = await db.products.aggregate(pipeline).to_list(2000)

    # Construir árbol jerárquico
    hierarchy = {}
    for item in results:
        _id = item.get("_id", {})
        cat = _id.get("category") or "Sin categoría"
        subcat = _id.get("subcategory")
        subcat2 = _id.get("subcategory2")
        count = item["count"]
        selected = item["selected_count"]

        if cat not in hierarchy:
            hierarchy[cat] = {
                "name": cat,
                "count": 0,
                "selected_count": 0,
                "subcategories": {}
            }

        hierarchy[cat]["count"] += count
        hierarchy[cat]["selected_count"] += selected

        if subcat:
            if subcat not in hierarchy[cat]["subcategories"]:
                hierarchy[cat]["subcategories"][subcat] = {
                    "name": subcat,
                    "count": 0,
                    "selected_count": 0,
                    "subcategories": {}
                }

            hierarchy[cat]["subcategories"][subcat]["count"] += count
            hierarchy[cat]["subcategories"][subcat]["selected_count"] += selected

            if subcat2:
                if subcat2 not in hierarchy[cat]["subcategories"][subcat]["subcategories"]:
                    hierarchy[cat]["subcategories"][subcat]["subcategories"][subcat2] = {
                        "name": subcat2,
                        "count": 0,
                        "selected_count": 0
                    }

                hierarchy[cat]["subcategories"][subcat]["subcategories"][subcat2]["count"] += count
                hierarchy[cat]["subcategories"][subcat]["subcategories"][subcat2]["selected_count"] += selected

    # Convertir a lista ordenada
    result = []
    for cat_name in sorted(hierarchy.keys()):
        cat_data = hierarchy[cat_name]
        cat_item = {
            "name": cat_data["name"],
            "count": cat_data["count"],
            "selected_count": cat_data["selected_count"],
            "subcategories": []
        }

        for subcat_name in sorted(cat_data["subcategories"].keys()):
            subcat_data = cat_data["subcategories"][subcat_name]
            subcat_item = {
                "name": subcat_data["name"],
                "count": subcat_data["count"],
                "selected_count": subcat_data["selected_count"],
                "subcategories": []
            }

            for subcat2_name in sorted(subcat_data["subcategories"].keys()):
                subcat2_data = subcat_data["subcategories"][subcat2_name]
                subcat_item["subcategories"].append({
                    "name": subcat2_data["name"],
                    "count": subcat2_data["count"],
                    "selected_count": subcat2_data["selected_count"]
                })

            cat_item["subcategories"].append(subcat_item)

        result.append(cat_item)

    return result


@router.get("/products/selected-count")
async def get_selected_products_count(
    supplier_id: str | None = None,
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


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, user: dict = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": user["id"]}, {"_id": 0, "user_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductResponse(**product)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, update: ProductUpdate, user: dict = Depends(get_current_user)):
    existing = await db.products.find_one({"id": product_id, "user_id": user["id"]}, {"_id": 0, "id": 1})
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(UTC).isoformat()
        await db.products.update_one({"id": product_id}, {"$set": update_data})
    updated = await db.products.find_one({"id": product_id}, {"_id": 0, "user_id": 0})
    return ProductResponse(**updated)



@router.post("/products/add-to-catalogs")
@limiter.limit("30/minute")
async def add_products_to_multiple_catalogs(
    request: Request,
    data: dict, user: dict = Depends(get_current_user)
):
    product_ids = data.get("product_ids", [])
    catalog_ids = data.get("catalog_ids", [])

    if not product_ids or not catalog_ids:
        return {"added": 0, "message": "No hay productos o catálogos seleccionados"}

    # Obtener todos los catálogos válidos en una sola consulta
    catalog_docs = await db.catalogs.find(
        {"id": {"$in": catalog_ids}, "user_id": user["id"]}
    ).to_list(100)
    valid_catalog_ids = {c["id"] for c in catalog_docs}

    if not valid_catalog_ids:
        return {"added": 0, "message": "No se encontraron catálogos válidos"}

    # Obtener items existentes en una sola consulta
    existing_items = await db.catalog_items.find({
        "catalog_id": {"$in": list(valid_catalog_ids)},
        "product_id": {"$in": product_ids}
    }).to_list(10000)
    existing_pairs = {(item["catalog_id"], item["product_id"]) for item in existing_items}

    # Preparar inserción en lote
    items_to_insert = []
    now = datetime.now(UTC).isoformat()
    for catalog_id in valid_catalog_ids:
        for product_id in product_ids:
            if (catalog_id, product_id) not in existing_pairs:
                items_to_insert.append({
                    "id": str(uuid.uuid4()),
                    "catalog_id": catalog_id,
                    "product_id": product_id,
                    "user_id": user["id"],
                    "custom_price": None,
                    "custom_name": None,
                    "active": True,
                    "created_at": now
                })

    # Insertar todo en una sola operación
    if items_to_insert:
        await db.catalog_items.insert_many(items_to_insert)

    added = len(items_to_insert)
    return {"added": added, "message": f"{added} productos añadidos"}


# ==================== UNIFIED PRODUCTS (EAN-based) ====================

@router.get("/products-unified", response_model=list[UnifiedProductResponse])
async def get_unified_products(
    category: str | None = None, search: str | None = None,
    min_stock: int | None = None, skip: int = Query(0, ge=0, le=100000), limit: int = Query(50, ge=1, le=500),
    sort_by: str | None = None, sort_order: str | None = "asc",
    include_all: bool | None = False,
    user: dict = Depends(get_current_user)
):
    # Solo mostrar productos seleccionados (is_selected=True) a menos que include_all=True
    # Filtrar productos con EAN válido (no null y no vacío)
    match_query = {
        "user_id": user["id"],
        "ean": {"$nin": [None, ""]},
    }
    if not include_all:
        match_query["is_selected"] = True
    if category:
        match_query["category"] = category
    if search:
        _s = re.escape(search[:100])
        match_query["$or"] = [
            {"name": {"$regex": _s, "$options": "i"}},
            {"sku": {"$regex": _s, "$options": "i"}},
            {"ean": {"$regex": _s, "$options": "i"}},
        ]
    pipeline = [
        {"$match": match_query},
        {"$group": {
            "_id": "$ean",
            "products": {"$push": {
                "id": "$id", "name": "$name", "description": "$description",
                "category": "$category", "brand": "$brand", "image_url": "$image_url",
                "price": "$price", "stock": "$stock", "sku": "$sku",
                "supplier_id": "$supplier_id", "supplier_name": "$supplier_name", "weight": "$weight",
                "short_description": "$short_description", "long_description": "$long_description"
            }},
            "total_stock": {"$sum": "$stock"},
            "supplier_count": {"$sum": 1},
            "min_price": {"$min": "$price"},
            "first_name": {"$first": "$name"}
        }},
        {"$match": {"_id": {"$nin": [None, ""]}}}
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
            ean=ean if ean else "", name=best.get("name", ""), description=best.get("description"),
            category=best.get("category"), brand=best.get("brand"),
            image_url=best.get("image_url"), best_price=best.get("price", 0),
            best_supplier=best.get("supplier_name", ""), best_supplier_id=best.get("supplier_id", ""),
            total_stock=item["total_stock"], supplier_count=item["supplier_count"],
            suppliers=suppliers, weight=best.get("weight"),
            short_description=best.get("short_description"),
            long_description=best.get("long_description")
        ))
    return unified_products


@router.get("/products-unified/count")
async def get_unified_products_count(
    category: str | None = None, search: str | None = None,
    min_stock: int | None = None,
    include_all: bool | None = False,
    user: dict = Depends(get_current_user)
):
    """Obtener el total de productos unificados para paginación"""
    match_query = {
        "user_id": user["id"],
        "ean": {"$nin": [None, ""]},
    }
    if not include_all:
        match_query["is_selected"] = True
    if category:
        match_query["category"] = category
    if search:
        _s = re.escape(search[:100])
        match_query["$or"] = [
            {"name": {"$regex": _s, "$options": "i"}},
            {"sku": {"$regex": _s, "$options": "i"}},
            {"ean": {"$regex": _s, "$options": "i"}},
        ]
    pipeline = [
        {"$match": match_query},
        {"$group": {
            "_id": "$ean",
            "total_stock": {"$sum": "$stock"}
        }},
        {"$match": {"_id": {"$nin": [None, ""]}}}
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
        weight=best.get("weight"),
        short_description=best.get("short_description"),
        long_description=best.get("long_description")
    )


# ==================== PRODUCT SELECTION (Supplier -> Products flow) ====================

@router.post("/products/select")
@limiter.limit("60/minute")
async def select_products(
    request: Request,
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
        {"$set": {"is_selected": True, "updated_at": datetime.now(UTC).isoformat()}}
    )

    return {
        "selected": result.modified_count,
        "message": f"{result.modified_count} productos seleccionados"
    }


@router.post("/products/deselect")
@limiter.limit("60/minute")
async def deselect_products(
    request: Request,
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
        {"$set": {"is_selected": False, "updated_at": datetime.now(UTC).isoformat()}}
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
    Seleccionar todos los productos de un proveedor o filtrados por categoría/subcategoría.
    Soporta filtrado jerárquico por categoría, subcategoría y subcategoría2.
    """
    supplier_id = data.get("supplier_id")
    category = data.get("category")
    subcategory = data.get("subcategory")
    subcategory2 = data.get("subcategory2")
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
    if subcategory:
        query["subcategory"] = subcategory
    if subcategory2:
        query["subcategory2"] = subcategory2

    result = await db.products.update_many(
        query,
        {"$set": {"is_selected": select_all, "updated_at": datetime.now(UTC).isoformat()}}
    )

    action = "seleccionados" if select_all else "deseleccionados"

    # Construir mensaje descriptivo
    filter_parts = []
    if category:
        filter_parts.append(category)
    if subcategory:
        filter_parts.append(subcategory)
    if subcategory2:
        filter_parts.append(subcategory2)

    filter_msg = f" de '{' > '.join(filter_parts)}'" if filter_parts else ""

    return {
        "modified": result.modified_count,
        "message": f"{result.modified_count} productos{filter_msg} {action}"
    }


@router.get("/supplier/{supplier_id}/products", response_model=list[ProductResponse])
async def get_supplier_products(
    supplier_id: str,
    category: str | None = None,
    subcategory: str | None = None,
    subcategory2: str | None = None,
    search: str | None = None,
    is_selected: bool | None = None,
    brand: str | None = None,
    part_number: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_stock: int | None = None,
    max_stock: int | None = None,
    skip: int = Query(0, ge=0, le=100000),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user)
):
    """
    Obtener productos de un proveedor específico con filtros opcionales.
    Incluye el estado de selección (is_selected) de cada producto.
    Soporta filtrado jerárquico por categoría, subcategoría y subcategoría2,
    así como filtros avanzados por marca, part_number, rango de precio y stock.
    """
    # Verificar que el proveedor pertenece al usuario
    supplier = await db.suppliers.find_one({"id": supplier_id, "user_id": user["id"]})
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    query = {"supplier_id": supplier_id, "user_id": user["id"]}

    if category:
        query["category"] = category
    if subcategory:
        query["subcategory"] = subcategory
    if subcategory2:
        query["subcategory2"] = subcategory2
    if search:
        _s = re.escape(search[:100])
        query["$or"] = [
            {"name": {"$regex": _s, "$options": "i"}},
            {"sku": {"$regex": _s, "$options": "i"}},
            {"ean": {"$regex": _s, "$options": "i"}},
        ]
    if is_selected is not None:
        query["is_selected"] = is_selected
    if brand:
        query["brand"] = {"$regex": re.escape(brand[:100]), "$options": "i"}
    if part_number:
        query["part_number"] = {"$regex": re.escape(part_number[:100]), "$options": "i"}
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    if min_stock is not None:
        query["stock"] = {"$gte": min_stock}
    if max_stock is not None:
        query.setdefault("stock", {})["$lte"] = max_stock

    products = await db.products.find(query, {"_id": 0, "user_id": 0}).skip(skip).limit(limit).to_list(limit)

    return [ProductResponse(**p) for p in products]


@router.get("/supplier/{supplier_id}/products/count")
async def get_supplier_products_count(
    supplier_id: str,
    category: str | None = None,
    subcategory: str | None = None,
    subcategory2: str | None = None,
    search: str | None = None,
    is_selected: bool | None = None,
    brand: str | None = None,
    part_number: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_stock: int | None = None,
    max_stock: int | None = None,
    user: dict = Depends(get_current_user)
):
    """
    Obtener el conteo de productos de un proveedor con los mismos filtros.
    Soporta filtrado jerárquico por categoría, subcategoría y subcategoría2,
    así como filtros avanzados por marca, part_number, rango de precio y stock.
    """
    query = {"supplier_id": supplier_id, "user_id": user["id"]}

    if category:
        query["category"] = category
    if subcategory:
        query["subcategory"] = subcategory
    if subcategory2:
        query["subcategory2"] = subcategory2
    if search:
        _s = re.escape(search[:100])
        query["$or"] = [
            {"name": {"$regex": _s, "$options": "i"}},
            {"sku": {"$regex": _s, "$options": "i"}},
            {"ean": {"$regex": _s, "$options": "i"}},
        ]
    if is_selected is not None:
        query["is_selected"] = is_selected
    if brand:
        query["brand"] = {"$regex": re.escape(brand[:100]), "$options": "i"}
    if part_number:
        query["part_number"] = {"$regex": re.escape(part_number[:100]), "$options": "i"}
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    if min_stock is not None:
        query["stock"] = {"$gte": min_stock}
    if max_stock is not None:
        query.setdefault("stock", {})["$lte"] = max_stock

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
        {"$sort": {"_id": 1}},
        {"$limit": 1000},
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



# ==================== PRODUCT IMAGE UPLOAD ====================

@router.post("/products/{product_id}/upload-image")
@limiter.limit("20/minute")
async def upload_product_image(
    request: Request,
    product_id: str,
    image_type: str = "main",  # main, gallery
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload main image or gallery image for a product"""
    product = await db.products.find_one({"id": product_id, "user_id": user["id"]}, {"_id": 0, "id": 1, "gallery_images": 1})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Validate file type with whitelist
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
    ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

    if not file.content_type or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de imagen no permitido. Use JPG, PNG, GIF o WebP")

    raw_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if raw_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Extensión de archivo no permitida. Use .jpg, .png, .gif o .webp")

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="El archivo supera el tamaño máximo permitido de 5 MB")

    # Validate magic bytes (content-based type detection — not spoofable by client)
    detected_type = _detect_image_type(content)
    if not detected_type:
        raise HTTPException(status_code=400, detail="El contenido del archivo no corresponde a una imagen válida")

    # Normalise extension to the canonical one from magic bytes
    safe_ext = "jpg" if detected_type == "jpg" else detected_type

    # Generate unique filename with sanitized extension (never trust client filename)
    filename = f"{uuid.uuid4().hex}.{safe_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    # Build URL - use the /api/uploads/ route
    image_url = f"/api/uploads/products/{filename}"

    now = datetime.now(UTC).isoformat()

    if image_type == "main":
        # Update main image
        await db.products.update_one(
            {"id": product_id},
            {"$set": {"image_url": image_url, "updated_at": now}}
        )
    else:
        # Add to gallery
        gallery = product.get("gallery_images") or []
        gallery.append(image_url)
        await db.products.update_one(
            {"id": product_id},
            {"$set": {"gallery_images": gallery, "updated_at": now}}
        )

    return {"url": image_url, "message": "Imagen subida correctamente"}


@router.delete("/products/{product_id}/gallery-image")
async def remove_gallery_image(
    product_id: str,
    image_url: str,
    user: dict = Depends(get_current_user)
):
    """Remove an image from product gallery"""
    product = await db.products.find_one({"id": product_id, "user_id": user["id"]}, {"_id": 0, "id": 1, "gallery_images": 1})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    gallery = product.get("gallery_images") or []
    if image_url in gallery:
        gallery.remove(image_url)
        await db.products.update_one(
            {"id": product_id},
            {"$set": {"gallery_images": gallery, "updated_at": datetime.now(UTC).isoformat()}}
        )
        return {"message": "Imagen eliminada de la galería"}

    raise HTTPException(status_code=404, detail="Imagen no encontrada en la galería")


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    """Delete a single product"""
    product = await db.products.find_one({"id": product_id, "user_id": user["id"]}, {"_id": 0, "id": 1})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Remove from all catalogs first
    await db.catalog_items.delete_many({"product_id": product_id, "user_id": user["id"]})

    # Delete the product
    result = await db.products.delete_one({"id": product_id, "user_id": user["id"]})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return {"message": "Producto eliminado correctamente"}


@router.post("/products/delete-bulk")
@limiter.limit("10/minute")
async def delete_products_bulk(request: Request, data: dict, user: dict = Depends(get_current_user)):
    """Delete multiple products by their EANs"""
    eans = data.get("eans", [])
    if not eans:
        raise HTTPException(status_code=400, detail="No se proporcionaron EANs para eliminar")

    # Find products by EANs
    products = await db.products.find(
        {"ean": {"$in": eans}, "user_id": user["id"]},
        {"_id": 0, "id": 1}
    ).to_list(10000)

    if not products:
        raise HTTPException(status_code=404, detail="No se encontraron productos con los EANs proporcionados")

    product_ids = [p["id"] for p in products]

    # Remove from all catalogs first
    await db.catalog_items.delete_many({"product_id": {"$in": product_ids}, "user_id": user["id"]})

    # Delete the products
    result = await db.products.delete_many({"id": {"$in": product_ids}, "user_id": user["id"]})

    return {"deleted": result.deleted_count, "message": f"{result.deleted_count} productos eliminados"}
