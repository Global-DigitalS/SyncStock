"""
Rutas de administración para SuperAdmin.
Gestión de branding, planes de suscripción y plantillas de email.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import base64
import logging

from services.auth import get_superadmin_user
from services.database import db
from services.sanitizer import sanitize_string, sanitize_dict, sanitize_url

router = APIRouter()
logger = logging.getLogger(__name__)

# Use relative path from backend directory for uploads
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#4f46e5"  # indigo-600
    secondary_color: str = "#0f172a"  # slate-900
    accent_color: str = "#10b981"  # emerald-500
    footer_text: str = ""
    theme_preset: str = "default"
    # Hero section for login/register
    hero_image_url: Optional[str] = None
    hero_title: str = "Gestiona tu inventario de forma inteligente"
    hero_subtitle: str = "Sincroniza proveedores, configura márgenes y exporta a tu tienda online en minutos."
    # Page title (browser tab)
    page_title: str = "SyncStock — Sincronización de Inventario B2B Automatizada"

class BrandingConfigUpdate(BaseModel):
    app_name: Optional[str] = None
    app_slogan: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    footer_text: Optional[str] = None
    theme_preset: Optional[str] = None
    # Hero section for login/register
    hero_image_url: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    # Page title (browser tab)
    page_title: Optional[str] = None


# ==================== SUBSCRIPTION PLAN MODELS ====================

class SubscriptionPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    max_suppliers: int = 5
    max_catalogs: int = 3
    max_products: int = 1000
    max_stores: int = 1
    max_crm_connections: int = 1
    price_monthly: float = 0
    price_yearly: float = 0
    trial_days: int = 0
    features: List[str] = []
    is_default: bool = False
    sort_order: int = 0
    # Unified Auto-Sync options (for Suppliers, Stores, CRM)
    auto_sync_enabled: bool = False
    sync_intervals: List[int] = []
    # Legacy CRM-only Auto-Sync options (for backwards compatibility)
    crm_sync_enabled: bool = False
    crm_sync_intervals: List[int] = []

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_suppliers: Optional[int] = None
    max_catalogs: Optional[int] = None
    max_products: Optional[int] = None
    max_stores: Optional[int] = None
    max_crm_connections: Optional[int] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    trial_days: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    sort_order: Optional[int] = None
    # Unified Auto-Sync options (for Suppliers, Stores, CRM)
    auto_sync_enabled: Optional[bool] = None
    sync_intervals: Optional[List[int]] = None
    # Legacy CRM-only Auto-Sync options (for backwards compatibility)
    crm_sync_enabled: Optional[bool] = None
    crm_sync_intervals: Optional[List[int]] = None


# ==================== EMAIL TEMPLATE MODELS ====================

class EmailTemplateCreate(BaseModel):
    name: str
    key: str  # welcome, password_reset, subscription_change, etc.
    subject: str
    html_content: str
    text_content: Optional[str] = None
    variables: List[str] = []  # Available variables: {name}, {email}, {link}, etc.
    is_active: bool = True

class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None


# ==================== BRANDING ENDPOINTS ====================

@router.get("/admin/branding")
async def get_branding(user: dict = Depends(get_superadmin_user)):
    """Get current branding configuration"""
    config = await db.app_config.find_one({"type": "branding"})
    if not config:
        return BrandingConfig().model_dump()
    config.pop("_id", None)
    config.pop("type", None)
    return config


@router.put("/admin/branding")
async def update_branding(data: BrandingConfigUpdate, user: dict = Depends(get_superadmin_user)):
    """Update branding configuration"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
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


