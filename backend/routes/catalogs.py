from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from services.database import db
from services.auth import get_current_user
from services.sync import calculate_final_price
from models.schemas import (
    CatalogCreate, CatalogUpdate, CatalogResponse,
    CatalogProductAdd, CatalogItemCreate, CatalogMarginRuleCreate,
    CatalogMarginRuleResponse, MarginRuleCreate, MarginRuleResponse,
    ProductResponse
)

router = APIRouter()


# ==================== CATALOGS ====================

@router.post("/catalogs", response_model=CatalogResponse)
async def create_catalog(catalog: CatalogCreate, user: dict = Depends(get_current_user)):
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
        is_default=is_default, product_count=0, margin_rules_count=0, created_at=now)


@router.get("/catalogs", response_model=List[CatalogResponse])
async def get_catalogs(user: dict = Depends(get_current_user)):
    catalogs = await db.catalogs.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    result = []
    for cat in catalogs:
        product_count = await db.catalog_items.count_documents({"catalog_id": cat["id"]})
        rules_count = await db.catalog_margin_rules.count_documents({"catalog_id": cat["id"]})
        result.append(CatalogResponse(
            id=cat["id"], name=cat["name"], description=cat.get("description"),
            is_default=cat.get("is_default", False), product_count=product_count,
            margin_rules_count=rules_count, created_at=cat["created_at"]
        ))
    return result


@router.get("/catalogs/{catalog_id}", response_model=CatalogResponse)
async def get_catalog_by_id(catalog_id: str, user: dict = Depends(get_current_user)):
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]}, {"_id": 0})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    product_count = await db.catalog_items.count_documents({"catalog_id": catalog_id})
    rules_count = await db.catalog_margin_rules.count_documents({"catalog_id": catalog_id})
    return CatalogResponse(
        id=catalog["id"], name=catalog["name"], description=catalog.get("description"),
        is_default=catalog.get("is_default", False), product_count=product_count,
        margin_rules_count=rules_count, created_at=catalog["created_at"]
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
    return CatalogResponse(
        id=updated["id"], name=updated["name"], description=updated.get("description"),
        is_default=updated.get("is_default", False), product_count=product_count,
        margin_rules_count=rules_count, created_at=updated["created_at"]
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
        await db.catalog_items.insert_one({
            "id": str(uuid.uuid4()), "catalog_id": catalog_id,
            "product_id": product_id, "user_id": user["id"],
            "custom_price": custom_price, "custom_name": None, "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        added += 1
    return {"added": added, "message": f"{added} productos añadidos al catálogo"}


@router.get("/catalogs/{catalog_id}/products")
async def get_catalog_products(
    catalog_id: str, active_only: bool = False, search: Optional[str] = None,
    skip: int = 0, limit: int = 100, user: dict = Depends(get_current_user)
):
    catalog = await db.catalogs.find_one({"id": catalog_id, "user_id": user["id"]})
    if not catalog:
        raise HTTPException(status_code=404, detail="Catálogo no encontrado")
    query = {"catalog_id": catalog_id}
    if active_only:
        query["active"] = True
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
