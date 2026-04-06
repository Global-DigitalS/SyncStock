"""
Rutas de integraciones (Google Services, SEO) para SuperAdmin.
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel

from services.auth import get_superadmin_user
from services.database import db
from services.sanitizer import sanitize_string

sub_router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== GOOGLE SERVICES MODELS ====================

class GoogleServicesConfig(BaseModel):
    # Google Analytics (GA4)
    analytics_enabled: bool = False
    analytics_measurement_id: str = ""  # G-XXXXXXXXXX
    analytics_api_secret: str = ""
    # Google Search Console
    search_console_enabled: bool = False
    search_console_property_url: str = ""
    search_console_verification_code: str = ""
    # Google Tag Manager
    tag_manager_enabled: bool = False
    tag_manager_container_id: str = ""  # GTM-XXXXXXX
    # Google Ads
    google_ads_enabled: bool = False
    google_ads_conversion_id: str = ""  # AW-XXXXXXXXX
    google_ads_conversion_label: str = ""

class GoogleServicesConfigUpdate(BaseModel):
    # Google Analytics (GA4)
    analytics_enabled: bool | None = None
    analytics_measurement_id: str | None = None
    analytics_api_secret: str | None = None
    # Google Search Console
    search_console_enabled: bool | None = None
    search_console_property_url: str | None = None
    search_console_verification_code: str | None = None
    # Google Tag Manager
    tag_manager_enabled: bool | None = None
    tag_manager_container_id: str | None = None
    # Google Ads
    google_ads_enabled: bool | None = None
    google_ads_conversion_id: str | None = None
    google_ads_conversion_label: str | None = None


_GOOGLE_DEFAULTS = GoogleServicesConfig().model_dump()
_SEO_DEFAULTS = None  # initialized after SEOConfig is defined


# ==================== GOOGLE SERVICES ENDPOINTS ====================

@sub_router.get("/admin/google-services")
async def get_google_services(user: dict = Depends(get_superadmin_user)):
    """Get Google services configuration"""
    config = await db.app_config.find_one({"type": "google_services"})
    if not config:
        return _GOOGLE_DEFAULTS
    config.pop("_id", None)
    config.pop("type", None)
    config.pop("updated_at", None)
    config.pop("updated_by", None)
    return config


@sub_router.put("/admin/google-services")
async def update_google_services(data: GoogleServicesConfigUpdate, user: dict = Depends(get_superadmin_user)):
    """Update Google services configuration"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    # Sanitize string fields
    for key in list(update_data.keys()):
        if isinstance(update_data[key], str):
            update_data[key] = sanitize_string(update_data[key])

    update_data["updated_at"] = datetime.now(UTC).isoformat()
    update_data["updated_by"] = user["id"]

    await db.app_config.update_one(
        {"type": "google_services"},
        {"$set": update_data},
        upsert=True
    )

    config = await db.app_config.find_one({"type": "google_services"})
    config.pop("_id", None)
    config.pop("type", None)

    logger.info(f"Google services config updated by {user.get('email')}")
    return {"success": True, "config": config}


@sub_router.get("/google-services/public")
async def get_public_google_services():
    """Get public Google services configuration (no auth required).
    Returns only the IDs/codes needed for frontend tracking scripts."""
    try:
        config = await db.app_config.find_one({"type": "google_services"})
    except Exception:
        logger.warning("No se pudo leer la configuración de Google Services de la BD")
        return _GOOGLE_DEFAULTS

    if not config:
        return _GOOGLE_DEFAULTS

    return {
        "analytics_enabled": config.get("analytics_enabled", False),
        "analytics_measurement_id": config.get("analytics_measurement_id", ""),
        "search_console_enabled": config.get("search_console_enabled", False),
        "search_console_verification_code": config.get("search_console_verification_code", ""),
        "tag_manager_enabled": config.get("tag_manager_enabled", False),
        "tag_manager_container_id": config.get("tag_manager_container_id", ""),
        "google_ads_enabled": config.get("google_ads_enabled", False),
        "google_ads_conversion_id": config.get("google_ads_conversion_id", ""),
        "google_ads_conversion_label": config.get("google_ads_conversion_label", ""),
    }


# ==================== SEO MODELS ====================

