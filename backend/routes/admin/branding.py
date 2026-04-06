"""
Rutas de branding e iconos para SuperAdmin.
"""
import logging
import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from services.auth import get_superadmin_user
from services.database import db

sub_router = APIRouter()
logger = logging.getLogger(__name__)

# Use relative path from backend directory for uploads
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads")
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except PermissionError:
    # Fallback to /tmp if we can't create the uploads directory
    UPLOAD_DIR = "/tmp/syncstock_uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    logger.warning(f"Using fallback upload directory: {UPLOAD_DIR}")


# ==================== BRANDING MODELS ====================

class BrandingConfig(BaseModel):
    app_name: str = "SyncStock"
    app_slogan: str = "Sincronización de Inventario B2B"
    logo_url: str | None = None
    favicon_url: str | None = None
    primary_color: str = "#4f46e5"  # indigo-600
    secondary_color: str = "#0f172a"  # slate-900
    accent_color: str = "#10b981"  # emerald-500
    footer_text: str = ""
    theme_preset: str = "default"
    # Hero section for login/register
    hero_image_url: str | None = None
    hero_title: str = "Gestiona tu inventario de forma inteligente"
    hero_subtitle: str = "Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos."
    # Page title (browser tab)
    page_title: str = "SyncStock — Sincronización de Inventario B2B Automatizada"

class BrandingConfigUpdate(BaseModel):
    app_name: str | None = None
    app_slogan: str | None = None
    logo_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    accent_color: str | None = None
    footer_text: str | None = None
    theme_preset: str | None = None
    # Hero section for login/register
    hero_image_url: str | None = None
    hero_title: str | None = None
    hero_subtitle: str | None = None
    # Page title (browser tab)
    page_title: str | None = None


_BRANDING_DEFAULTS = BrandingConfig().model_dump()


# ==================== BRANDING ENDPOINTS ====================

@sub_router.get("/admin/branding")
async def get_branding(user: dict = Depends(get_superadmin_user)):
    """Get current branding configuration"""
    config = await db.app_config.find_one({"type": "branding"})
    if not config:
        return _BRANDING_DEFAULTS
    config.pop("_id", None)
    config.pop("type", None)
    return config


@sub_router.put("/admin/branding")
async def update_branding(data: BrandingConfigUpdate, user: dict = Depends(get_superadmin_user)):
    """Update branding configuration"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(UTC).isoformat()
    update_data["updated_by"] = user["id"]

    await db.app_config.update_one(
        {"type": "branding"},
        {"$set": update_data},
        upsert=True
    )

    config = await db.app_config.find_one({"type": "branding"})
    config.pop("_id", None)
    config.pop("type", None)
    return {"success": True, "branding": config}


@sub_router.post("/admin/branding/upload-logo")
async def upload_logo(file: UploadFile = File(...), user: dict = Depends(get_superadmin_user)):
    """Upload logo image"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"logo_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    logo_url = f"/api/uploads/{filename}"

    await db.app_config.update_one(
        {"type": "branding"},
        {"$set": {"logo_url": logo_url, "updated_at": datetime.now(UTC).isoformat()}},
        upsert=True
    )

    return {"success": True, "logo_url": logo_url}


@sub_router.post("/admin/branding/upload-favicon")
async def upload_favicon(file: UploadFile = File(...), user: dict = Depends(get_superadmin_user)):
    """Upload favicon image"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    ext = file.filename.split(".")[-1] if "." in file.filename else "ico"
    filename = f"favicon_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    favicon_url = f"/api/uploads/{filename}"

    await db.app_config.update_one(
        {"type": "branding"},
        {"$set": {"favicon_url": favicon_url, "updated_at": datetime.now(UTC).isoformat()}},
        upsert=True
    )

    return {"success": True, "favicon_url": favicon_url}


@sub_router.post("/admin/branding/upload-hero")
async def upload_hero_image(file: UploadFile = File(...), user: dict = Depends(get_superadmin_user)):
    """Upload hero background image for login/register pages"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"hero_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    hero_image_url = f"/api/uploads/{filename}"

    await db.app_config.update_one(
        {"type": "branding"},
        {"$set": {"hero_image_url": hero_image_url, "updated_at": datetime.now(UTC).isoformat()}},
        upsert=True
    )

    return {"success": True, "hero_image_url": hero_image_url}


# ==================== ICONS MANAGEMENT ====================

ICONS_DIR = os.path.join(UPLOAD_DIR, "icons")
try:
    os.makedirs(ICONS_DIR, exist_ok=True)
except PermissionError:
    ICONS_DIR = "/tmp/syncstock_uploads/icons"
    os.makedirs(ICONS_DIR, exist_ok=True)

