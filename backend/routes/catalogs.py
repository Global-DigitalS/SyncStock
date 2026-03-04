from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from services.database import db
from services.auth import get_current_user, check_user_limit
from services.sync import calculate_final_price
from models.schemas import (
    CatalogCreate, CatalogUpdate, CatalogResponse,
    CatalogProductAdd, CatalogItemCreate, CatalogMarginRuleCreate,
    CatalogMarginRuleResponse, MarginRuleCreate, MarginRuleResponse,
    ProductResponse, CatalogCategoryCreate, CatalogCategoryUpdate,
    CatalogCategoryResponse, CatalogCategoryBulkReorder, CatalogItemCategoryUpdate,
    BulkCategoryAssignment
)

router = APIRouter()


# ==================== CATALOGS ====================

@router.post("/catalogs", response_model=CatalogResponse)
async def create_catalog(catalog: CatalogCreate, user: dict = Depends(get_current_user)):
    # Check user limit
    can_create = await check_user_limit(user, "catalogs")
    if not can_create:
        raise HTTPException(
            status_code=403, 
            detail=f"Has alcanzado el límite de catálogos. Máximo: {user.get('max_catalogs', 5)}"
        )
    
    catalog_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    if catalog.is_default:
        await db.catalogs.update_many({"user_id": user["id"]}, {"$set": {"is_default": False}})
    existing_count = await db.catalogs.count_documents({"user_id": user["id"]})
    is_default = catalog.is_default or existing_count == 0
    catalog_doc = {
        "id": catalog_id, "user_id": user["id"],
        "name": catalog.name, "description": catalog.description,
        "is_default": is_default, "created_at": now
    }
    await db.catalogs.insert_one(catalog_doc)
    return CatalogResponse(id=catalog_id, name=catalog.name, description=catalog.description,
        is_default=is_default, product_count=0, margin_rules_count=0, categories_count=0, created_at=now)


@router.get("/catalogs", response_model=List[CatalogResponse])
async def get_catalogs(user: dict = Depends(get_current_user)):
    catalogs = await db.catalogs.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    if not catalogs:
        return []
    
    # Obtener IDs de catálogos
    catalog_ids = [c["id"] for c in catalogs]
    
    # Obtener conteos de productos en una sola consulta con agregación
    items_pipeline = [
        {"$match": {"catalog_id": {"$in": catalog_ids}}},
        {"$group": {"_id": "$catalog_id", "count": {"$sum": 1}}}
    ]
    items_counts_list = await db.catalog_items.aggregate(items_pipeline).to_list(100)
    items_counts = {doc["_id"]: doc["count"] for doc in items_counts_list}
    
    # Obtener conteos de reglas en una sola consulta con agregación
    rules_pipeline = [
        {"$match": {"catalog_id": {"$in": catalog_ids}}},
        {"$group": {"_id": "$catalog_id", "count": {"$sum": 1}}}
    ]
    rules_counts_list = await db.catalog_margin_rules.aggregate(rules_pipeline).to_list(100)
    rules_counts = {doc["_id"]: doc["count"] for doc in rules_counts_list}
    
    # Obtener conteos de categorías
    categories_pipeline = [
        {"$match": {"catalog_id": {"$in": catalog_ids}}},
        {"$group": {"_id": "$catalog_id", "count": {"$sum": 1}}}
    ]
    categories_counts_list = await db.catalog_categories.aggregate(categories_pipeline).to_list(100)
    categories_counts = {doc["_id"]: doc["count"] for doc in categories_counts_list}
    
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
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]}, {"_id": 0})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    product_count = await db.catalog_items.count_documents({"catalog_id": catalog_id})
    rules_count = await db.catalog_margin_rules.count_documents({"catalog_id": catalog_id})
    categories_count = await db.catalog_categories.count_documents({"catalog_id": catalog_id})
    return CatalogResponse(
        id=catalog["id"], name=catalog["name"], description=catalog.get("description"),
        is_default=catalog.get("is_default", False), product_count=product_count,
        margin_rules_count=rules_count, categories_count=categories_count, created_at=catalog["created_at"]
    )


