from pydantic import BaseModel


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
    trial_days: int = 0
    features: list[str] = []
    is_active: bool = True
    created_at: str
    # Opciones de auto-sync (unificado para todos los servicios: proveedores, tiendas, CRM)
    auto_sync_enabled: bool = False  # Si este plan permite auto-sync
    sync_intervals: list[int] = []  # Intervalos permitidos en horas: [1, 6, 12, 24]
    # Campos legacy para compatibilidad
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
    # Estadísticas de monitorización de competidores
    competitors_active: int = 0
    competitors_snapshots_24h: int = 0
    competitors_alerts_triggered_7d: int = 0
    competitors_pending_matches: int = 0
