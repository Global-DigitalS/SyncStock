from __future__ import annotations

from pydantic import BaseModel, Field

from models.product import ProductResponse


# ==================== CATALOG MODELS ====================

class CatalogCreate(BaseModel):
    name: str = Field(..., description="Nombre del catálogo")
    description: str | None = None
    is_default: bool = False


class CatalogUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_default: bool | None = None


class CatalogResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_default: bool = False
    product_count: int = 0
    margin_rules_count: int = 0
    categories_count: int = 0
    created_at: str


class CatalogProductAdd(BaseModel):
    product_ids: list[str]
    custom_prices: dict[str, float] | None = None
    category_ids: list[str] | None = None


class CatalogItemCreate(BaseModel):
    product_id: str
    custom_price: float | None = None
    custom_name: str | None = None
    active: bool = True
    category_ids: list[str] | None = None


class CatalogItemResponse(BaseModel):
    id: str
    product_id: str
    product: ProductResponse
    custom_price: float | None = None
    custom_name: str | None = None
    final_price: float
    active: bool
    category_ids: list[str] = []
    created_at: str


class CatalogItemCategoryUpdate(BaseModel):
    category_ids: list[str]


class BulkCategoryAssignment(BaseModel):
    """Asignar categorías a múltiples productos a la vez"""
    product_item_ids: list[str]
    category_ids: list[str]
    mode: str = "add"  # "add" para añadir, "replace" para reemplazar, "remove" para eliminar


class CatalogMarginRuleCreate(BaseModel):
    catalog_id: str
    name: str
    rule_type: str = "percentage"
    value: float
    apply_to: str = "all"
    apply_to_value: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    priority: int = 0


class CatalogMarginRuleResponse(BaseModel):
    id: str
    catalog_id: str
    name: str
    rule_type: str
    value: float
    apply_to: str
    apply_to_value: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    priority: int
    created_at: str


# ==================== CATALOG CATEGORY MODELS ====================

class CatalogCategoryCreate(BaseModel):
    name: str
    parent_id: str | None = None
    position: int = 0
    description: str | None = None


class CatalogCategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: str | None = None
    position: int | None = None
    description: str | None = None


class CatalogCategoryResponse(BaseModel):
    id: str
    catalog_id: str
    name: str
    parent_id: str | None = None
    position: int = 0
    description: str | None = None
    level: int = 0
    product_count: int = 0
    children: list[CatalogCategoryResponse] = []
    created_at: str


class CatalogCategoryReorder(BaseModel):
    category_id: str
    new_parent_id: str | None = None
    new_position: int


class CatalogCategoryBulkReorder(BaseModel):
    updates: list[CatalogCategoryReorder]


class ProductCategoryAssignment(BaseModel):
    category_ids: list[str]


# Resolver referencias circulares de modelos auto-referenciales
CatalogCategoryResponse.model_rebuild()


# ==================== MARGIN RULE MODELS ====================

class MarginRuleCreate(BaseModel):
    name: str
    rule_type: str
    value: float
    apply_to: str
    apply_to_value: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    priority: int = 0


class MarginRuleResponse(MarginRuleCreate):
    id: str
    user_id: str
    created_at: str


# ==================== SYNC HISTORY MODELS ====================

class SyncHistoryResponse(BaseModel):
    id: str
    supplier_id: str
    supplier_name: str
    sync_type: str  # manual, scheduled
    status: str  # success, error, partial
    imported: int = 0
    updated: int = 0
    errors: int = 0
    duration_seconds: float = 0
    error_message: str | None = None
    created_at: str


# ==================== NOTIFICATION MODELS ====================

class NotificationResponse(BaseModel):
    id: str
    type: str
    message: str
    product_id: str | None = None
    product_name: str | None = None
    read: bool
    created_at: str


class PriceHistoryResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    old_price: float
    new_price: float
    change_percentage: float
    created_at: str


# ==================== EXPORT MODELS ====================

class ExportRequest(BaseModel):
    platform: str
    catalog_ids: list[str] | None = None


# ==================== STORE CATALOG CREATION ====================

class CreateStoreCatalogRequest(BaseModel):
    """Request para crear un catálogo a partir de productos de una tienda"""
    store_config_id: str
    catalog_name: str | None = None
    catalog_id: str | None = None  # Usar catálogo existente en lugar de crear uno nuevo
    match_by: list[str] = ["sku", "ean", "name"]  # Campos para hacer matching de productos
    skip_unmatched: bool = True  # Si False, crear productos sin proveedor


class StoreCatalogCreationResponse(BaseModel):
    """Respuesta de creación de catálogo a partir de productos de una tienda"""
    catalog_id: str
    catalog_name: str
    total_products: int
    matched_products: int
    unmatched_products: int
    added_items: int
    created_products: int = 0
    errors: list[str] = []
    created_at: str