VALID_ICON_KEYS = {
    # Suppliers
    "supplier_url", "supplier_ftp",
    # Stores
    "store_woocommerce", "store_prestashop", "store_shopify", "store_wix", "store_magento",
    # Marketplaces
    "marketplace_google_merchant", "marketplace_facebook_shops", "marketplace_amazon",
    "marketplace_el_corte_ingles", "marketplace_miravia", "marketplace_idealo",
    "marketplace_kelkoo", "marketplace_trovaprezzi", "marketplace_ebay",
    "marketplace_zalando", "marketplace_pricerunner", "marketplace_bing_shopping",
    # CRM
    "crm_dolibarr", "crm_odoo",
}


@sub_router.get("/admin/icons")
async def get_icons(user: dict = Depends(get_superadmin_user)):
    """Get all custom icons configuration"""
    config = await db.app_config.find_one({"type": "icons"})
    if not config:
        return {"icons": {}}
    config.pop("_id", None)
    config.pop("type", None)
    return config


@sub_router.post("/admin/icons/upload/{icon_key}")
async def upload_icon(
    icon_key: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_superadmin_user)
):
    """Upload a custom icon for a specific element"""
    if icon_key not in VALID_ICON_KEYS:
        raise HTTPException(status_code=400, detail=f"Clave de icono no válida: {icon_key}")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    content = await file.read()
    if len(content) > 500 * 1024:  # 500KB limit
        raise HTTPException(status_code=400, detail="El archivo no puede superar 500KB")

    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "png"
    if ext not in ("png", "svg", "webp", "jpg", "jpeg", "ico"):
        ext = "png"

    filename = f"{icon_key}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(ICONS_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    icon_url = f"/api/uploads/icons/{filename}"

    # Remove old icon file if it exists
    current = await db.app_config.find_one({"type": "icons"})
    if current and current.get("icons", {}).get(icon_key):
        old_url = current["icons"][icon_key]
        old_filename = old_url.split("/")[-1]
        old_filepath = os.path.join(ICONS_DIR, old_filename)
        if os.path.exists(old_filepath):
            try:
                os.remove(old_filepath)
            except OSError:
                pass

    await db.app_config.update_one(
        {"type": "icons"},
        {"$set": {f"icons.{icon_key}": icon_url, "updated_at": datetime.now(UTC).isoformat()}},
        upsert=True
    )

    return {"success": True, "icon_url": icon_url, "icon_key": icon_key}


@sub_router.delete("/admin/icons/{icon_key}")
async def delete_icon(icon_key: str, user: dict = Depends(get_superadmin_user)):
    """Remove a custom icon and restore default"""
    if icon_key not in VALID_ICON_KEYS:
        raise HTTPException(status_code=400, detail=f"Clave de icono no válida: {icon_key}")

    current = await db.app_config.find_one({"type": "icons"})
    if current and current.get("icons", {}).get(icon_key):
        old_url = current["icons"][icon_key]
        old_filename = old_url.split("/")[-1]
        old_filepath = os.path.join(ICONS_DIR, old_filename)
        if os.path.exists(old_filepath):
            try:
                os.remove(old_filepath)
            except OSError:
                pass

    await db.app_config.update_one(
        {"type": "icons"},
        {"$unset": {f"icons.{icon_key}": ""}, "$set": {"updated_at": datetime.now(UTC).isoformat()}},
        upsert=True
    )

    return {"success": True, "icon_key": icon_key}


@sub_router.get("/icons/public")
async def get_public_icons():
    """Get all custom icons (no auth required)"""
    try:
        config = await db.app_config.find_one({"type": "icons"})
    except Exception:
        logger.warning("No se pudo leer la configuración de iconos de la BD")
        return {"icons": {}}

    if not config:
        return {"icons": {}}
    return {"icons": config.get("icons", {})}


@sub_router.get("/branding/public")
async def get_public_branding():
    """Get public branding configuration (no auth required)"""
    try:
        config = await db.app_config.find_one({"type": "branding"})
    except Exception:
        logger.warning("No se pudo leer la configuración de branding de la BD")
        return _BRANDING_DEFAULTS

    if not config:
        return _BRANDING_DEFAULTS

    # Return only public fields
    return {
        "app_name": config.get("app_name", "SyncStock"),
        "app_slogan": config.get("app_slogan", "Sincronización de Inventario B2B"),
        "logo_url": config.get("logo_url"),
        "favicon_url": config.get("favicon_url"),
        "primary_color": config.get("primary_color", "#4f46e5"),
        "secondary_color": config.get("secondary_color", "#0f172a"),
        "accent_color": config.get("accent_color", "#10b981"),
        "footer_text": config.get("footer_text", ""),
        "theme_preset": config.get("theme_preset", "default"),
        # Hero section
        "hero_image_url": config.get("hero_image_url"),
        "hero_title": config.get("hero_title", "Gestiona tu inventario de forma inteligente"),
        "hero_subtitle": config.get("hero_subtitle", "Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos."),
        # Page title
        "page_title": config.get("page_title", "SyncStock — Sincronización de Inventario B2B Automatizada")
    }
