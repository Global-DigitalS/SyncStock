from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any


# ==================== AUTH MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company: Optional[str] = None
    role: Optional[str] = "user"  # superadmin, admin, user, viewer

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    company: Optional[str] = None
    role: str = "user"
    max_suppliers: int = 10
    max_catalogs: int = 5
    max_woocommerce_stores: int = 2
    created_at: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    max_suppliers: Optional[int] = None
    max_catalogs: Optional[int] = None
    max_woocommerce_stores: Optional[int] = None

class UserLimits(BaseModel):
    max_suppliers: int = 10
    max_catalogs: int = 5
    max_woocommerce_stores: int = 2


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

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    connection_type: Optional[str] = None
    file_url: Optional[str] = None
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

class SupplierResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    connection_type: Optional[str] = "ftp"
    file_url: Optional[str] = None
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
    detected_columns: Optional[List[str]] = None
    product_count: int = 0
    last_sync: Optional[str] = None
    created_at: str


# ==================== PRODUCT MODELS ====================

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    brand: Optional[str] = None
    ean: Optional[str] = None
    weight: Optional[float] = None
    image_url: Optional[str] = None
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

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    ean: Optional[str] = None
    weight: Optional[float] = None
    image_url: Optional[str] = None
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
    created_at: str

class CatalogProductAdd(BaseModel):
    product_ids: List[str]
    custom_prices: Optional[Dict[str, float]] = None

class CatalogItemCreate(BaseModel):
    product_id: str
    custom_price: Optional[float] = None
    custom_name: Optional[str] = None
    active: bool = True

class CatalogItemResponse(BaseModel):
    id: str
    product_id: str
    product: ProductResponse
    custom_price: Optional[float] = None
    custom_name: Optional[str] = None
    final_price: float
    active: bool
    created_at: str

class CatalogMarginRuleCreate(BaseModel):
    catalog_id: str
    name: str
    rule_type: str = "percentage"
    value: float
    apply_to: str = "all"
    apply_to_value: Optional[str] = None
    priority: int = 0

class CatalogMarginRuleResponse(BaseModel):
    id: str
    catalog_id: str
    name: str
    rule_type: str
    value: float
    apply_to: str
    apply_to_value: Optional[str] = None
    priority: int
    created_at: str


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
    price_monthly: float
    price_yearly: float
    features: List[str] = []
    is_active: bool = True
    created_at: str

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
