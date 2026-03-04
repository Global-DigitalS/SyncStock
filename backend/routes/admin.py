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

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==================== BRANDING MODELS ====================

class BrandingConfig(BaseModel):
    app_name: str = "StockHub"
    app_slogan: str = "Gestión de Catálogos"
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#4f46e5"  # indigo-600
    secondary_color: str = "#0f172a"  # slate-900
    accent_color: str = "#10b981"  # emerald-500
    footer_text: str = ""
    theme_preset: str = "default"

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


# ==================== SUBSCRIPTION PLAN MODELS ====================

class SubscriptionPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    max_suppliers: int = 5
    max_catalogs: int = 3
    max_products: int = 1000
    max_stores: int = 1
    price_monthly: float = 0
    price_yearly: float = 0
    features: List[str] = []
    is_default: bool = False
    sort_order: int = 0

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_suppliers: Optional[int] = None
    max_catalogs: Optional[int] = None
    max_products: Optional[int] = None
    max_stores: Optional[int] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    sort_order: Optional[int] = None


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
    
    logo_url = f"/uploads/{filename}"
    
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
    
    favicon_url = f"/uploads/{filename}"
    
    await db.app_config.update_one(
        {"type": "branding"},
        {"$set": {"favicon_url": favicon_url, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"success": True, "favicon_url": favicon_url}


# ==================== PUBLIC BRANDING ENDPOINT (NO AUTH) ====================

@router.get("/branding/public")
async def get_public_branding():
    """Get public branding configuration (no auth required)"""
    config = await db.app_config.find_one({"type": "branding"})
    if not config:
        return BrandingConfig().model_dump()
    
    # Return only public fields
    return {
        "app_name": config.get("app_name", "StockHub"),
        "app_slogan": config.get("app_slogan", "Gestión de Catálogos"),
        "logo_url": config.get("logo_url"),
        "favicon_url": config.get("favicon_url"),
        "primary_color": config.get("primary_color", "#4f46e5"),
        "secondary_color": config.get("secondary_color", "#0f172a"),
        "accent_color": config.get("accent_color", "#10b981"),
        "footer_text": config.get("footer_text", ""),
        "theme_preset": config.get("theme_preset", "default")
    }


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
    
    for key, value in sample_data.items():
        html = html.replace(f"{{{key}}}", str(value))
        subject = subject.replace(f"{{{key}}}", str(value))
    
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
    return {"success": True, "branding": config}