class SEOConfig(BaseModel):
    site_url: str = "https://sync-stock.com"
    page_title: str = "SyncStock — Sincronización de Inventario B2B Automatizada"
    meta_description: str = "SyncStock — Sincroniza catálogos de proveedores, gestiona márgenes y publica en WooCommerce, Shopify y PrestaShop automáticamente. Prueba gratuita 14 días."
    meta_keywords: str = "sincronización inventario, gestión catálogos, woocommerce, shopify, prestashop, dolibarr, odoo, proveedores ftp, stock automatico, b2b saas"
    robots: str = "index, follow"
    og_title: str = "SyncStock — Sincronización de Inventario B2B Automatizada"
    og_description: str = "Conecta proveedores FTP/SFTP/URL, gestiona catálogos con márgenes personalizados y publica en tus tiendas online automáticamente."
    og_image: str = ""
    og_locale: str = "es_ES"
    og_site_name: str = "SyncStock"
    twitter_card: str = "summary_large_image"
    twitter_title: str = "SyncStock — Sincronización de Inventario B2B"
    twitter_description: str = "Automatiza la gestión de stock entre proveedores y tiendas online. WooCommerce, Shopify, Dolibarr y más."
    twitter_image: str = ""

class SEOConfigUpdate(BaseModel):
    site_url: str | None = None
    page_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    robots: str | None = None
    og_title: str | None = None
    og_description: str | None = None
    og_image: str | None = None
    og_locale: str | None = None
    og_site_name: str | None = None
    twitter_card: str | None = None
    twitter_title: str | None = None
    twitter_description: str | None = None
    twitter_image: str | None = None


_SEO_DEFAULTS = SEOConfig().model_dump()


# ==================== SEO ENDPOINTS ====================

SITEMAP_ROUTES = [
    {"loc": "/", "priority": "1.0", "changefreq": "weekly"},
    {"loc": "/caracteristicas", "priority": "0.8", "changefreq": "monthly"},
    {"loc": "/precios", "priority": "0.9", "changefreq": "weekly"},
    {"loc": "/nosotros", "priority": "0.6", "changefreq": "monthly"},
    {"loc": "/contacto", "priority": "0.7", "changefreq": "monthly"},
    {"loc": "/blog", "priority": "0.7", "changefreq": "weekly"},
    {"loc": "/privacidad", "priority": "0.3", "changefreq": "yearly"},
    {"loc": "/terminos", "priority": "0.3", "changefreq": "yearly"},
]


@sub_router.get("/admin/seo")
async def get_seo_config(user: dict = Depends(get_superadmin_user)):
    """Get SEO configuration"""
    config = await db.app_config.find_one({"type": "seo"})
    if not config:
        return _SEO_DEFAULTS
    config.pop("_id", None)
    config.pop("type", None)
    config.pop("updated_at", None)
    config.pop("updated_by", None)
    return config


@sub_router.put("/admin/seo")
async def update_seo_config(data: SEOConfigUpdate, user: dict = Depends(get_superadmin_user)):
    """Update SEO configuration"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    for key in list(update_data.keys()):
        if isinstance(update_data[key], str):
            update_data[key] = sanitize_string(update_data[key])
    update_data["updated_at"] = datetime.now(UTC).isoformat()
    update_data["updated_by"] = user["id"]

    await db.app_config.update_one(
        {"type": "seo"},
        {"$set": update_data},
        upsert=True
    )

    config = await db.app_config.find_one({"type": "seo"})
    config.pop("_id", None)
    config.pop("type", None)
    logger.info(f"SEO config updated by {user.get('email')}")
    return {"success": True, "config": config}


@sub_router.get("/seo/public")
async def get_public_seo():
    """Get public SEO configuration (no auth required)"""
    try:
        config = await db.app_config.find_one({"type": "seo"})
    except Exception:
        logger.warning("No se pudo leer la configuración SEO de la BD")
        return _SEO_DEFAULTS

    if not config:
        return _SEO_DEFAULTS
    config.pop("_id", None)
    config.pop("type", None)
    config.pop("updated_at", None)
    config.pop("updated_by", None)
    return config


@sub_router.get("/seo/sitemap.xml")
async def get_sitemap():
    """Generate and serve sitemap.xml (public, no auth required)"""
    try:
        config = await db.app_config.find_one({"type": "seo"})
    except Exception:
        config = None

    site_url = config.get("site_url", "https://sync-stock.com").rstrip("/") if config else "https://sync-stock.com"

    lastmod = datetime.now(UTC).strftime("%Y-%m-%d")

    urls_xml = ""
    for route in SITEMAP_ROUTES:
        urls_xml += f"""  <url>
    <loc>{site_url}{route['loc']}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{route['changefreq']}</changefreq>
    <priority>{route['priority']}</priority>
  </url>\n"""

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}</urlset>"""

    return Response(content=sitemap_xml, media_type="application/xml")
