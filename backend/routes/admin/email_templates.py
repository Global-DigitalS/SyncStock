"""
Rutas de plantillas de email y presets de tema para SuperAdmin.
"""
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.auth import get_superadmin_user
from services.database import db

from .branding import BrandingConfig

sub_router = APIRouter()


# ==================== EMAIL TEMPLATE MODELS ====================

class EmailTemplateCreate(BaseModel):
    name: str
    key: str  # welcome, password_reset, subscription_change, etc.
    subject: str
    html_content: str
    text_content: str | None = None
    variables: list[str] = []  # Available variables: {name}, {email}, {link}, etc.
    is_active: bool = True

class EmailTemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    html_content: str | None = None
    text_content: str | None = None
    variables: list[str] | None = None
    is_active: bool | None = None


# ==================== DEFAULT TEMPLATES ====================

DEFAULT_TEMPLATES = [
    {
        "key": "welcome",
        "name": "Bienvenida",
        "subject": "\u00a1Bienvenido a {app_name}!",
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
        <h2 style="color: #1e293b;">\u00a1Hola {name}!</h2>
        <p style="color: #475569; line-height: 1.6;">
            Te damos la bienvenida a <strong>{app_name}</strong>. Tu cuenta ha sido creada correctamente.
        </p>
        <p style="color: #475569; line-height: 1.6;">
            Ya puedes empezar a gestionar tus cat\u00e1logos de productos y sincronizarlos con tus tiendas online.
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
        "name": "Recuperar Contrase\u00f1a",
        "subject": "Restablecer contrase\u00f1a - {app_name}",
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
        <h2 style="color: #1e293b;">Restablecer contrase\u00f1a</h2>
        <p style="color: #475569; line-height: 1.6;">
            Hola {name}, hemos recibido una solicitud para restablecer tu contrase\u00f1a.
        </p>
        <p style="color: #475569; line-height: 1.6;">
            Haz clic en el siguiente bot\u00f3n para crear una nueva contrase\u00f1a:
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background: {primary_color}; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; display: inline-block;">
                Restablecer contrase\u00f1a
            </a>
        </div>
        <p style="color: #94a3b8; font-size: 14px;">
            Este enlace expirar\u00e1 en 1 hora. Si no solicitaste este cambio, ignora este correo.
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
        "name": "Cambio de Suscripci\u00f3n",
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
        <h2 style="color: #1e293b;">Cambio de suscripci\u00f3n</h2>
        <p style="color: #475569; line-height: 1.6;">
            Hola {name}, tu plan de suscripci\u00f3n ha sido actualizado.
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


# ==================== EMAIL TEMPLATES ENDPOINTS ====================

@sub_router.get("/admin/email-templates")
async def get_email_templates(user: dict = Depends(get_superadmin_user)):
    """Get all email templates"""
    templates = await db.email_templates.find({}, {"_id": 0}).to_list(100)

    # If no templates exist, create defaults
    if not templates:
        now = datetime.now(UTC).isoformat()
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


@sub_router.get("/admin/email-templates/{template_id}")
async def get_email_template(template_id: str, user: dict = Depends(get_superadmin_user)):
    """Get a specific email template"""
    template = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@sub_router.put("/admin/email-templates/{template_id}")
async def update_email_template(template_id: str, data: EmailTemplateUpdate, user: dict = Depends(get_superadmin_user)):
    """Update an email template"""
    existing = await db.email_templates.find_one({"id": template_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(UTC).isoformat()
    update_data["updated_by"] = user["id"]

    await db.email_templates.update_one({"id": template_id}, {"$set": update_data})

    template = await db.email_templates.find_one({"id": template_id}, {"_id": 0})
    return {"success": True, "template": template}


@sub_router.post("/admin/email-templates")
async def create_email_template(data: EmailTemplateCreate, user: dict = Depends(get_superadmin_user)):
    """Create a new email template"""
    # Check if key already exists
    existing = await db.email_templates.find_one({"key": data.key})
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe una plantilla con la clave '{data.key}'")

    template_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    template = {
        "id": template_id,
        **data.model_dump(),
        "created_at": now,
        "created_by": user["id"]
    }

    await db.email_templates.insert_one(template)
    template.pop("_id", None)

    return {"success": True, "template": template}


@sub_router.delete("/admin/email-templates/{template_id}")
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


@sub_router.post("/admin/email-templates/{template_id}/preview")
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
        "app_name": branding.get("app_name", "SyncStock"),
        "app_url": "https://app.ejemplo.com",
        "primary_color": branding.get("primary_color", "#4f46e5"),
        "footer_text": branding.get("footer_text", ""),
        "reset_link": "https://app.ejemplo.com/reset-password?token=ejemplo",
        "old_plan": "Plan B\u00e1sico",
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


@sub_router.post("/admin/email-templates/reset-defaults")
async def reset_default_templates(user: dict = Depends(get_superadmin_user)):
    """Reset default templates to their original content"""
    now = datetime.now(UTC).isoformat()

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
        "name": "Indigo (Predeterminado)",
        "primary_color": "#4f46e5",
        "secondary_color": "#0f172a",
        "accent_color": "#10b981"
    },
    "ocean": {
        "name": "Oc\u00e9ano",
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

@sub_router.get("/admin/theme-presets")
async def get_theme_presets(user: dict = Depends(get_superadmin_user)):
    """Get available theme presets"""
    return THEME_PRESETS


@sub_router.post("/admin/branding/apply-preset/{preset_key}")
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
            "updated_at": datetime.now(UTC).isoformat()
        }},
        upsert=True
    )

    config = await db.app_config.find_one({"type": "branding"})
    config.pop("_id", None)
    return {"success": True, "branding": config}
