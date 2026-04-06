from typing import Any

from pydantic import BaseModel, EmailStr, Field

# ==================== AUTH MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: str | None = None
    role: str | None = "user"  # superadmin, admin, user, viewer
    plan_id: str | None = None  # Selected subscription plan

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = {"extra": "ignore"}

    id: str
    email: str
    name: str = ""
    company: str | None = None
    role: str = "user"
    max_suppliers: int = 10
    max_catalogs: int = 5
    max_woocommerce_stores: int = 2
    max_marketplace_connections: int = 1
    max_products: int | None = None
    is_active: bool | None = None
    plan_id: str | None = None
    plan_name: str | None = None
    subscription_plan_id: str | None = None
    subscription_plan_name: str | None = None
    subscription_status: str | None = None
    trial_end: str | None = None
    created_at: str | None = None

class UserUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    role: str | None = None
    max_suppliers: int | None = None
    max_catalogs: int | None = None
    max_woocommerce_stores: int | None = None
    max_marketplace_connections: int | None = None

class UserLimits(BaseModel):
    max_suppliers: int = 10
    max_catalogs: int = 5
    max_woocommerce_stores: int = 2
    max_marketplace_connections: int = 1
    max_products: int | None = 1000


class UserFullUpdate(BaseModel):
    """Model for full user update by SuperAdmin"""
    name: str | None = None
    email: EmailStr | None = None
    company: str | None = None
    role: str | None = None
    max_suppliers: int | None = None
    max_catalogs: int | None = None
    max_woocommerce_stores: int | None = None
    max_marketplace_connections: int | None = None
    max_products: int | None = None
    subscription_plan_id: str | None = None
    subscription_plan_name: str | None = None
    subscription_status: str | None = None
    is_active: bool | None = None


# ==================== SUPPLIER MODELS ====================

class FtpFileConfig(BaseModel):
    path: str
    role: str = "products"
    label: str | None = None
    separator: str | None = ";"
    header_row: int | None = 1
    merge_key: str | None = None

class SupplierCreate(BaseModel):
    name: str
    description: str | None = None
    connection_type: str | None = "ftp"
    file_url: str | None = None
    url_username: str | None = None
    url_password: str | None = None
    ftp_schema: str | None = "ftp"
    ftp_host: str | None = None
    ftp_user: str | None = None
    ftp_password: str | None = None
    ftp_port: int | None = 21
    ftp_path: str | None = None
    ftp_paths: list[dict[str, Any]] | None = None
    ftp_mode: str | None = "passive"
    file_format: str | None = "csv"
    csv_separator: str | None = ";"
    csv_enclosure: str | None = '"'
    csv_line_break: str | None = "\\n"
    csv_header_row: int | None = 1
    column_mapping: dict[str, Any] | None = None
    strip_ean_quotes: bool | None = False
    preset_id: str | None = None

class SupplierUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    connection_type: str | None = None
    file_url: str | None = None
    url_username: str | None = None
    url_password: str | None = None
    ftp_schema: str | None = None
    ftp_host: str | None = None
    ftp_user: str | None = None
    ftp_password: str | None = None
    ftp_port: int | None = None
    ftp_path: str | None = None
    ftp_paths: list[dict[str, Any]] | None = None
    ftp_mode: str | None = None
    file_format: str | None = None
    csv_separator: str | None = None
    csv_enclosure: str | None = None
    csv_line_break: str | None = None
    csv_header_row: int | None = None
    column_mapping: dict[str, Any] | None = None
    strip_ean_quotes: bool | None = None
    preset_id: str | None = None

class SupplierResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    connection_type: str | None = "ftp"
    file_url: str | None = None
    url_username: str | None = None
    ftp_schema: str | None = None
    ftp_host: str | None = None
    ftp_user: str | None = None
    ftp_port: int | None = None
    ftp_path: str | None = None
    ftp_paths: list[dict[str, Any]] | None = None
    ftp_mode: str | None = None
    file_format: str | None = None
    csv_separator: str | None = None
    csv_enclosure: str | None = None
    csv_line_break: str | None = None
    csv_header_row: int | None = None
    column_mapping: dict[str, Any] | None = None
    strip_ean_quotes: bool | None = False
    preset_id: str | None = None
    detected_columns: Any | None = None  # Can be List[str] or Dict[str, List[str]] for multi-file
    product_count: int = 0
    last_sync: str | None = None
    created_at: str


# ==================== PRODUCT MODELS ====================

class ProductBase(BaseModel):
    sku: str
    name: str
    description: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    price: float
    stock: int
    category: str | None = None
    brand: str | None = None
    ean: str | None = None
    weight: float | None = None
    image_url: str | None = None
    gallery_images: list[str] | None = None  # Secondary images
    attributes: dict[str, Any] | None = None

