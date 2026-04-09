from pydantic import BaseModel, Field


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