@router.post("/admin/branding/upload-logo")
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
        {"$set": {"logo_url": logo_url, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"success": True, "logo_url": logo_url}


@router.post("/admin/branding/upload-favicon")
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
        {"$set": {"favicon_url": favicon_url, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"success": True, "favicon_url": favicon_url}


@router.post("/admin/branding/upload-hero")
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
        {"$set": {"hero_image_url": hero_image_url, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"success": True, "hero_image_url": hero_image_url}


# ==================== PUBLIC BRANDING ENDPOINT (NO AUTH) ====================

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


@router.get("/admin/icons")
async def get_icons(user: dict = Depends(get_superadmin_user)):
    """Get all custom icons configuration"""
    config = await db.app_config.find_one({"type": "icons"})
    if not config:
        return {"icons": {}}
    config.pop("_id", None)
    config.pop("type", None)
    return config


@router.post("/admin/icons/upload/{icon_key}")
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
        {"$set": {f"icons.{icon_key}": icon_url, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

    return {"success": True, "icon_url": icon_url, "icon_key": icon_key}


@router.delete("/admin/icons/{icon_key}")
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
        {"$unset": {f"icons.{icon_key}": ""}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

    return {"success": True, "icon_key": icon_key}


@router.get("/icons/public")
async def get_public_icons():
    """Get all custom icons (no auth required)"""
    config = await db.app_config.find_one({"type": "icons"})
    if not config:
        return {"icons": {}}
    return {"icons": config.get("icons", {})}


@router.get("/branding/public")
async def get_public_branding():
    """Get public branding configuration (no auth required)"""
    config = await db.app_config.find_one({"type": "branding"})
    if not config:
        return BrandingConfig().model_dump()
    
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


# ==================== LANDING PAGE CONTENT ====================

@router.get("/landing/content")
async def get_landing_content():
    """Get landing page content (public endpoint)"""
    content = await db.app_config.find_one({"type": "landing_content"})
    
    # Default content if not configured
    default_content = {
        "hero": {
            "title": "Sincroniza tu inventario con un clic",
            "subtitle": "Conecta proveedores, gestiona catálogos y actualiza tus tiendas online automáticamente. Ahorra horas de trabajo manual cada semana.",
            "cta_primary": "Empezar Gratis",
            "cta_secondary": "Ver Demo",
            "image_url": None
        },
        "features": [
            {
                "icon": "Zap",
                "title": "Sincronización Automática",
                "description": "Actualiza precios, stock y productos en todas tus tiendas sin mover un dedo."
            },
            {
                "icon": "Database",
                "title": "Multi-Proveedor",
                "description": "Importa catálogos de múltiples proveedores en diferentes formatos (CSV, Excel, XML)."
            },
            {
                "icon": "Store",
                "title": "Multi-Tienda",
                "description": "Gestiona WooCommerce, PrestaShop, Shopify y más desde un solo panel."
            },
            {
                "icon": "Calculator",
                "title": "Márgenes Inteligentes",
                "description": "Configura reglas de precios por categoría, proveedor o producto individual."
            },
            {
                "icon": "RefreshCw",
                "title": "CRM Integrado",
                "description": "Sincroniza con Dolibarr y otros ERPs para mantener todo actualizado."
            },
            {
                "icon": "Shield",
                "title": "Datos Seguros",
                "description": "Encriptación de extremo a extremo y backups automáticos diarios."
            }
        ],
        "benefits": {
            "title": "¿Por qué elegir SyncStock?",
            "items": [
                {"stat": "80%", "text": "Menos tiempo en gestión de inventario"},
                {"stat": "0", "text": "Errores de sincronización manual"},
                {"stat": "24/7", "text": "Actualización automática disponible"},
                {"stat": "+500", "text": "Negocios ya confían en nosotros"}
            ]
        },
        "testimonials": [
            {
                "quote": "SyncStock nos ha ahorrado más de 20 horas semanales en gestión de catálogos.",
                "author": "María García",
                "role": "CEO, TechStore",
                "avatar": None
            },
            {
                "quote": "La sincronización con nuestro ERP funciona perfectamente. Muy recomendable.",
                "author": "Carlos López",
                "role": "Director de Operaciones, Distribuciones López",
                "avatar": None
            }
        ],
        "faq": [
            {
                "question": "¿Cuánto tiempo tarda la configuración inicial?",
                "answer": "La mayoría de usuarios están operativos en menos de 15 minutos. Solo necesitas conectar tus proveedores y tiendas."
            },
            {
                "question": "¿Puedo probar antes de pagar?",
                "answer": "¡Por supuesto! Ofrecemos 14 días de prueba gratuita con todas las funciones premium."
            },
            {
                "question": "¿Qué pasa si supero los límites de mi plan?",
                "answer": "Te avisaremos antes de llegar al límite y podrás actualizar tu plan en cualquier momento."
            },
            {
                "question": "¿Ofrecen soporte técnico?",
                "answer": "Sí, todos los planes incluyen soporte por email. Los planes Professional y Enterprise incluyen soporte prioritario 24/7."
            }
        ],
        "cta_final": {
            "title": "¿Listo para automatizar tu negocio?",
            "subtitle": "Únete a cientos de empresas que ya optimizan su gestión de inventario",
            "button_text": "Comenzar Prueba Gratuita"
        },
        "footer": {
            "company_description": "SyncStock es la plataforma líder en sincronización de inventarios para eCommerce.",
            "links": [
                {"label": "Términos", "url": "/terms"},
                {"label": "Privacidad", "url": "/privacy"},
                {"label": "Contacto", "url": "/contact"}
            ],
            "social": {
                "twitter": "",
                "linkedin": "",
                "facebook": ""
            }
        }
    }
    
    if not content:
        return default_content
    
    # Merge with defaults to ensure all fields exist
    result = default_content.copy()
    for key in default_content.keys():
        if key in content and content[key]:
            result[key] = content[key]
    
    return result


@router.put("/admin/landing/content")
async def update_landing_content(data: dict, user: dict = Depends(get_superadmin_user)):
    """Update landing page content"""
    data["type"] = "landing_content"
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.app_config.update_one(
        {"type": "landing_content"},
        {"$set": data},
        upsert=True
    )
    
    return {"success": True, "message": "Contenido actualizado"}


@router.get("/admin/landing/content")
async def get_admin_landing_content(user: dict = Depends(get_superadmin_user)):
    """Get landing page content for admin editing"""
    content = await db.app_config.find_one({"type": "landing_content"}, {"_id": 0})
    return content or {}


# ==================== SUBSCRIPTION PLANS ENDPOINTS ====================

@router.get("/admin/plans")
async def get_plans(user: dict = Depends(get_superadmin_user)):
    """Get all subscription plans"""
    plans = await db.subscription_plans.find({}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return plans


@router.post("/admin/plans")
async def create_plan(data: SubscriptionPlanCreate, user: dict = Depends(get_superadmin_user)):
    """Create a new subscription plan"""
    plan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # If this is the default plan, unset others
    if data.is_default:
        await db.subscription_plans.update_many({}, {"$set": {"is_default": False}})
    
    plan = {
        "id": plan_id,
        **data.model_dump(),
        "is_active": True,
        "created_at": now,
        "created_by": user["id"]
    }
    
    await db.subscription_plans.insert_one(plan)
    plan.pop("_id", None)
    
    return {"success": True, "plan": plan}


@router.put("/admin/plans/{plan_id}")
async def update_plan(plan_id: str, data: SubscriptionPlanUpdate, user: dict = Depends(get_superadmin_user)):
    """Update a subscription plan"""
    existing = await db.subscription_plans.find_one({"id": plan_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # If setting as default, unset others
    if data.is_default:
        await db.subscription_plans.update_many(
            {"id": {"$ne": plan_id}},
            {"$set": {"is_default": False}}
        )
    
    await db.subscription_plans.update_one({"id": plan_id}, {"$set": update_data})
    
    plan = await db.subscription_plans.find_one({"id": plan_id}, {"_id": 0})
    return {"success": True, "plan": plan}


@router.delete("/admin/plans/{plan_id}")
async def delete_plan(plan_id: str, user: dict = Depends(get_superadmin_user)):
    """Delete a subscription plan"""
    existing = await db.subscription_plans.find_one({"id": plan_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Check if any users are on this plan
    users_on_plan = await db.users.count_documents({"plan_id": plan_id})
    if users_on_plan > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar: {users_on_plan} usuario(s) tienen este plan asignado"
        )
    
    await db.subscription_plans.delete_one({"id": plan_id})
    return {"success": True, "message": "Plan eliminado"}


# ==================== EMAIL TEMPLATES ENDPOINTS ====================

DEFAULT_TEMPLATES = [
    {
        "key": "welcome",
        "name": "Bienvenida",
        "subject": "¡Bienvenido a {app_name}!",
        "variables": ["name", "email", "app_name", "app_url"],
        "html_content": """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f5; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden;">
    <div style="background: {primary_color}; padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{app_name}</h1>
    </div>
    <div style="padding: 30px;">
        <h2 style="color: #1e293b;">¡Hola {name}!</h2>
        <p style="color: #475569; line-height: 1.6;">
            Te damos la bienvenida a <strong>{app_name}</strong>. Tu cuenta ha sido creada correctamente.
        </p>
        <p style="color: #475569; line-height: 1.6;">
            Ya puedes empezar a gestionar tus catálogos de productos y sincronizarlos con tus tiendas online.
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{app_url}" style="background: {primary_color}; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; display: inline-block;">
                Acceder a mi cuenta
            </a>
        </div>
    </div>
    <div style="background: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 12px;">
        {footer_text}
    </div>
</div>
</body>
</html>
"""
    },
    {
        "key": "password_reset",
        "name": "Recuperar Contraseña",
        "subject": "Restablecer contraseña - {app_name}",
        "variables": ["name", "reset_link", "app_name", "app_url"],
        "html_content": """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f5; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden;">
    <div style="background: {primary_color}; padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{app_name}</h1>
    </div>
    <div style="padding: 30px;">
        <h2 style="color: #1e293b;">Restablecer contraseña</h2>
        <p style="color: #475569; line-height: 1.6;">
            Hola {name}, hemos recibido una solicitud para restablecer tu contraseña.
        </p>
        <p style="color: #475569; line-height: 1.6;">
            Haz clic en el siguiente botón para crear una nueva contraseña:
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background: {primary_color}; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; display: inline-block;">
                Restablecer contraseña
            </a>
        </div>
        <p style="color: #94a3b8; font-size: 14px;">
            Este enlace expirará en 1 hora. Si no solicitaste este cambio, ignora este correo.
        </p>
    </div>
    <div style="background: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 12px;">
        {footer_text}
    </div>
</div>
</body>
</html>
"""
    },
    {
        "key": "subscription_change",
        "name": "Cambio de Suscripción",
        "subject": "Cambio de plan - {app_name}",
        "variables": ["name", "old_plan", "new_plan", "app_name", "app_url"],
        "html_content": """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f5; padding: 20px;">
<div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden;">
    <div style="background: {primary_color}; padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{app_name}</h1>
    </div>
    <div style="padding: 30px;">
        <h2 style="color: #1e293b;">Cambio de suscripción</h2>
        <p style="color: #475569; line-height: 1.6;">
            Hola {name}, tu plan de suscripción ha sido actualizado.
        </p>
        <div style="background: #f1f5f9; border-radius: 8px; padding: 20px; margin: 20px 0;">
            <p style="margin: 0 0 10px 0;"><strong>Plan anterior:</strong> {old_plan}</p>
            <p style="margin: 0;"><strong>Nuevo plan:</strong> {new_plan}</p>
        </div>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{app_url}" style="background: {primary_color}; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; display: inline-block;">
                Ver mi cuenta
            </a>
        </div>
    </div>
    <div style="background: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 12px;">
        {footer_text}
    </div>
</div>
</body>
</html>
"""
    }
]


@router.get("/admin/email-templates")
async def get_email_templates(user: dict = Depends(get_superadmin_user)):
    """Get all email templates"""
    templates = await db.email_templates.find({}, {"_id": 0}).to_list(100)
    
    # If no templates exist, create defaults
    if not templates:
        now = datetime.now(timezone.utc).isoformat()
        for tpl in DEFAULT_TEMPLATES:
            template = {
                "id": str(uuid.uuid4()),
                **tpl,
                "is_active": True,
                "created_at": now
            }
            await db.email_templates.insert_one(template)
        templates = await db.email_templates.find({}, {"_id": 0}).to_list(100)
    
    return templates


@router.get("/admin/email-templates/{template_id}")
async def get_email_template(template_id: str, user: dict = Depends(get_superadmin_user)):
    """Get a specific email template"""
    template = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@router.put("/admin/email-templates/{template_id}")
async def update_email_template(template_id: str, data: EmailTemplateUpdate, user: dict = Depends(get_superadmin_user)):
    """Update an email template"""
    existing = await db.email_templates.find_one({"id": template_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user["id"]
    
    await db.email_templates.update_one({"id": template_id}, {"$set": update_data})
    
    template = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
    return {"success": True, "template": template}


@router.post("/admin/email-templates")
async def create_email_template(data: EmailTemplateCreate, user: dict = Depends(get_superadmin_user)):
    """Create a new email template"""
    # Check if key already exists
    existing = await db.email_templates.find_one({"key": data.key})
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe una plantilla con la clave '{data.key}'")
    
    template_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    template = {
        "id": template_id,
        **data.model_dump(),
        "created_at": now,
        "created_by": user["id"]
    }
    
    await db.email_templates.insert_one(template)
    template.pop("_id", None)
    
    return {"success": True, "template": template}


@router.delete("/admin/email-templates/{template_id}")
async def delete_email_template(template_id: str, user: dict = Depends(get_superadmin_user)):
    """Delete an email template"""
    existing = await db.email_templates.find_one({"id": template_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    # Don't allow deleting default templates
    if existing.get("key") in ["welcome", "password_reset", "subscription_change"]:
        raise HTTPException(status_code=400, detail="No se pueden eliminar las plantillas predeterminadas")
    
    await db.email_templates.delete_one({"id": template_id})
    return {"success": True, "message": "Plantilla eliminada"}


@router.post("/admin/email-templates/{template_id}/preview")
async def preview_email_template(template_id: str, user: dict = Depends(get_superadmin_user)):
    """Get a preview of an email template with sample data"""
    template = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    # Get branding for preview
    branding = await db.app_config.find_one({"type": "branding"})
    if not branding:
        branding = BrandingConfig().model_dump()
    
    # Sample data for preview
    sample_data = {
        "name": "Usuario de Ejemplo",
        "email": "usuario@ejemplo.com",
        "app_name": branding.get("app_name", "StockHub"),
        "app_url": "https://app.ejemplo.com",
        "primary_color": branding.get("primary_color", "#4f46e5"),
        "footer_text": branding.get("footer_text", ""),
        "reset_link": "https://app.ejemplo.com/reset-password?token=ejemplo",
        "old_plan": "Plan Básico",
        "new_plan": "Plan Pro"
    }
    
    # Replace variables in template
    html = template.get("html_content", "")
    subject = template.get("subject", "")
    
    from html import escape as _html_escape
    for key, value in sample_data.items():
        # Escape HTML in values injected into templates to prevent stored XSS (OWASP A03)
        safe_value = _html_escape(str(value))
        html = html.replace(f"{{{key}}}", safe_value)
        subject = subject.replace(f"{{{key}}}", safe_value)
    
    return {
        "subject": subject,
        "html": html,
        "template_name": template.get("name")
    }


@router.post("/admin/email-templates/reset-defaults")
async def reset_default_templates(user: dict = Depends(get_superadmin_user)):
    """Reset default templates to their original content"""
    now = datetime.now(timezone.utc).isoformat()
    
    for tpl in DEFAULT_TEMPLATES:
        await db.email_templates.update_one(
            {"key": tpl["key"]},
            {"$set": {
                "name": tpl["name"],
                "subject": tpl["subject"],
                "html_content": tpl["html_content"],
                "variables": tpl["variables"],
                "updated_at": now,
                "updated_by": user["id"]
            }},
            upsert=True
        )
    
    return {"success": True, "message": "Plantillas restablecidas a valores predeterminados"}


# ==================== THEME PRESETS ====================

THEME_PRESETS = {
    "default": {
        "name": "Índigo (Predeterminado)",
        "primary_color": "#4f46e5",
        "secondary_color": "#0f172a",
        "accent_color": "#10b981"
    },
    "ocean": {
        "name": "Océano",
        "primary_color": "#0891b2",
        "secondary_color": "#164e63",
        "accent_color": "#06b6d4"
    },
    "forest": {
        "name": "Bosque",
        "primary_color": "#059669",
        "secondary_color": "#064e3b",
        "accent_color": "#10b981"
    },
    "sunset": {
        "name": "Atardecer",
        "primary_color": "#ea580c",
        "secondary_color": "#7c2d12",
        "accent_color": "#f59e0b"
    },
    "royal": {
        "name": "Real",
        "primary_color": "#7c3aed",
        "secondary_color": "#4c1d95",
        "accent_color": "#a78bfa"
    },
    "slate": {
        "name": "Pizarra",
        "primary_color": "#475569",
        "secondary_color": "#1e293b",
        "accent_color": "#64748b"
    },
    "rose": {
        "name": "Rosa",
        "primary_color": "#e11d48",
        "secondary_color": "#881337",
        "accent_color": "#fb7185"
    }
}

@router.get("/admin/theme-presets")
async def get_theme_presets(user: dict = Depends(get_superadmin_user)):
    """Get available theme presets"""
    return THEME_PRESETS


@router.post("/admin/branding/apply-preset/{preset_key}")
async def apply_theme_preset(preset_key: str, user: dict = Depends(get_superadmin_user)):
    """Apply a theme preset to branding"""
    if preset_key not in THEME_PRESETS:
        raise HTTPException(status_code=404, detail="Tema no encontrado")
    
    preset = THEME_PRESETS[preset_key]
    
    await db.app_config.update_one(
        {"type": "branding"},
        {"$set": {
            "primary_color": preset["primary_color"],
            "secondary_color": preset["secondary_color"],
            "accent_color": preset["accent_color"],
            "theme_preset": preset_key,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    config = await db.app_config.find_one({"type": "branding"})
    config.pop("_id", None)
    config.pop("type", None)
    return {"success": True, "branding": config}


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
    analytics_enabled: Optional[bool] = None
    analytics_measurement_id: Optional[str] = None
    analytics_api_secret: Optional[str] = None
    # Google Search Console
    search_console_enabled: Optional[bool] = None
    search_console_property_url: Optional[str] = None
    search_console_verification_code: Optional[str] = None
    # Google Tag Manager
    tag_manager_enabled: Optional[bool] = None
    tag_manager_container_id: Optional[str] = None
    # Google Ads
    google_ads_enabled: Optional[bool] = None
    google_ads_conversion_id: Optional[str] = None
    google_ads_conversion_label: Optional[str] = None


# ==================== GOOGLE SERVICES ENDPOINTS ====================

@router.get("/admin/google-services")
async def get_google_services(user: dict = Depends(get_superadmin_user)):
    """Get Google services configuration"""
    config = await db.app_config.find_one({"type": "google_services"})
    if not config:
        return GoogleServicesConfig().model_dump()
    config.pop("_id", None)
    config.pop("type", None)
    config.pop("updated_at", None)
    config.pop("updated_by", None)
    return config


@router.put("/admin/google-services")
async def update_google_services(data: GoogleServicesConfigUpdate, user: dict = Depends(get_superadmin_user)):
    """Update Google services configuration"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    # Sanitize string fields
    for key in list(update_data.keys()):
        if isinstance(update_data[key], str):
            update_data[key] = sanitize_string(update_data[key])

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
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


@router.get("/google-services/public")
async def get_public_google_services():
    """Get public Google services configuration (no auth required).
    Returns only the IDs/codes needed for frontend tracking scripts."""
    config = await db.app_config.find_one({"type": "google_services"})
    if not config:
        return GoogleServicesConfig().model_dump()

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


# ==================== SYSTEM RESET ====================

class ResetConfirmation(BaseModel):
    confirmation_text: str = Field(..., description="Debe ser 'RESET' para confirmar")

@router.post("/admin/system/reset")
async def reset_application(confirmation: ResetConfirmation, user: dict = Depends(get_superadmin_user)):
    """
    Reset the entire application, deleting all data EXCEPT users.
    Requires confirmation_text = "RESET" to execute.
    """
    if confirmation.confirmation_text != "RESET":
        raise HTTPException(
            status_code=400, 
            detail="Confirmación incorrecta. Escriba 'RESET' para confirmar."
        )
    
    try:
        # List of collections to preserve (users-related)
        preserved_collections = ["users"]
        
        # Get all collection names
        database = db.client.get_database(db.name)
        all_collections = await database.list_collection_names()
        
        deleted_stats = {}
        
        for collection_name in all_collections:
            if collection_name in preserved_collections:
                # Count but don't delete users
                count = await database[collection_name].count_documents({})
                deleted_stats[collection_name] = {"preserved": True, "count": count}
                continue
            
            # Count documents before deletion
            count = await database[collection_name].count_documents({})
            
            # Delete all documents in this collection
            if count > 0:
                result = await database[collection_name].delete_many({})
                deleted_stats[collection_name] = {
                    "deleted": result.deleted_count,
                    "preserved": False
                }
            else:
                deleted_stats[collection_name] = {"deleted": 0, "preserved": False}
        
        logger.warning(f"SYSTEM RESET executed by SuperAdmin {user.get('email')} - Stats: {deleted_stats}")
        
        return {
            "success": True,
            "message": "Aplicación reiniciada correctamente. Todos los datos han sido eliminados excepto los usuarios.",
            "stats": deleted_stats,
            "executed_by": user.get("email"),
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during system reset: {e}")
        raise HTTPException(status_code=500, detail=f"Error al reiniciar la aplicación: {str(e)}")