class ProductResponse(ProductBase):
    id: str
    supplier_id: str
    supplier_name: str
    created_at: str
    updated_at: str
    # Selection flag for product flow: Supplier -> Products -> Catalogs
    is_selected: bool = False
    # Extended editable fields
    referencia: str | None = None
    part_number: str | None = None
    asin: str | None = None
    upc: str | None = None
    gtin: str | None = None
    oem: str | None = None
    id_erp: str | None = None
    activado: bool = True
    descatalogado: bool = False
    condicion: str | None = None
    activar_pos: bool = False
    tipo_pack: bool = False
    vender_sin_stock: bool = False
    nuevo: str | None = None
    fecha_disponibilidad: str | None = None
    stock_disponible: int | None = None
    stock_fantasma: int | None = None
    stock_market: int | None = None
    unid_caja: int | None = None
    cantidad_minima: int | None = 0
    dias_entrega: int | None = None
    cantidad_maxima_carrito: int | None = None
    resto_stock: bool = True
    requiere_envio: bool = True
    envio_gratis: bool = False
    gastos_envio: float | None = None
    largo: float | None = 0
    ancho: float | None = 0
    alto: float | None = 0
    tipo_peso: str | None = "kilogram"
    formas_pago: str | None = "todas"
    formas_envio: str | None = "todas"
    permite_actualizar_coste: bool = True
    permite_actualizar_stock: bool = True
    tipo_cheque_regalo: bool = False
    # PIM fields - SEO
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    slug: str | None = None
    # PIM fields - Additional pricing
    cost_price: float | None = None
    compare_at_price: float | None = None
    tax_class: str | None = None
    currency: str | None = "EUR"
    # PIM fields - Tags and custom attributes
    tags: list[str] | None = None
    custom_attributes: list[dict[str, str]] | None = None
    # PIM fields - Additional info
    manufacturer: str | None = None
    mpn: str | None = None
    video_url: str | None = None
    country_of_origin: str | None = None
    warranty: str | None = None
    notas_internas: str | None = None

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    price: float | None = None
    stock: int | None = None
    category: str | None = None
    brand: str | None = None
    ean: str | None = None
    weight: float | None = None
    image_url: str | None = None
    gallery_images: list[str] | None = None
    is_selected: bool | None = None
    referencia: str | None = None
    part_number: str | None = None
    asin: str | None = None
    upc: str | None = None
    gtin: str | None = None
    oem: str | None = None
    id_erp: str | None = None
    activado: bool | None = None
    descatalogado: bool | None = None
    condicion: str | None = None
    activar_pos: bool | None = None
    tipo_pack: bool | None = None
    vender_sin_stock: bool | None = None
    nuevo: str | None = None
    fecha_disponibilidad: str | None = None
    stock_disponible: int | None = None
    stock_fantasma: int | None = None
    stock_market: int | None = None
    unid_caja: int | None = None
    cantidad_minima: int | None = None
    dias_entrega: int | None = None
    cantidad_maxima_carrito: int | None = None
    resto_stock: bool | None = None
    requiere_envio: bool | None = None
    envio_gratis: bool | None = None
    gastos_envio: float | None = None
    largo: float | None = None
    ancho: float | None = None
    alto: float | None = None
    tipo_peso: str | None = None
    formas_pago: str | None = None
    formas_envio: str | None = None
    permite_actualizar_coste: bool | None = None
    permite_actualizar_stock: bool | None = None
    tipo_cheque_regalo: bool | None = None
    # PIM fields - SEO
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    slug: str | None = None
    # PIM fields - Additional pricing
    cost_price: float | None = None
    compare_at_price: float | None = None
    tax_class: str | None = None
    currency: str | None = None
    # PIM fields - Tags and custom attributes
    tags: list[str] | None = None
    custom_attributes: list[dict[str, str]] | None = None
    # PIM fields - Additional info
    manufacturer: str | None = None
    mpn: str | None = None
    video_url: str | None = None
    country_of_origin: str | None = None
    warranty: str | None = None
    notas_internas: str | None = None


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
    """Assign categories to multiple products at once"""
    product_item_ids: list[str]
    category_ids: list[str]
    mode: str = "add"  # "add" to append, "replace" to overwrite, "remove" to remove

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
    children: list["CatalogCategoryResponse"] = []
    created_at: str

class CatalogCategoryReorder(BaseModel):
    category_id: str
    new_parent_id: str | None = None
    new_position: int

class CatalogCategoryBulkReorder(BaseModel):
    updates: list[CatalogCategoryReorder]

