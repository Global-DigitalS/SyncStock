from pydantic import BaseModel, Field


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