@router.put("/catalogs/{catalog_id}", response_model=CatalogResponse)
async def update_catalog(catalog_id: str, update: CatalogUpdate, user: dict = Depends(get_current_user)):
    existing = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data.get("is_default"):
        await db.catalogs.update_many({"user_id": user["id"], "id": {"$ne": catalog_id}}, {"$set": {"is_default": False}})
    if update_data:
        await db.catalogs.update_one({"id": catalog_id}, {"$set": update_data})
    updated = await db.catalogs.find_one({"id": catalog_id}, {"_id": 0})
    product_count = await db.catalog_items.count_documents({"catalog_id": catalog_id})
    rules_count = await db.catalog_margin_rules.count_documents({"catalog_id": catalog_id})
    categories_count = await db.catalog_categories.count_documents({"catalog_id": catalog_id})
    return CatalogResponse(
        id=updated["id"], name=updated["name"], description=updated.get("description"),
        is_default=updated.get("is_default", False), product_count=product_count,
        margin_rules_count=rules_count, categories_count=categories_count, created_at=updated["created_at"]
    )


@router.delete("/catalogs/{catalog_id}")
async def delete_catalog(catalog_id: str, user: dict = Depends(get_current_user)):
    existing = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    await db.catalog_items.delete_many({"catalog_id": catalog_id})
    await db.catalog_margin_rules.delete_many({"catalog_id": catalog_id})
    await db.catalogs.delete_one({"id": catalog_id})
    return {"message": "Catálogo eliminado"}


# ==================== CATALOG ITEMS ====================

@router.post("/catalogs/{catalog_id}/products")
async def add_products_to_catalog(catalog_id: str, data: CatalogProductAdd, user: dict = Depends(get_current_user)):
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    added = 0
    for product_id in data.product_ids:
        product = await db.products.find_one({"id": product_id, "user_id": user["id"]})
        if not product:
            continue
        existing = await db.catalog_items.find_one({"catalog_id": catalog_id, "product_id": product_id})
        if existing:
            continue
        custom_price = data.custom_prices.get(product_id) if data.custom_prices else None
        category_ids = data.category_ids if data.category_ids else []
        await db.catalog_items.insert_one({
            "id": str(uuid.uuid4()), "catalog_id": catalog_id,
            "product_id": product_id, "user_id": user["id"],
            "custom_price": custom_price, "custom_name": None, "active": True,
            "category_ids": category_ids,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        added += 1
    return {"added": added, "message": f"{added} productos añadidos al catálogo"}


@router.get("/catalogs/{catalog_id}/products")
async def get_catalog_products(
    catalog_id: str, active_only: bool = False, search: Optional[str] = None,
    category_id: Optional[str] = None,
    skip: int = 0, limit: int = 100, user: dict = Depends(get_current_user)
):
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    query = {"catalog_id": catalog_id}
    if active_only:
        query["active"] = True
    if category_id:
        query["category_ids"] = category_id
    items = await db.catalog_items.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    margin_rules = await db.catalog_margin_rules.find({"catalog_id": catalog_id}, {"_id": 0}).sort("priority", -1).to_list(100)
    result = []
    for item in items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0, "user_id": 0})
        if not product:
            continue
        if search:
            search_lower = search.lower()
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
            "created_at": item["created_at"]
        })
    return result