class ProductCategoryAssignment(BaseModel):
    category_ids: list[str]


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


# ==================== WOOCOMMERCE MODELS ====================

class WooCommerceConfig(BaseModel):
    store_url: str = Field(..., description="URL de la tienda WooCommerce")
    consumer_key: str = Field(..., description="Consumer Key de la API REST")
    consumer_secret: str = Field(..., description="Consumer Secret de la API REST")
    name: str | None = "Mi Tienda WooCommerce"
    catalog_id: str | None = None
    auto_sync_enabled: bool = False

class WooCommerceConfigUpdate(BaseModel):
    store_url: str | None = None
    consumer_key: str | None = None
    consumer_secret: str | None = None
    name: str | None = None
    catalog_id: str | None = None
    auto_sync_enabled: bool | None = None

class WooCommerceConfigResponse(BaseModel):
    id: str
    name: str
    store_url: str
    consumer_key_masked: str
    is_connected: bool = False
    last_sync: str | None = None
    products_synced: int = 0
    created_at: str
    catalog_id: str | None = None
    catalog_name: str | None = None
    auto_sync_enabled: bool = False
    next_sync: str | None = None

class WooCommerceExportRequest(BaseModel):
    config_id: str
    catalog_id: str | None = None
    update_existing: bool = True

class WooCommerceExportResult(BaseModel):
    status: str
    created: int = 0
    updated: int = 0
    failed: int = 0
    errors: list[str] = []


# ==================== SUBSCRIPTION/BILLING MODELS ====================

class SubscriptionPlan(BaseModel):
    id: str
    name: str
    description: str | None = None
    max_suppliers: int
    max_catalogs: int
    max_woocommerce_stores: int
    max_crm_connections: int = 1
    max_marketplace_connections: int = 1
    price_monthly: float
    price_yearly: float
    trial_days: int = 0  # Días de prueba gratuita
    features: list[str] = []
    is_active: bool = True
    created_at: str
    # Auto-sync options (unified for all services: suppliers, stores, CRM)
    auto_sync_enabled: bool = False  # Whether this plan allows auto-sync
    sync_intervals: list[int] = []  # Allowed intervals in hours: [1, 6, 12, 24]
    # Legacy fields for backwards compatibility
    crm_sync_enabled: bool = False
    crm_sync_intervals: list[int] = []

class UserSubscription(BaseModel):
    id: str
    user_id: str
    plan_id: str
    plan_name: str
    status: str  # active, cancelled, expired, trial
    billing_cycle: str  # monthly, yearly
    current_period_start: str
    current_period_end: str
    created_at: str


# ==================== DASHBOARD MODELS ====================

class DashboardStats(BaseModel):
    total_suppliers: int
    total_products: int
    total_catalog_items: int
    total_catalogs: int = 0
    low_stock_count: int
    out_of_stock_count: int = 0
    unread_notifications: int = 0
    recent_price_changes: int = 0
    woocommerce_stores: int = 0
    woocommerce_connected: int = 0
    woocommerce_auto_sync: int = 0
    woocommerce_total_synced: int = 0
    # Competitor monitoring stats
    competitors_active: int = 0
    competitors_snapshots_24h: int = 0
    competitors_alerts_triggered_7d: int = 0
    competitors_pending_matches: int = 0


# ==================== UNIFIED PRODUCT MODELS (EAN-based) ====================

class SupplierOffer(BaseModel):
    supplier_id: str
    supplier_name: str
    price: float
    stock: int
    sku: str
    is_best_offer: bool = False
    product_id: str

class UnifiedProductResponse(BaseModel):
    ean: str | None = None
    name: str
    description: str | None = None
    category: str | None = None
    brand: str | None = None
    image_url: str | None = None
    best_price: float
    best_supplier: str
    best_supplier_id: str
    total_stock: int
    supplier_count: int
    suppliers: list[SupplierOffer]
    weight: float | None = None
    short_description: str | None = None
    long_description: str | None = None


# ==================== MARKETPLACE MODELS ====================

class MarketplaceConnectionCreate(BaseModel):
    platform_id: str
    name: str
    catalog_id: str
    store_url: str | None = ""
    currency: str | None = "EUR"
    condition: str | None = "new"
    shipping_cost: str | None = ""
    delivery_time: str | None = ""
    field_mapping: dict[str, str] | None = {}
    include_out_of_stock: bool = False

class MarketplaceConnectionUpdate(BaseModel):
    name: str | None = None
    catalog_id: str | None = None
    store_url: str | None = None
    currency: str | None = None
    condition: str | None = None
    shipping_cost: str | None = None
    delivery_time: str | None = None
    field_mapping: dict[str, str] | None = None
    include_out_of_stock: bool | None = None
    is_active: bool | None = None

