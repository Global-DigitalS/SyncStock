from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any


# ==================== AUTH MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: Optional[str] = None
    role: Optional[str] = "user"  # superadmin, admin, user, viewer
    plan_id: Optional[str] = None  # Selected subscription plan

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = {"extra": "ignore"}

    id: str
    email: str
    name: str = ""
    company: Optional[str] = None
    role: str = "user"
    max_suppliers: int = 10
    max_catalogs: int = 5
    max_woocommerce_stores: int = 2
    max_marketplace_connections: int = 1
    max_products: Optional[int] = None
    is_active: Optional[bool] = None
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    subscription_plan_id: Optional[str] = None
    subscription_plan_name: Optional[str] = None
    subscription_status: Optional[str] = None
    trial_end: Optional[str] = None
    created_at: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    max_suppliers: Optional[int] = None
    max_catalogs: Optional[int] = None
    max_woocommerce_stores: Optional[int] = None
    max_marketplace_connections: Optional[int] = None

class UserLimits(BaseModel):
    max_suppliers: int = 10
    max_catalogs: int = 5
    max_woocommerce_stores: int = 2
    max_marketplace_connections: int = 1
    max_products: Optional[int] = 1000


class UserFullUpdate(BaseModel):
    """Model for full user update by SuperAdmin"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    role: Optional[str] = None
    max_suppliers: Optional[int] = None
    max_catalogs: Optional[int] = None
    max_woocommerce_stores: Optional[int] = None
    max_marketplace_connections: Optional[int] = None
    max_products: Optional[int] = None
    subscription_plan_id: Optional[str] = None
    subscription_plan_name: Optional[str] = None
    subscription_status: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== SUPPLIER MODELS ====================

class FtpFileConfig(BaseModel):
    path: str
    role: str = "products"
    label: Optional[str] = None
    separator: Optional[str] = ";"
    header_row: Optional[int] = 1
    merge_key: Optional[str] = None

class SupplierCreate(BaseModel):
    name: str
    description: Optional[str] = None
    connection_type: Optional[str] = "ftp"
    file_url: Optional[str] = None
    url_username: Optional[str] = None
    url_password: Optional[str] = None
    ftp_schema: Optional[str] = "ftp"
    ftp_host: Optional[str] = None
    ftp_user: Optional[str] = None
    ftp_password: Optional[str] = None
    ftp_port: Optional[int] = 21
    ftp_path: Optional[str] = None
    ftp_paths: Optional[List[Dict[str, Any]]] = None
    ftp_mode: Optional[str] = "passive"
    file_format: Optional[str] = "csv"
    csv_separator: Optional[str] = ";"
    csv_enclosure: Optional[str] = '"'
    csv_line_break: Optional[str] = "\\n"
    csv_header_row: Optional[int] = 1
    column_mapping: Optional[Dict[str, Any]] = None
    strip_ean_quotes: Optional[bool] = False
    preset_id: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    connection_type: Optional[str] = None
    file_url: Optional[str] = None
    url_username: Optional[str] = None
    url_password: Optional[str] = None
    ftp_schema: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_user: Optional[str] = None
    ftp_password: Optional[str] = None
    ftp_port: Optional[int] = None
    ftp_path: Optional[str] = None
    ftp_paths: Optional[List[Dict[str, Any]]] = None
    ftp_mode: Optional[str] = None
    file_format: Optional[str] = None
    csv_separator: Optional[str] = None
    csv_enclosure: Optional[str] = None
    csv_line_break: Optional[str] = None
    csv_header_row: Optional[int] = None
    column_mapping: Optional[Dict[str, Any]] = None
    strip_ean_quotes: Optional[bool] = None
    preset_id: Optional[str] = None

class SupplierResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    connection_type: Optional[str] = "ftp"
    file_url: Optional[str] = None
    url_username: Optional[str] = None
    ftp_schema: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_user: Optional[str] = None
    ftp_port: Optional[int] = None
    ftp_path: Optional[str] = None
    ftp_paths: Optional[List[Dict[str, Any]]] = None
    ftp_mode: Optional[str] = None
    file_format: Optional[str] = None
    csv_separator: Optional[str] = None
    csv_enclosure: Optional[str] = None
    csv_line_break: Optional[str] = None
    csv_header_row: Optional[int] = None
    column_mapping: Optional[Dict[str, Any]] = None
    strip_ean_quotes: Optional[bool] = False
    preset_id: Optional[str] = None
    detected_columns: Optional[Any] = None  # Can be List[str] or Dict[str, List[str]] for multi-file
    product_count: int = 0
    last_sync: Optional[str] = None
    created_at: str


# ==================== PRODUCT MODELS ====================

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    brand: Optional[str] = None
    ean: Optional[str] = None
    weight: Optional[float] = None
    image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None  # Secondary images
    attributes: Optional[Dict[str, Any]] = None

class ProductResponse(ProductBase):
    id: str
    supplier_id: str
    supplier_name: str
    created_at: str
    updated_at: str
    # Selection flag for product flow: Supplier -> Products -> Catalogs
    is_selected: bool = False
    # Extended editable fields
    referencia: Optional[str] = None
    part_number: Optional[str] = None
    asin: Optional[str] = None
    upc: Optional[str] = None
    gtin: Optional[str] = None
    oem: Optional[str] = None
    id_erp: Optional[str] = None
    activado: bool = True
    descatalogado: bool = False
    condicion: Optional[str] = None
    activar_pos: bool = False
    tipo_pack: bool = False
    vender_sin_stock: bool = False
    nuevo: Optional[str] = None
    fecha_disponibilidad: Optional[str] = None
    stock_disponible: Optional[int] = None
    stock_fantasma: Optional[int] = None
    stock_market: Optional[int] = None
    unid_caja: Optional[int] = None
    cantidad_minima: Optional[int] = 0
    dias_entrega: Optional[int] = None
    cantidad_maxima_carrito: Optional[int] = None
    resto_stock: bool = True
    requiere_envio: bool = True
    envio_gratis: bool = False
    gastos_envio: Optional[float] = None
    largo: Optional[float] = 0
    ancho: Optional[float] = 0
    alto: Optional[float] = 0
    tipo_peso: Optional[str] = "kilogram"
    formas_pago: Optional[str] = "todas"
    formas_envio: Optional[str] = "todas"
    permite_actualizar_coste: bool = True
    permite_actualizar_stock: bool = True
    tipo_cheque_regalo: bool = False
    # PIM fields - SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    slug: Optional[str] = None
    # PIM fields - Additional pricing
    cost_price: Optional[float] = None
    compare_at_price: Optional[float] = None
    tax_class: Optional[str] = None
    currency: Optional[str] = "EUR"
    # PIM fields - Tags and custom attributes
    tags: Optional[List[str]] = None
    custom_attributes: Optional[List[Dict[str, str]]] = None
    # PIM fields - Additional info
    manufacturer: Optional[str] = None
    mpn: Optional[str] = None
    video_url: Optional[str] = None
    country_of_origin: Optional[str] = None
    warranty: Optional[str] = None
    notas_internas: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    ean: Optional[str] = None
    weight: Optional[float] = None
    image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    is_selected: Optional[bool] = None
    referencia: Optional[str] = None
    part_number: Optional[str] = None
    asin: Optional[str] = None
    upc: Optional[str] = None
    gtin: Optional[str] = None
    oem: Optional[str] = None
    id_erp: Optional[str] = None
    activado: Optional[bool] = None
    descatalogado: Optional[bool] = None
    condicion: Optional[str] = None
    activar_pos: Optional[bool] = None
    tipo_pack: Optional[bool] = None
    vender_sin_stock: Optional[bool] = None
    nuevo: Optional[str] = None
    fecha_disponibilidad: Optional[str] = None
    stock_disponible: Optional[int] = None
    stock_fantasma: Optional[int] = None
    stock_market: Optional[int] = None
    unid_caja: Optional[int] = None
    cantidad_minima: Optional[int] = None
    dias_entrega: Optional[int] = None
    cantidad_maxima_carrito: Optional[int] = None
    resto_stock: Optional[bool] = None
    requiere_envio: Optional[bool] = None
    envio_gratis: Optional[bool] = None
    gastos_envio: Optional[float] = None
    largo: Optional[float] = None
    ancho: Optional[float] = None
    alto: Optional[float] = None
    tipo_peso: Optional[str] = None
    formas_pago: Optional[str] = None
    formas_envio: Optional[str] = None
    permite_actualizar_coste: Optional[bool] = None
    permite_actualizar_stock: Optional[bool] = None
    tipo_cheque_regalo: Optional[bool] = None
    # PIM fields - SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    slug: Optional[str] = None
    # PIM fields - Additional pricing
    cost_price: Optional[float] = None
    compare_at_price: Optional[float] = None
    tax_class: Optional[str] = None
    currency: Optional[str] = None
    # PIM fields - Tags and custom attributes
    tags: Optional[List[str]] = None
    custom_attributes: Optional[List[Dict[str, str]]] = None
    # PIM fields - Additional info
    manufacturer: Optional[str] = None
    mpn: Optional[str] = None
    video_url: Optional[str] = None
    country_of_origin: Optional[str] = None
    warranty: Optional[str] = None
    notas_internas: Optional[str] = None


# ==================== CATALOG MODELS ====================

class CatalogCreate(BaseModel):
    name: str = Field(..., description="Nombre del catálogo")
    description: Optional[str] = None
    is_default: bool = False

class CatalogUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None

class CatalogResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_default: bool = False
    product_count: int = 0
    margin_rules_count: int = 0
    categories_count: int = 0
    created_at: str

class CatalogProductAdd(BaseModel):
    product_ids: List[str]
    custom_prices: Optional[Dict[str, float]] = None
    category_ids: Optional[List[str]] = None

class CatalogItemCreate(BaseModel):
    product_id: str
    custom_price: Optional[float] = None
    custom_name: Optional[str] = None
    active: bool = True
    category_ids: Optional[List[str]] = None

class CatalogItemResponse(BaseModel):
    id: str
    product_id: str
    product: ProductResponse
    custom_price: Optional[float] = None
    custom_name: Optional[str] = None
    final_price: float
    active: bool
    category_ids: List[str] = []
    created_at: str

class CatalogItemCategoryUpdate(BaseModel):
    category_ids: List[str]

class BulkCategoryAssignment(BaseModel):
    """Assign categories to multiple products at once"""
    product_item_ids: List[str]
    category_ids: List[str]
    mode: str = "add"  # "add" to append, "replace" to overwrite, "remove" to remove

class CatalogMarginRuleCreate(BaseModel):
    catalog_id: str
    name: str
    rule_type: str = "percentage"
    value: float
    apply_to: str = "all"
    apply_to_value: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    priority: int = 0

class CatalogMarginRuleResponse(BaseModel):
    id: str
    catalog_id: str
    name: str
    rule_type: str
    value: float
    apply_to: str
    apply_to_value: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    priority: int
    created_at: str


# ==================== CATALOG CATEGORY MODELS ====================

class CatalogCategoryCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    position: int = 0
    description: Optional[str] = None

class CatalogCategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    position: Optional[int] = None
    description: Optional[str] = None

class CatalogCategoryResponse(BaseModel):
    id: str
    catalog_id: str
    name: str
    parent_id: Optional[str] = None
    position: int = 0
    description: Optional[str] = None
    level: int = 0
    product_count: int = 0
    children: List["CatalogCategoryResponse"] = []
    created_at: str

class CatalogCategoryReorder(BaseModel):
    category_id: str
    new_parent_id: Optional[str] = None
    new_position: int

class CatalogCategoryBulkReorder(BaseModel):
    updates: List[CatalogCategoryReorder]

class ProductCategoryAssignment(BaseModel):
    category_ids: List[str]


# ==================== MARGIN RULE MODELS ====================

class MarginRuleCreate(BaseModel):
    name: str
    rule_type: str
    value: float
    apply_to: str
    apply_to_value: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
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
    error_message: Optional[str] = None
    created_at: str


# ==================== NOTIFICATION MODELS ====================

class NotificationResponse(BaseModel):
    id: str
    type: str
    message: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
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
    catalog_ids: Optional[List[str]] = None


# ==================== WOOCOMMERCE MODELS ====================

class WooCommerceConfig(BaseModel):
    store_url: str = Field(..., description="URL de la tienda WooCommerce")
    consumer_key: str = Field(..., description="Consumer Key de la API REST")
    consumer_secret: str = Field(..., description="Consumer Secret de la API REST")
    name: Optional[str] = "Mi Tienda WooCommerce"
    catalog_id: Optional[str] = None
    auto_sync_enabled: bool = False

class WooCommerceConfigUpdate(BaseModel):
    store_url: Optional[str] = None
    consumer_key: Optional[str] = None
    consumer_secret: Optional[str] = None
    name: Optional[str] = None
    catalog_id: Optional[str] = None
    auto_sync_enabled: Optional[bool] = None

class WooCommerceConfigResponse(BaseModel):
    id: str
    name: str
    store_url: str
    consumer_key_masked: str
    is_connected: bool = False
    last_sync: Optional[str] = None
    products_synced: int = 0
    created_at: str
    catalog_id: Optional[str] = None
    catalog_name: Optional[str] = None
    auto_sync_enabled: bool = False
    next_sync: Optional[str] = None

class WooCommerceExportRequest(BaseModel):
    config_id: str
    catalog_id: Optional[str] = None
    update_existing: bool = True

class WooCommerceExportResult(BaseModel):
    status: str
    created: int = 0
    updated: int = 0
    failed: int = 0
    errors: List[str] = []


# ==================== SUBSCRIPTION/BILLING MODELS ====================

class SubscriptionPlan(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    max_suppliers: int
    max_catalogs: int
    max_woocommerce_stores: int
    max_crm_connections: int = 1
    max_marketplace_connections: int = 1
    price_monthly: float
    price_yearly: float
    trial_days: int = 0  # Días de prueba gratuita
    features: List[str] = []
    is_active: bool = True
    created_at: str
    # Auto-sync options (unified for all services: suppliers, stores, CRM)
    auto_sync_enabled: bool = False  # Whether this plan allows auto-sync
    sync_intervals: List[int] = []  # Allowed intervals in hours: [1, 6, 12, 24]
    # Legacy fields for backwards compatibility
    crm_sync_enabled: bool = False
    crm_sync_intervals: List[int] = []

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
    ean: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    best_price: float
    best_supplier: str
    best_supplier_id: str
    total_stock: int
    supplier_count: int
    suppliers: List[SupplierOffer]
    weight: Optional[float] = None


# ==================== MARKETPLACE MODELS ====================

class MarketplaceConnectionCreate(BaseModel):
    platform_id: str
    name: str
    catalog_id: str
    store_url: Optional[str] = ""
    currency: Optional[str] = "EUR"
    condition: Optional[str] = "new"
    shipping_cost: Optional[str] = ""
    delivery_time: Optional[str] = ""
    field_mapping: Optional[Dict[str, str]] = {}
    include_out_of_stock: bool = False

class MarketplaceConnectionUpdate(BaseModel):
    name: Optional[str] = None
    catalog_id: Optional[str] = None
    store_url: Optional[str] = None
    currency: Optional[str] = None
    condition: Optional[str] = None
    shipping_cost: Optional[str] = None
    delivery_time: Optional[str] = None
    field_mapping: Optional[Dict[str, str]] = None
    include_out_of_stock: Optional[bool] = None
    is_active: Optional[bool] = None

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
    field_mapping: Dict[str, str] = {}
    include_out_of_stock: bool = False
    is_active: bool = True
    feed_format: str = "xml"
    last_generated: Optional[str] = None
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
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    base_url: Optional[str] = Field(None, min_length=1, max_length=500)
    channel: Optional[str] = None
    country: Optional[str] = Field(None, max_length=5)
    active: Optional[bool] = None

class CompetitorResponse(BaseModel):
    id: str
    user_id: str
    name: str
    base_url: str
    channel: str
    country: str = "ES"
    active: bool = True
    last_crawl_at: Optional[str] = None
    last_crawl_status: Optional[str] = None  # success, error, partial
    total_snapshots: int = 0
    created_at: str


class PriceSnapshotResponse(BaseModel):
    """Snapshot de precio de un competidor para un producto"""
    id: str
    competitor_id: str
    competitor_name: Optional[str] = None
    sku: Optional[str] = None
    ean: Optional[str] = None
    product_name: Optional[str] = None
    price: float
    original_price: Optional[float] = None  # Precio tachado / antes de descuento
    currency: str = "EUR"
    url: Optional[str] = None
    seller: Optional[str] = None
    availability: Optional[str] = None  # in_stock, out_of_stock, limited
    match_confidence: Optional[float] = None  # 0.0 - 1.0
    matched_by: Optional[str] = None  # ean, sku, fuzzy_name
    scraped_at: str


class PriceAlertCreate(BaseModel):
    """Configurar una alerta de precio"""
    sku: Optional[str] = None
    ean: Optional[str] = None
    alert_type: str = Field(..., description="Tipo: price_drop, price_below, competitor_cheaper, any_change")
    threshold: Optional[float] = Field(None, ge=0, description="Umbral en porcentaje o precio absoluto")
    channel: str = Field(default="app", description="Canal de notificación: app, email, webhook")
    webhook_url: Optional[str] = Field(None, max_length=500)
    active: bool = True

class PriceAlertUpdate(BaseModel):
    sku: Optional[str] = None
    ean: Optional[str] = None
    alert_type: Optional[str] = None
    threshold: Optional[float] = Field(None, ge=0)
    channel: Optional[str] = None
    webhook_url: Optional[str] = Field(None, max_length=500)
    active: Optional[bool] = None

class PriceAlertResponse(BaseModel):
    id: str
    user_id: str
    sku: Optional[str] = None
    ean: Optional[str] = None
    alert_type: str
    threshold: Optional[float] = None
    channel: str = "app"
    webhook_url: Optional[str] = None
    active: bool = True
    last_triggered_at: Optional[str] = None
    trigger_count: int = 0
    created_at: str


class CompetitorPriceComparison(BaseModel):
    """Comparación de precio de un producto con competidores"""
    sku: str
    ean: Optional[str] = None
    product_name: Optional[str] = None
    my_price: Optional[float] = None
    competitors: List[PriceSnapshotResponse] = []
    best_competitor_price: Optional[float] = None
    position: Optional[str] = None  # cheaper, equal, expensive
    price_difference: Optional[float] = None
    price_difference_percent: Optional[float] = None
