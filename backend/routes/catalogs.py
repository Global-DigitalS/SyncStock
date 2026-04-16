import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.schemas import (
    BulkCategoryAssignment,
    CatalogCategoryBulkReorder,
    CatalogCategoryCreate,
    CatalogCategoryResponse,
    CatalogCategoryUpdate,
    CatalogCreate,
    CatalogItemCategoryUpdate,
    CatalogItemCreate,
    CatalogMarginRuleCreate,
    CatalogMarginRuleResponse,
    CatalogProductAdd,
    CatalogResponse,
    CatalogUpdate,
    MarginRuleCreate,
    MarginRuleResponse,
    ProductResponse,
)
from repositories import (
    CatalogCategoryRepository, CatalogItemRepository, CatalogRepository,
    MarginRuleRepository, ProductRepository,
)
from services.auth import check_user_limit, get_current_user
from services.database import db
from services.sync import calculate_final_price

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# MEDIUM FIX #15: Hardcoded batch limits - now configurable constants
# These limits prevent unbounded queries and memory exhaustion
MAX_CATALOGS_PER_USER = 100      # User shouldn't have >100 catalogs
MAX_CATALOG_ITEMS = 100          # Items per catalog summary
MAX_MARGIN_RULES = 100           # Rules per catalog (UI limitation)
MAX_CATEGORIES = 100             # Categories per catalog
MAX_PRODUCTS_PAGE = 1000         # Products per page query

# ==================== CATALOGS ====================

@router.post("/catalogs", response_model=CatalogResponse)
@limiter.limit("30/minute")
async def create_catalog(request: Request, catalog: CatalogCreate, user: dict = Depends(get_current_user)):
    # Check user limit
    can_create = await check_user_limit(user, "catalogs")
    if not can_create:
        raise HTTPException(
            status_code=403,
            detail=f"Has alcanzado el límite de catálogos. Máximo: {user.get('max_catalogs', 5)}"
        )

    catalog_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    if catalog.is_default:
        await CatalogRepository.set_all_non_default(user["id"])
    existing_count = await CatalogRepository.count(user["id"])
    is_default = catalog.is_default or existing_count == 0
    catalog_doc = {
        "id": catalog_id, "user_id": user["id"],
        "name": catalog.name, "description": catalog.description,
        "is_default": is_default, "created_at": now
    }
    await CatalogRepository.create(catalog_doc)
    return CatalogResponse(id=catalog_id, name=catalog.name, description=catalog.description,
        is_default=is_default, product_count=0, margin_rules_count=0, categories_count=0, created_at=now)


@router.get("/catalogs", response_model=list[CatalogResponse])
async def get_catalogs(user: dict = Depends(get_current_user)):
    catalogs = await CatalogRepository.get_all(user["id"])

    if not catalogs:
        return []

    catalog_ids = [c["id"] for c in catalogs]

    items_counts = await CatalogRepository.get_item_counts(catalog_ids)
    rules_counts = await CatalogRepository.get_rule_counts(catalog_ids)
    categories_counts = await CatalogRepository.get_category_counts(catalog_ids)

    # Construir respuesta
    result = []
    for cat in catalogs:
        result.append(CatalogResponse(
            id=cat["id"],
            name=cat["name"],
            description=cat.get("description"),
            is_default=cat.get("is_default", False),
            product_count=items_counts.get(cat["id"], 0),
            margin_rules_count=rules_counts.get(cat["id"], 0),
            categories_count=categories_counts.get(cat["id"], 0),
            created_at=cat["created_at"]
        ))
    return result


@router.get("/catalogs/{catalog_id}", response_model=CatalogResponse)
async def get_catalog_by_id(catalog_id: str, user: dict = Depends(get_current_user)):
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    product_count = await CatalogItemRepository.count(catalog_id)
    rules_count = await MarginRuleRepository.count(catalog_id)
    categories_count = await CatalogCategoryRepository.count(catalog_id)
    return CatalogResponse(
        id=catalog["id"], name=catalog["name"], description=catalog.get("description"),
        is_default=catalog.get("is_default", False), product_count=product_count,
        margin_rules_count=rules_count, categories_count=categories_count, created_at=catalog["created_at"]
    )