class MarketplaceConnectionResponse(BaseModel):
    id: str
    user_id: str
    platform_id: str
    platform_name: str
    name: str
    catalog_id: str
    catalog_name: str
    store_url: str = ""
    currency: str = "EUR"
    condition: str = "new"
    shipping_cost: str = ""
    delivery_time: str = ""
    field_mapping: dict[str, str] = {}
    include_out_of_stock: bool = False
    is_active: bool = True
    feed_format: str = "xml"
    last_generated: str | None = None
    products_count: int = 0
    created_at: str
    updated_at: str


# ==================== COMPETITOR MONITORING MODELS ====================

class CompetitorCreate(BaseModel):
    """Crear un competidor para monitorización de precios"""
    name: str = Field(..., min_length=1, max_length=200, description="Nombre del competidor")
    base_url: str = Field(..., min_length=1, max_length=500, description="URL base del competidor")
    channel: str = Field(..., description="Canal: amazon_es, pccomponentes, web_directa, etc.")
    country: str = Field(default="ES", max_length=5, description="Código de país ISO 3166-1 alpha-2")
    active: bool = True

class CompetitorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    base_url: str | None = Field(None, min_length=1, max_length=500)
    channel: str | None = None
    country: str | None = Field(None, max_length=5)
    active: bool | None = None

class CompetitorResponse(BaseModel):
    id: str
    user_id: str
    name: str
    base_url: str
    channel: str
    country: str = "ES"
    active: bool = True
    last_crawl_at: str | None = None
    last_crawl_status: str | None = None  # success, error, partial
    total_snapshots: int = 0
    created_at: str


class PriceSnapshotResponse(BaseModel):
    """Snapshot de precio de un competidor para un producto"""
    id: str
    competitor_id: str
    competitor_name: str | None = None
    sku: str | None = None
    ean: str | None = None
    product_name: str | None = None
    price: float
    original_price: float | None = None  # Precio tachado / antes de descuento
    currency: str = "EUR"
    url: str | None = None
    seller: str | None = None
    availability: str | None = None  # in_stock, out_of_stock, limited
    match_confidence: float | None = None  # 0.0 - 1.0
    matched_by: str | None = None  # ean, sku, fuzzy_name
    scraped_at: str


class PriceAlertCreate(BaseModel):
    """Configurar una alerta de precio"""
    sku: str | None = None
    ean: str | None = None
    alert_type: str = Field(..., description="Tipo: price_drop, price_below, competitor_cheaper, any_change")
    threshold: float | None = Field(None, ge=0, description="Umbral en porcentaje o precio absoluto")
    channel: str = Field(default="app", description="Canal de notificación: app, email, webhook")
    webhook_url: str | None = Field(None, max_length=500)
    active: bool = True

class PriceAlertUpdate(BaseModel):
    sku: str | None = None
    ean: str | None = None
    alert_type: str | None = None
    threshold: float | None = Field(None, ge=0)
    channel: str | None = None
    webhook_url: str | None = Field(None, max_length=500)
    active: bool | None = None

class PriceAlertResponse(BaseModel):
    id: str
    user_id: str
    sku: str | None = None
    ean: str | None = None
    alert_type: str
    threshold: float | None = None
    channel: str = "app"
    webhook_url: str | None = None
    active: bool = True
    last_triggered_at: str | None = None
    trigger_count: int = 0
    created_at: str


class CompetitorPriceComparison(BaseModel):
    """Comparación de precio de un producto con competidores"""
    sku: str
    ean: str | None = None
    product_name: str | None = None
    my_price: float | None = None
    competitors: list[PriceSnapshotResponse] = []
    best_competitor_price: float | None = None
    position: str | None = None  # cheaper, equal, expensive
    price_difference: float | None = None
    price_difference_percent: float | None = None


# ==================== STORE CATALOG CREATION ====================

class CreateStoreCatalogRequest(BaseModel):
    """Request to create a catalog from store products"""
    store_config_id: str
    catalog_name: str | None = None
    catalog_id: str | None = None  # Use existing catalog instead of creating new one
    match_by: list[str] = ["sku", "ean", "name"]  # Fields to match products by
    skip_unmatched: bool = True  # If False, create products without supplier

class StoreCatalogCreationResponse(BaseModel):
    """Response from creating catalog from store products"""
    catalog_id: str
    catalog_name: str
    total_products: int
    matched_products: int
    unmatched_products: int
    added_items: int
    created_products: int = 0
    errors: list[str] = []
    created_at: str
