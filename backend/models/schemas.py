# ==================== RE-EXPORTADOR DE MODELOS ====================
# Este archivo re-exporta todos los modelos desde sus archivos de dominio.
# Mantener para compatibilidad: cualquier código que importe desde
# "models.schemas" seguirá funcionando sin cambios.
#
# La lógica vive en:
#   models/user.py        — UserCreate, UserLogin, UserResponse, UserUpdate, UserLimits, UserFullUpdate
#   models/supplier.py    — FtpFileConfig, SupplierCreate, SupplierUpdate, SupplierResponse
#   models/product.py     — ProductBase, ProductResponse, ProductUpdate, SupplierOffer, UnifiedProductResponse
#   models/catalog.py     — CatalogCreate/Update/Response, CatalogItem*, CatalogMarginRule*,
#                           CatalogCategory*, MarginRule*, SyncHistoryResponse,
#                           NotificationResponse, PriceHistoryResponse, ExportRequest,
#                           CreateStoreCatalogRequest, StoreCatalogCreationResponse
#   models/store.py       — WooCommerceConfig*, MarketplaceConnection*
#   models/subscription.py — SubscriptionPlan, UserSubscription, DashboardStats
#   models/competitor.py  — Competitor*, PriceSnapshot*, PriceAlert*, CompetitorPriceComparison
#   models/page.py        — PageType, HeroSection, PageCreate, PageUpdate, PageResponse, PageListResponse

from models.catalog import (  # noqa: F401
    BulkCategoryAssignment,
    CatalogCategoryBulkReorder,
    CatalogCategoryCreate,
    CatalogCategoryReorder,
    CatalogCategoryResponse,
    CatalogCategoryUpdate,
    CatalogCreate,
    CatalogItemCategoryUpdate,
    CatalogItemCreate,
    CatalogItemResponse,
    CatalogMarginRuleCreate,
    CatalogMarginRuleResponse,
    CatalogProductAdd,
    CatalogResponse,
    CatalogUpdate,
    CreateStoreCatalogRequest,
    ExportRequest,
    MarginRuleCreate,
    MarginRuleResponse,
    NotificationResponse,
    PriceHistoryResponse,
    ProductCategoryAssignment,
    StoreCatalogCreationResponse,
    SyncHistoryResponse,
)
from models.competitor import (  # noqa: F401
    CompetitorCreate,
    CompetitorPriceComparison,
    CompetitorResponse,
    CompetitorUpdate,
    PriceAlertCreate,
    PriceAlertResponse,
    PriceAlertUpdate,
    PriceSnapshotResponse,
)
from models.product import (  # noqa: F401
    ProductBase,
    ProductResponse,
    ProductUpdate,
    SupplierOffer,
    UnifiedProductResponse,
)
from models.store import (  # noqa: F401
    MarketplaceConnectionCreate,
    MarketplaceConnectionResponse,
    MarketplaceConnectionUpdate,
    WooCommerceConfig,
    WooCommerceConfigResponse,
    WooCommerceConfigUpdate,
    WooCommerceExportRequest,
    WooCommerceExportResult,
)
from models.subscription import (  # noqa: F401
    DashboardStats,
    SubscriptionPlan,
    UserSubscription,
)
from models.supplier import (  # noqa: F401
    FtpFileConfig,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)
from models.user import (  # noqa: F401
    UserCreate,
    UserFullUpdate,
    UserLimits,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from models.page import (  # noqa: F401
    HeroSection,
    PageCreate,
    PageListResponse,
    PageResponse,
    PageType,
    PageUpdate,
)