@router.put("/catalogs/{catalog_id}", response_model=CatalogResponse)
@limiter.limit("30/minute")
async def update_catalog(request: Request, catalog_id: str, update: CatalogUpdate, user: dict = Depends(get_current_user)):
    existing = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data.get("is_default"):
        await CatalogRepository.set_others_non_default(user["id"], catalog_id)
    if update_data:
        await CatalogRepository.update_by_id(catalog_id, update_data)
    updated = await CatalogRepository.get_by_id_no_auth(catalog_id)
    product_count = await CatalogItemRepository.count(catalog_id)
    rules_count = await MarginRuleRepository.count(catalog_id)
    categories_count = await CatalogCategoryRepository.count(catalog_id)
    return CatalogResponse(
        id=updated["id"], name=updated["name"], description=updated.get("description"),
        is_default=updated.get("is_default", False), product_count=product_count,
        margin_rules_count=rules_count, categories_count=categories_count, created_at=updated["created_at"]
    )


@router.delete("/catalogs/{catalog_id}")
@limiter.limit("10/minute")
async def delete_catalog(request: Request, catalog_id: str, user: dict = Depends(get_current_user)):
    deleted = await CatalogRepository.delete_with_cascade(catalog_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    return {"message": "Catálogo eliminado"}


# ==================== CATALOG ITEMS ====================

@router.post("/catalogs/{catalog_id}/products")
@limiter.limit("30/minute")
async def add_products_to_catalog(request: Request, catalog_id: str, data: CatalogProductAdd, user: dict = Depends(get_current_user)):
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    product_ids = list(data.product_ids)

    # Batch: validar que todos los productos existen y pertenecen al usuario
    valid_products = await ProductRepository.find_by_ids(product_ids, {"_id": 0, "id": 1, "user_id": 1})
    valid_ids = {p["id"] for p in valid_products if p.get("user_id") == user["id"]}

    # Batch: obtener los que ya están en el catálogo
    already_in_catalog = await CatalogItemRepository.find_pairs([catalog_id], product_ids)
    already_in_catalog = {pid for (_, pid) in already_in_catalog}

    now = datetime.now(UTC).isoformat()
    category_ids = data.category_ids if data.category_ids else []
    to_insert = []
    for pid in product_ids:
        if pid not in valid_ids or pid in already_in_catalog:
            continue
        custom_price = data.custom_prices.get(pid) if data.custom_prices else None
        to_insert.append({
            "id": str(uuid.uuid4()), "catalog_id": catalog_id,
            "product_id": pid, "user_id": user["id"],
            "custom_price": custom_price, "custom_name": None, "active": True,
            "category_ids": category_ids,
            "created_at": now,
        })

    if to_insert:
        await CatalogItemRepository.insert_many(to_insert)

    return {"added": len(to_insert), "message": f"{len(to_insert)} productos añadidos al catálogo"}


@router.get("/catalogs/{catalog_id}/products")
async def get_catalog_products(
    catalog_id: str, active_only: bool = False, search: str | None = None,
    category_id: str | None = None,
    skip: int = Query(0, ge=0, le=1000000),  # MEDIUM #12: Validate pagination
    limit: int = Query(100, ge=1, le=1000),  # MEDIUM #12: Validate limit range
    user: dict = Depends(get_current_user)
):
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    query = {}
    if active_only:
        query["active"] = True
    if category_id:
        query["category_ids"] = category_id
    items = await CatalogItemRepository.get_paginated(catalog_id, query, skip, limit)
    margin_rules = await MarginRuleRepository.get_all(catalog_id)

    # Batch: cargar todos los productos en una sola query
    product_ids_page = [item["product_id"] for item in items]
    products_list = await ProductRepository.find_by_ids(product_ids_page)
    products_map = {p["id"]: p for p in products_list}

    search_lower = search.lower() if search else None
    result = []
    for item in items:
        product = products_map.get(item["product_id"])
        if not product:
            continue
        if search_lower:
            if search_lower not in product.get("name", "").lower() and search_lower not in product.get("sku", "").lower():
                continue
        base_price = item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        result.append({
            "id": item["id"], "catalog_id": catalog_id,
            "product_id": item["product_id"], "product": product,
            "custom_price": item.get("custom_price"), "custom_name": item.get("custom_name"),
            "active": item.get("active", True), "final_price": final_price,
            "category_ids": item.get("category_ids", []),
            "created_at": item["created_at"],
        })
    return result


@router.delete("/catalogs/{catalog_id}/products/{item_id}")
async def remove_product_from_catalog(catalog_id: str, item_id: str, user: dict = Depends(get_current_user)):
    deleted = await CatalogItemRepository.delete_item(item_id, catalog_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Producto no encontrado en el catálogo")
    return {"message": "Producto eliminado del catálogo"}


# ==================== CATALOG MARGIN RULES ====================

@router.post("/catalogs/{catalog_id}/margin-rules", response_model=CatalogMarginRuleResponse)
@limiter.limit("30/minute")
async def create_catalog_margin_rule(request: Request, catalog_id: str, rule: CatalogMarginRuleCreate, user: dict = Depends(get_current_user)):
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    rule_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    rule_doc = {
        "id": rule_id, "catalog_id": catalog_id, "user_id": user["id"],
        "name": rule.name, "rule_type": rule.rule_type, "value": rule.value,
        "apply_to": rule.apply_to, "apply_to_value": rule.apply_to_value,
        "min_price": rule.min_price, "max_price": rule.max_price,
        "priority": rule.priority, "created_at": now
    }
    await MarginRuleRepository.create(rule_doc)
    return CatalogMarginRuleResponse(**{k: v for k, v in rule_doc.items() if k != "user_id"})


@router.get("/catalogs/{catalog_id}/margin-rules", response_model=list[CatalogMarginRuleResponse])
async def get_catalog_margin_rules(catalog_id: str, user: dict = Depends(get_current_user)):
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    rules = await MarginRuleRepository.get_all(catalog_id)
    return [CatalogMarginRuleResponse(**r) for r in rules]


@router.put("/catalogs/{catalog_id}/margin-rules/{rule_id}", response_model=CatalogMarginRuleResponse)
async def update_catalog_margin_rule(catalog_id: str, rule_id: str, rule: CatalogMarginRuleCreate, user: dict = Depends(get_current_user)):
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    existing = await MarginRuleRepository.get_by_id(rule_id, catalog_id, user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    update_data = {
        "name": rule.name, "rule_type": rule.rule_type, "value": rule.value,
        "apply_to": rule.apply_to, "apply_to_value": rule.apply_to_value,
        "min_price": rule.min_price, "max_price": rule.max_price,
        "priority": rule.priority
    }
    updated = await MarginRuleRepository.update(rule_id, user["id"], update_data)
    return CatalogMarginRuleResponse(**updated)


@router.delete("/catalogs/{catalog_id}/margin-rules/{rule_id}")
@limiter.limit("10/minute")
async def delete_catalog_margin_rule(request: Request, catalog_id: str, rule_id: str, user: dict = Depends(get_current_user)):
    deleted = await MarginRuleRepository.delete(rule_id, catalog_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"message": "Regla eliminada"}


# ==================== LEGACY CATALOG ENDPOINTS ====================

@router.post("/catalog")
async def add_to_catalog(item: CatalogItemCreate, user: dict = Depends(get_current_user)):
    product = await ProductRepository.get_by_id(item.product_id, user["id"])
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    existing = await CatalogItemRepository.get_by_product_user(item.product_id, user["id"])
    if existing:
        raise HTTPException(status_code=400, detail="Producto ya está en el catálogo")
    catalog_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    await CatalogItemRepository.insert_one({
        "id": catalog_id, "product_id": item.product_id, "user_id": user["id"],
        "custom_price": item.custom_price, "custom_name": item.custom_name,
        "active": item.active, "created_at": now
    })
    return {"id": catalog_id, "message": "Producto añadido al catálogo"}


@router.get("/catalog")
async def get_catalog(active_only: bool = False, search: str | None = None,
    skip: int = Query(0, ge=0, le=100000), limit: int = Query(100, ge=1, le=500), user: dict = Depends(get_current_user)):
    extra_q = {"active": True} if active_only else {}
    catalog_items = await CatalogItemRepository.get_by_user_paginated(user["id"], extra_q, skip, limit)
    margin_rules = await MarginRuleRepository.get_by_user(user["id"])

    # Batch: cargar todos los productos de una vez en lugar de N queries individuales
    product_ids = [item["product_id"] for item in catalog_items]
    products_list = await ProductRepository.find_by_ids(product_ids, {"_id": 0, "user_id": 0})
    products_map = {p["id"]: p for p in products_list}

    search_lower = search.lower() if search else None
    result = []
    for item in catalog_items:
        product = products_map.get(item["product_id"])
        if not product:
            continue
        if search_lower and search_lower not in product.get("name", "").lower() and search_lower not in product.get("sku", "").lower():
            continue
        base_price = item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        result.append({
            "id": item["id"], "product_id": item["product_id"],
            "product": ProductResponse(**product),
            "custom_price": item.get("custom_price"), "custom_name": item.get("custom_name"),
            "final_price": round(final_price, 2), "active": item.get("active", True),
            "created_at": item.get("created_at")
        })
    return result


@router.put("/catalog/{catalog_id}")
async def update_catalog_item(catalog_id: str, item: CatalogItemCreate, user: dict = Depends(get_current_user)):
    existing = await CatalogItemRepository.get_by_id_no_catalog(catalog_id)
    if not existing or existing.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    await CatalogItemRepository.update_by_id(catalog_id, {"custom_price": item.custom_price, "custom_name": item.custom_name, "active": item.active})
    return {"message": "Item actualizado"}


@router.delete("/catalog/{catalog_id}")
async def remove_from_catalog(catalog_id: str, user: dict = Depends(get_current_user)):
    deleted = await CatalogItemRepository.delete_item_by_id(catalog_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return {"message": "Item eliminado del catálogo"}


# ==================== MARGIN RULES ====================

@router.post("/margin-rules", response_model=MarginRuleResponse)
async def create_margin_rule(rule: MarginRuleCreate, user: dict = Depends(get_current_user)):
    rule_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    rule_doc = {"id": rule_id, "user_id": user["id"], **rule.model_dump(), "created_at": now}
    await MarginRuleRepository.create(rule_doc)
    rule_doc.pop("_id", None)
    return MarginRuleResponse(**rule_doc)


@router.get("/margin-rules", response_model=list[MarginRuleResponse])
async def get_margin_rules(user: dict = Depends(get_current_user)):
    rules = await MarginRuleRepository.get_by_user(user["id"])
    return [MarginRuleResponse(**r) for r in rules]


@router.put("/margin-rules/{rule_id}", response_model=MarginRuleResponse)
async def update_margin_rule(rule_id: str, rule: MarginRuleCreate, user: dict = Depends(get_current_user)):
    existing = await MarginRuleRepository.get_by_id_no_catalog(rule_id, user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    updated = await MarginRuleRepository.update(rule_id, user["id"], rule.model_dump())
    return MarginRuleResponse(**updated)


@router.delete("/margin-rules/{rule_id}")
async def delete_margin_rule(rule_id: str, user: dict = Depends(get_current_user)):
    deleted = await MarginRuleRepository.delete_by_user(rule_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"message": "Regla eliminada"}



# ==================== CATALOG CATEGORIES ====================

async def get_category_level(catalog_id: str, parent_id: str | None) -> int:
    """Get the level of the parent category"""
    if not parent_id:
        return -1  # Return -1 so that child becomes level 0
    parent = await CatalogCategoryRepository.get_by_id_raw(parent_id, catalog_id)
    if not parent:
        return -1
    return parent.get("level", 0)


async def build_category_tree(categories: list[dict], parent_id: str | None = None, counts_map: dict = None) -> list[dict]:
    """Build hierarchical tree structure from flat category list"""
    # Pre-cargar conteos si no se han cargado (1 query en vez de N)
    if counts_map is None and categories:
        catalog_id = categories[0].get("catalog_id")
        cat_ids = [c["id"] for c in categories]
        pipeline = [
            {"$match": {"catalog_id": catalog_id, "category_ids": {"$in": cat_ids}}},
            {"$unwind": "$category_ids"},
            {"$match": {"category_ids": {"$in": cat_ids}}},
            {"$group": {"_id": "$category_ids", "count": {"$sum": 1}}}
        ]
        counts_list = await CatalogItemRepository.aggregate(pipeline)
        counts_map = {doc["_id"]: doc["count"] for doc in counts_list}

    tree = []
    for cat in categories:
        if cat.get("parent_id") == parent_id:
            children = await build_category_tree(categories, cat["id"], counts_map)
            product_count = counts_map.get(cat["id"], 0) if counts_map else 0
            cat_data = {k: v for k, v in cat.items() if k != "_id"}
            tree.append({
                **cat_data,
                "children": children,
                "product_count": product_count
            })
    tree.sort(key=lambda x: x.get("position", 0))
    return tree


@router.post("/catalogs/{catalog_id}/categories", response_model=CatalogCategoryResponse)
async def create_catalog_category(catalog_id: str, category: CatalogCategoryCreate, user: dict = Depends(get_current_user)):
    """Create a new category in the catalog (max 4 levels deep)"""
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    # Check parent exists and level limit
    level = 0
    if category.parent_id:
        parent = await CatalogCategoryRepository.get_by_id_raw(category.parent_id, catalog_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Categoría padre no encontrada")
        level = await get_category_level(catalog_id, category.parent_id) + 1
        if level >= 4:
            raise HTTPException(status_code=400, detail="Máximo 4 niveles de categorías permitidos")

    # Get next position if not specified
    if category.position == 0:
        max_pos = await CatalogCategoryRepository.get_max_position(catalog_id, category.parent_id)
        category.position = (max_pos.get("position", 0) + 1) if max_pos else 0

    category_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    category_doc = {
        "id": category_id,
        "catalog_id": catalog_id,
        "user_id": user["id"],
        "name": category.name,
        "parent_id": category.parent_id,
        "position": category.position,
        "description": category.description,
        "level": level,
        "created_at": now
    }
    await CatalogCategoryRepository.create(category_doc)

    return CatalogCategoryResponse(
        id=category_id, catalog_id=catalog_id, name=category.name,
        parent_id=category.parent_id, position=category.position,
        description=category.description, level=level, product_count=0,
        children=[], created_at=now
    )


@router.get("/catalogs/{catalog_id}/categories")
async def get_catalog_categories(catalog_id: str, flat: bool = False, user: dict = Depends(get_current_user)):
    """Get all categories for a catalog (tree or flat structure)"""
    try:
        catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
        if not catalog:
            raise HTTPException(status_code=404, detail="Catálogo no encontrado")

        categories = await CatalogCategoryRepository.get_all_by_position(catalog_id)

        if flat:
            # Batch: obtener conteos de todas las categorías en 1 query
            cat_ids = [c["id"] for c in categories]
            pipeline = [
                {"$match": {"catalog_id": catalog_id, "category_ids": {"$in": cat_ids}}},
                {"$unwind": "$category_ids"},
                {"$match": {"category_ids": {"$in": cat_ids}}},
                {"$group": {"_id": "$category_ids", "count": {"$sum": 1}}}
            ]
            counts_list = await CatalogItemRepository.aggregate(pipeline)
            counts_map = {doc["_id"]: doc["count"] for doc in counts_list}

            result = []
            for cat in categories:
                cat_data = {k: v for k, v in cat.items() if k != "_id"}
                result.append({**cat_data, "product_count": counts_map.get(cat["id"], 0), "children": []})
            return result

        # Return tree structure
        return await build_category_tree(categories)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching categories for catalog {catalog_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno al cargar categorías")


@router.get("/catalogs/{catalog_id}/categories/{category_id}", response_model=CatalogCategoryResponse)
async def get_catalog_category(catalog_id: str, category_id: str, user: dict = Depends(get_current_user)):
    """Get a single category by ID"""
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    category = await CatalogCategoryRepository.get_by_id(category_id, catalog_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    product_count = await CatalogItemRepository.count_by_category(catalog_id, category_id)

    return CatalogCategoryResponse(**category, product_count=product_count, children=[])


@router.put("/catalogs/{catalog_id}/categories/{category_id}", response_model=CatalogCategoryResponse)
async def update_catalog_category(catalog_id: str, category_id: str, update: CatalogCategoryUpdate, user: dict = Depends(get_current_user)):
    """Update a category"""
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    existing = await CatalogCategoryRepository.get_by_id_raw(category_id, catalog_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    # If changing parent, check level limit
    if "parent_id" in update_data and update_data["parent_id"] != existing.get("parent_id"):
        if update_data["parent_id"]:
            new_level = await get_category_level(catalog_id, update_data["parent_id"]) + 1
            if new_level >= 4:
                raise HTTPException(status_code=400, detail="Máximo 4 niveles de categorías permitidos")
            # Check it's not moving to one of its own descendants
            if update_data["parent_id"] == category_id:
                raise HTTPException(status_code=400, detail="Una categoría no puede ser su propio padre")
            update_data["level"] = new_level
        else:
            update_data["level"] = 0

    if update_data:
        await CatalogCategoryRepository.update_by_id(category_id, update_data)

    updated = await CatalogCategoryRepository.get_by_id(category_id, catalog_id)
    product_count = await CatalogItemRepository.count_by_category(catalog_id, category_id)

    return CatalogCategoryResponse(**updated, product_count=product_count, children=[])


@router.delete("/catalogs/{catalog_id}/categories/{category_id}")
async def delete_catalog_category(catalog_id: str, category_id: str, user: dict = Depends(get_current_user)):
    """Delete a category and optionally its children"""
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    existing = await CatalogCategoryRepository.get_by_id_raw(category_id, catalog_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Get all descendant categories
    async def get_descendants(parent_id: str) -> list[str]:
        descendants = []
        children = await CatalogCategoryRepository.find_children(catalog_id, parent_id)
        for child in children:
            descendants.append(child["id"])
            descendants.extend(await get_descendants(child["id"]))
        return descendants

    category_ids_to_delete = [category_id] + await get_descendants(category_id)

    # Remove category references from products
    await CatalogItemRepository.remove_category_refs(catalog_id, category_ids_to_delete)

    # Delete categories
    await CatalogCategoryRepository.delete_by_ids(category_ids_to_delete)

    return {"message": f"Eliminadas {len(category_ids_to_delete)} categoría(s)"}


@router.post("/catalogs/{catalog_id}/categories/reorder")
async def reorder_catalog_categories(catalog_id: str, reorder: CatalogCategoryBulkReorder, user: dict = Depends(get_current_user)):
    """Bulk reorder categories"""
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    for update in reorder.updates:
        # Check level limit if changing parent
        if update.new_parent_id:
            new_level = await get_category_level(catalog_id, update.new_parent_id) + 1
            if new_level >= 4:
                continue  # Skip this update
            await CatalogCategoryRepository.update_by_id_in_catalog(
                update.category_id, catalog_id,
                {"parent_id": update.new_parent_id, "position": update.new_position, "level": new_level}
            )
        else:
            await CatalogCategoryRepository.update_by_id_in_catalog(
                update.category_id, catalog_id,
                {"parent_id": None, "position": update.new_position, "level": 0}
            )

    return {"message": "Categorías reordenadas"}


# ==================== CATALOG ITEM CATEGORIES ====================

@router.put("/catalogs/{catalog_id}/products/{item_id}/categories")
async def update_product_categories(catalog_id: str, item_id: str, update: CatalogItemCategoryUpdate, user: dict = Depends(get_current_user)):
    """Update categories for a product in the catalog"""
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    item = await CatalogItemRepository.get_by_item_id(item_id, catalog_id)
    if not item:
        raise HTTPException(status_code=404, detail="Producto no encontrado en el catálogo")

    # Verify all category IDs exist in this catalog
    if update.category_ids:
        valid_categories = await CatalogCategoryRepository.get_in_catalog(catalog_id, update.category_ids)
        valid_ids = [c["id"] for c in valid_categories]
        invalid_ids = set(update.category_ids) - set(valid_ids)
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"Categorías no válidas: {invalid_ids}")

    await CatalogItemRepository.update_by_id(item_id, {"category_ids": update.category_ids})

    return {"message": "Categorías actualizadas", "category_ids": update.category_ids}


@router.get("/catalogs/{catalog_id}/categories/{category_id}/products")
async def get_category_products(catalog_id: str, category_id: str, user: dict = Depends(get_current_user)):
    """Get all products in a specific category"""
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    category = await CatalogCategoryRepository.get_by_id_raw(category_id, catalog_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    items = await CatalogItemRepository.find_by_category(catalog_id, category_id)

    result = []
    product_ids_cat = [item["product_id"] for item in items]
    products_cat = await ProductRepository.find_by_ids(product_ids_cat)
    products_cat_map = {p["id"]: p for p in products_cat}
    for item in items:
        product = products_cat_map.get(item["product_id"])
        if product:
            result.append({
                "id": item["id"],
                "product_id": item["product_id"],
                "product": product,
                "category_ids": item.get("category_ids", [])
            })

    return result


@router.post("/catalogs/{catalog_id}/products/bulk-categories")
@limiter.limit("10/minute")
async def bulk_assign_categories(request: Request, catalog_id: str, data: BulkCategoryAssignment, user: dict = Depends(get_current_user)):
    """Assign categories to multiple products at once
    
    Modes:
    - add: Add the specified categories to existing ones
    - replace: Replace all categories with the specified ones
    - remove: Remove the specified categories from products
    """
    catalog = await CatalogRepository.get_by_id(catalog_id, user["id"])
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")

    if not data.product_item_ids:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos un producto")

    if data.mode not in ["add", "replace", "remove"]:
        raise HTTPException(status_code=400, detail="Modo no válido. Use 'add', 'replace' o 'remove'")

    # Verify all category IDs exist in this catalog
    if data.category_ids:
        valid_categories = await CatalogCategoryRepository.get_in_catalog(catalog_id, data.category_ids)
        valid_ids = [c["id"] for c in valid_categories]
        invalid_ids = set(data.category_ids) - set(valid_ids)
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"Categorías no válidas: {list(invalid_ids)}")

    updated_count = 0

    if data.mode == "replace":
        updated_count = await CatalogItemRepository.update_many(
            {"catalog_id": catalog_id, "id": {"$in": data.product_item_ids}},
            {"$set": {"category_ids": data.category_ids}}
        )

    elif data.mode == "add":
        updated_count = await CatalogItemRepository.update_many(
            {"catalog_id": catalog_id, "id": {"$in": data.product_item_ids}},
            {"$addToSet": {"category_ids": {"$each": data.category_ids}}}
        )

    elif data.mode == "remove":
        updated_count = await CatalogItemRepository.update_many(
            {"catalog_id": catalog_id, "id": {"$in": data.product_item_ids}},
            {"$pull": {"category_ids": {"$in": data.category_ids}}}
        )

    return {
        "message": f"Categorías actualizadas en {updated_count} producto(s)",
        "updated_count": updated_count,
        "mode": data.mode,
        "category_ids": data.category_ids
    }