@router.delete("/catalogs/{catalog_id}/products/{item_id}")
async def remove_product_from_catalog(catalog_id: str, item_id: str, user: dict = Depends(get_current_user)):
    result = await db.catalog_items.delete_one({"id": item_id, "catalog_id": catalog_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado en el catálogo")
    return {"message": "Producto eliminado del catálogo"}


# ==================== CATALOG MARGIN RULES ====================

@router.post("/catalogs/{catalog_id}/margin-rules", response_model=CatalogMarginRuleResponse)
async def create_catalog_margin_rule(catalog_id: str, rule: CatalogMarginRuleCreate, user: dict = Depends(get_current_user)):
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    rule_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    rule_doc = {
        "id": rule_id, "catalog_id": catalog_id, "user_id": user["id"],
        "name": rule.name, "rule_type": rule.rule_type, "value": rule.value,
        "apply_to": rule.apply_to, "apply_to_value": rule.apply_to_value,
        "min_price": rule.min_price, "max_price": rule.max_price,
        "priority": rule.priority, "created_at": now
    }
    await db.catalog_margin_rules.insert_one(rule_doc)
    return CatalogMarginRuleResponse(**{k: v for k, v in rule_doc.items() if k != "user_id"})


@router.get("/catalogs/{catalog_id}/margin-rules", response_model=List[CatalogMarginRuleResponse])
async def get_catalog_margin_rules(catalog_id: str, user: dict = Depends(get_current_user)):
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    rules = await db.catalog_margin_rules.find({"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}).sort("priority", -1).to_list(100)
    return [CatalogMarginRuleResponse(**r) for r in rules]


@router.put("/catalogs/{catalog_id}/margin-rules/{rule_id}", response_model=CatalogMarginRuleResponse)
async def update_catalog_margin_rule(catalog_id: str, rule_id: str, rule: CatalogMarginRuleCreate, user: dict = Depends(get_current_user)):
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    existing = await db.catalog_margin_rules.find_one({"id": rule_id, "catalog_id": catalog_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    update_data = {
        "name": rule.name, "rule_type": rule.rule_type, "value": rule.value,
        "apply_to": rule.apply_to, "apply_to_value": rule.apply_to_value,
        "min_price": rule.min_price, "max_price": rule.max_price,
        "priority": rule.priority
    }
    await db.catalog_margin_rules.update_one({"id": rule_id}, {"$set": update_data})
    updated = await db.catalog_margin_rules.find_one({"id": rule_id}, {"_id": 0, "user_id": 0})
    return CatalogMarginRuleResponse(**updated)


@router.delete("/catalogs/{catalog_id}/margin-rules/{rule_id}")
async def delete_catalog_margin_rule(catalog_id: str, rule_id: str, user: dict = Depends(get_current_user)):
    result = await db.catalog_margin_rules.delete_one({"id": rule_id, "catalog_id": catalog_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"message": "Regla eliminada"}


# ==================== LEGACY CATALOG ENDPOINTS ====================

@router.post("/catalog")
async def add_to_catalog(item: CatalogItemCreate, user: dict = Depends(get_current_user)):
    product = await db.products.find_one({"id": item.product_id, "user_id": user["id"]})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    existing = await db.catalog.find_one({"product_id": item.product_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Producto ya está en el catálogo")
    catalog_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.catalog.insert_one({
        "id": catalog_id, "product_id": item.product_id, "user_id": user["id"],
        "custom_price": item.custom_price, "custom_name": item.custom_name,
        "active": item.active, "created_at": now
    })
    return {"id": catalog_id, "message": "Producto añadido al catálogo"}


@router.get("/catalog")
async def get_catalog(active_only: bool = False, search: Optional[str] = None,
    skip: int = 0, limit: int = 100, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if active_only:
        query["active"] = True
    catalog_items = await db.catalog.find(query, {"_id": 0, "user_id": 0}).skip(skip).limit(limit).to_list(limit)
    margin_rules = await db.margin_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("priority", -1).to_list(100)
    result = []
    for item in catalog_items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0, "user_id": 0})
        if not product:
            continue
        if search and search.lower() not in product.get("name", "").lower() and search.lower() not in product.get("sku", "").lower():
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
    existing = await db.catalog.find_one({"id": catalog_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    await db.catalog.update_one({"id": catalog_id}, {"$set": {"custom_price": item.custom_price, "custom_name": item.custom_name, "active": item.active}})
    return {"message": "Item actualizado"}


@router.delete("/catalog/{catalog_id}")
async def remove_from_catalog(catalog_id: str, user: dict = Depends(get_current_user)):
    result = await db.catalog.delete_one({"id": catalog_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return {"message": "Item eliminado del catálogo"}


# ==================== MARGIN RULES ====================

@router.post("/margin-rules", response_model=MarginRuleResponse)
async def create_margin_rule(rule: MarginRuleCreate, user: dict = Depends(get_current_user)):
    rule_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    rule_doc = {"id": rule_id, "user_id": user["id"], **rule.model_dump(), "created_at": now}
    await db.margin_rules.insert_one(rule_doc)
    rule_doc.pop("_id", None)
    return MarginRuleResponse(**rule_doc)


@router.get("/margin-rules", response_model=List[MarginRuleResponse])
async def get_margin_rules(user: dict = Depends(get_current_user)):
    rules = await db.margin_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("priority", -1).to_list(100)
    return [MarginRuleResponse(**r) for r in rules]


@router.put("/margin-rules/{rule_id}", response_model=MarginRuleResponse)
async def update_margin_rule(rule_id: str, rule: MarginRuleCreate, user: dict = Depends(get_current_user)):
    existing = await db.margin_rules.find_one({"id": rule_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    await db.margin_rules.update_one({"id": rule_id}, {"$set": rule.model_dump()})
    updated = await db.margin_rules.find_one({"id": rule_id}, {"_id": 0})
    return MarginRuleResponse(**updated)


@router.delete("/margin-rules/{rule_id}")
async def delete_margin_rule(rule_id: str, user: dict = Depends(get_current_user)):
    result = await db.margin_rules.delete_one({"id": rule_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"message": "Regla eliminada"}



# ==================== CATALOG CATEGORIES ====================

async def get_category_level(catalog_id: str, parent_id: Optional[str]) -> int:
    """Get the level of the parent category"""
    if not parent_id:
        return -1  # Return -1 so that child becomes level 0
    parent = await db.catalog_categories.find_one({"id": parent_id, "catalog_id": catalog_id})
    if not parent:
        return -1
    return parent.get("level", 0)


async def build_category_tree(categories: List[dict], parent_id: Optional[str] = None) -> List[dict]:
    """Build hierarchical tree structure from flat category list"""
    tree = []
    for cat in categories:
        if cat.get("parent_id") == parent_id:
            children = await build_category_tree(categories, cat["id"])
            # Count products in this category
            product_count = await db.catalog_items.count_documents({
                "catalog_id": cat["catalog_id"],
                "category_ids": cat["id"]
            })
            tree.append({
                **cat,
                "children": children,
                "product_count": product_count
            })
    # Sort by position
    tree.sort(key=lambda x: x.get("position", 0))
    return tree


@router.post("/catalogs/{catalog_id}/categories", response_model=CatalogCategoryResponse)
async def create_catalog_category(catalog_id: str, category: CatalogCategoryCreate, user: dict = Depends(get_current_user)):
    """Create a new category in the catalog (max 4 levels deep)"""
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    # Check parent exists and level limit
    level = 0
    if category.parent_id:
        parent = await db.catalog_categories.find_one({"id": category.parent_id, "catalog_id": catalog_id})
        if not parent:
            raise HTTPException(status_code=404, detail="Categoría padre no encontrada")
        level = await get_category_level(catalog_id, category.parent_id) + 1
        if level >= 4:
            raise HTTPException(status_code=400, detail="Máximo 4 niveles de categorías permitidos")
    
    # Get next position if not specified
    if category.position == 0:
        max_pos = await db.catalog_categories.find_one(
            {"catalog_id": catalog_id, "parent_id": category.parent_id},
            sort=[("position", -1)]
        )
        category.position = (max_pos.get("position", 0) + 1) if max_pos else 0
    
    category_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
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
    await db.catalog_categories.insert_one(category_doc)
    
    return CatalogCategoryResponse(
        id=category_id, catalog_id=catalog_id, name=category.name,
        parent_id=category.parent_id, position=category.position,
        description=category.description, level=level, product_count=0,
        children=[], created_at=now
    )


@router.get("/catalogs/{catalog_id}/categories")
async def get_catalog_categories(catalog_id: str, flat: bool = False, user: dict = Depends(get_current_user)):
    """Get all categories for a catalog (tree or flat structure)"""
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    categories = await db.catalog_categories.find(
        {"catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
    ).sort("position", 1).to_list(500)
    
    if flat:
        # Return flat list with product counts
        result = []
        for cat in categories:
            product_count = await db.catalog_items.count_documents({
                "catalog_id": catalog_id,
                "category_ids": cat["id"]
            })
            result.append({**cat, "product_count": product_count, "children": []})
        return result
    
    # Return tree structure
    return await build_category_tree(categories)


@router.get("/catalogs/{catalog_id}/categories/{category_id}", response_model=CatalogCategoryResponse)
async def get_catalog_category(catalog_id: str, category_id: str, user: dict = Depends(get_current_user)):
    """Get a single category by ID"""
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    category = await db.catalog_categories.find_one(
        {"id": category_id, "catalog_id": catalog_id}, {"_id": 0, "user_id": 0}
    )
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    product_count = await db.catalog_items.count_documents({
        "catalog_id": catalog_id,
        "category_ids": category_id
    })
    
    return CatalogCategoryResponse(**category, product_count=product_count, children=[])


@router.put("/catalogs/{catalog_id}/categories/{category_id}", response_model=CatalogCategoryResponse)
async def update_catalog_category(catalog_id: str, category_id: str, update: CatalogCategoryUpdate, user: dict = Depends(get_current_user)):
    """Update a category"""
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    existing = await db.catalog_categories.find_one({"id": category_id, "catalog_id": catalog_id})
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
        await db.catalog_categories.update_one({"id": category_id}, {"$set": update_data})
    
    updated = await db.catalog_categories.find_one({"id": category_id}, {"_id": 0, "user_id": 0})
    product_count = await db.catalog_items.count_documents({
        "catalog_id": catalog_id,
        "category_ids": category_id
    })
    
    return CatalogCategoryResponse(**updated, product_count=product_count, children=[])


@router.delete("/catalogs/{catalog_id}/categories/{category_id}")
async def delete_catalog_category(catalog_id: str, category_id: str, user: dict = Depends(get_current_user)):
    """Delete a category and optionally its children"""
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    existing = await db.catalog_categories.find_one({"id": category_id, "catalog_id": catalog_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Get all descendant categories
    async def get_descendants(parent_id: str) -> List[str]:
        descendants = []
        children = await db.catalog_categories.find(
            {"catalog_id": catalog_id, "parent_id": parent_id}
        ).to_list(100)
        for child in children:
            descendants.append(child["id"])
            descendants.extend(await get_descendants(child["id"]))
        return descendants
    
    category_ids_to_delete = [category_id] + await get_descendants(category_id)
    
    # Remove category references from products
    await db.catalog_items.update_many(
        {"catalog_id": catalog_id, "category_ids": {"$in": category_ids_to_delete}},
        {"$pull": {"category_ids": {"$in": category_ids_to_delete}}}
    )
    
    # Delete categories
    await db.catalog_categories.delete_many({"id": {"$in": category_ids_to_delete}})
    
    return {"message": f"Eliminadas {len(category_ids_to_delete)} categoría(s)"}


@router.post("/catalogs/{catalog_id}/categories/reorder")
async def reorder_catalog_categories(catalog_id: str, reorder: CatalogCategoryBulkReorder, user: dict = Depends(get_current_user)):
    """Bulk reorder categories"""
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    for update in reorder.updates:
        # Check level limit if changing parent
        if update.new_parent_id:
            new_level = await get_category_level(catalog_id, update.new_parent_id) + 1
            if new_level >= 4:
                continue  # Skip this update
            await db.catalog_categories.update_one(
                {"id": update.category_id, "catalog_id": catalog_id},
                {"$set": {"parent_id": update.new_parent_id, "position": update.new_position, "level": new_level}}
            )
        else:
            await db.catalog_categories.update_one(
                {"id": update.category_id, "catalog_id": catalog_id},
                {"$set": {"parent_id": None, "position": update.new_position, "level": 0}}
            )
    
    return {"message": "Categorías reordenadas"}


# ==================== CATALOG ITEM CATEGORIES ====================

@router.put("/catalogs/{catalog_id}/products/{item_id}/categories")
async def update_product_categories(catalog_id: str, item_id: str, update: CatalogItemCategoryUpdate, user: dict = Depends(get_current_user)):
    """Update categories for a product in the catalog"""
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    item = await db.catalog_items.find_one({"id": item_id, "catalog_id": catalog_id})
    if not item:
        raise HTTPException(status_code=404, detail="Producto no encontrado en el catálogo")
    
    # Verify all category IDs exist in this catalog
    if update.category_ids:
        valid_categories = await db.catalog_categories.find(
            {"catalog_id": catalog_id, "id": {"$in": update.category_ids}}
        ).to_list(100)
        valid_ids = [c["id"] for c in valid_categories]
        invalid_ids = set(update.category_ids) - set(valid_ids)
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"Categorías no válidas: {invalid_ids}")
    
    await db.catalog_items.update_one(
        {"id": item_id},
        {"$set": {"category_ids": update.category_ids}}
    )
    
    return {"message": "Categorías actualizadas", "category_ids": update.category_ids}


@router.get("/catalogs/{catalog_id}/categories/{category_id}/products")
async def get_category_products(catalog_id: str, category_id: str, user: dict = Depends(get_current_user)):
    """Get all products in a specific category"""
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    category = await db.catalog_categories.find_one({"id": category_id, "catalog_id": catalog_id})
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    items = await db.catalog_items.find(
        {"catalog_id": catalog_id, "category_ids": category_id}, {"_id": 0}
    ).to_list(500)
    
    result = []
    for item in items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0, "user_id": 0})
        if product:
            result.append({
                "id": item["id"],
                "product_id": item["product_id"],
                "product": product,
                "category_ids": item.get("category_ids", [])
            })
    
    return result


@router.post("/catalogs/{catalog_id}/products/bulk-categories")
async def bulk_assign_categories(catalog_id: str, data: BulkCategoryAssignment, user: dict = Depends(get_current_user)):
    """Assign categories to multiple products at once
    
    Modes:
    - add: Add the specified categories to existing ones
    - replace: Replace all categories with the specified ones
    - remove: Remove the specified categories from products
    """
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    
    if not data.product_item_ids:
        raise HTTPException(status_code=400, detail="Debe seleccionar al menos un producto")
    
    if data.mode not in ["add", "replace", "remove"]:
        raise HTTPException(status_code=400, detail="Modo no válido. Use 'add', 'replace' o 'remove'")
    
    # Verify all category IDs exist in this catalog
    if data.category_ids:
        valid_categories = await db.catalog_categories.find(
            {"catalog_id": catalog_id, "id": {"$in": data.category_ids}}
        ).to_list(100)
        valid_ids = [c["id"] for c in valid_categories]
        invalid_ids = set(data.category_ids) - set(valid_ids)
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"Categorías no válidas: {list(invalid_ids)}")
    
    updated_count = 0
    
    if data.mode == "replace":
        # Replace all categories
        result = await db.catalog_items.update_many(
            {"catalog_id": catalog_id, "id": {"$in": data.product_item_ids}},
            {"$set": {"category_ids": data.category_ids}}
        )
        updated_count = result.modified_count
        
    elif data.mode == "add":
        # Add categories to existing ones (using $addToSet to avoid duplicates)
        result = await db.catalog_items.update_many(
            {"catalog_id": catalog_id, "id": {"$in": data.product_item_ids}},
            {"$addToSet": {"category_ids": {"$each": data.category_ids}}}
        )
        updated_count = result.modified_count
        
    elif data.mode == "remove":
        # Remove specified categories
        result = await db.catalog_items.update_many(
            {"catalog_id": catalog_id, "id": {"$in": data.product_item_ids}},
            {"$pull": {"category_ids": {"$in": data.category_ids}}}
        )
        updated_count = result.modified_count
    
    return {
        "message": f"Categorías actualizadas en {updated_count} producto(s)",
        "updated_count": updated_count,
        "mode": data.mode,
        "category_ids": data.category_ids
    }
