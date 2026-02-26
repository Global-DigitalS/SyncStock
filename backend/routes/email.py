"""
Rutas para configuración y envío de correos electrónicos.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging

from services.auth import get_current_user, get_superadmin_user, hash_password
from services.database import db
from services.config_manager import get_config, update_config
from services.email_service import (
    EmailService,
    get_email_service,
    get_welcome_email_template,
    get_password_reset_email_template,
    get_subscription_change_email_template
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class SmtpConfigRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_from_email: Optional[str] = ""
    smtp_from_name: Optional[str] = "SupplierSync Pro"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False


class SmtpTestRequest(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    test_email: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class SendTestEmailRequest(BaseModel):
    to_email: EmailStr
    template: str = "welcome"  # welcome, password_reset, subscription_change


# ==================== SMTP CONFIGURATION ====================

@router.get("/email/config")
async def get_email_config(user: dict = Depends(get_superadmin_user)):
    """Obtiene la configuración actual de email (sin contraseña)"""
    config = get_config()
    
    return {
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "smtp_user": config.smtp_user,
        "smtp_from_email": config.smtp_from_email,
        "smtp_from_name": config.smtp_from_name,
        "smtp_use_tls": config.smtp_use_tls,
        "smtp_use_ssl": config.smtp_use_ssl,
        "smtp_configured": config.smtp_configured,
        "has_password": bool(config.smtp_password)
    }


@router.post("/email/config")
async def save_email_config(req: SmtpConfigRequest, user: dict = Depends(require_superadmin)):
    """Guarda la configuración de email"""
    try:
        update_config(
            smtp_host=req.smtp_host,
            smtp_port=req.smtp_port,
            smtp_user=req.smtp_user,
            smtp_password=req.smtp_password,
            smtp_from_email=req.smtp_from_email or req.smtp_user,
            smtp_from_name=req.smtp_from_name,
            smtp_use_tls=req.smtp_use_tls,
            smtp_use_ssl=req.smtp_use_ssl,
            smtp_configured=True
        )
        
        return {
            "success": True,
            "message": "Configuración de email guardada correctamente"
        }
    except Exception as e:
        logger.error(f"Error saving email config: {e}")
        return {
            "success": False,
            "message": f"Error al guardar: {str(e)}"
        }


@router.post("/email/test-connection")
async def test_smtp_connection(req: SmtpTestRequest):
    """Prueba la conexión SMTP sin guardar la configuración"""
    email_service = EmailService({
        'smtp_host': req.smtp_host,
        'smtp_port': req.smtp_port,
        'smtp_user': req.smtp_user,
        'smtp_password': req.smtp_password,
        'smtp_use_tls': req.smtp_use_tls,
        'smtp_use_ssl': req.smtp_use_ssl,
    })
    
    result = email_service.test_connection()
    return result


@router.post("/email/send-test")
async def send_test_email(req: SendTestEmailRequest, user: dict = Depends(require_superadmin)):
    """Envía un correo de prueba"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        return {
            "success": False,
            "message": "El servicio de email no está configurado"
        }
    
    config = get_config()
    app_url = config.cors_origins.split(',')[0] if config.cors_origins != '*' else 'https://app.example.com'
    
    # Seleccionar template
    if req.template == "welcome":
        template = get_welcome_email_template("Usuario de Prueba", app_url)
    elif req.template == "password_reset":
        template = get_password_reset_email_template(
            "Usuario de Prueba",
            f"{app_url}/reset-password?token=test-token-123",
            app_url
        )
    elif req.template == "subscription_change":
        template = get_subscription_change_email_template(
            "Usuario de Prueba",
            "Plan Básico",
            "Plan Profesional",
            app_url
        )
    else:
        return {"success": False, "message": "Template no válido"}
    
    result = email_service.send_email(
        to_email=req.to_email,
        subject=f"[PRUEBA] {template['subject']}",
        html_content=template['html'],
        text_content=template['text']
    )
    
    return result


# ==================== PASSWORD RESET ====================

@router.post("/auth/forgot-password")
async def forgot_password(req: PasswordResetRequest):
    """Solicita un enlace para restablecer contraseña"""
    # Buscar usuario
    user = await db.users.find_one({"email": req.email})
    
    # Siempre devolver éxito para no revelar si el email existe
    if not user:
        logger.info(f"Password reset requested for non-existent email: {req.email}")
        return {
            "success": True,
            "message": "Si el email existe, recibirás un enlace para restablecer tu contraseña"
        }
    
    # Generar token de reset
    reset_token = str(uuid.uuid4())
    reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Guardar token en la base de datos
    await db.users.update_one(
        {"email": req.email},
        {"$set": {
            "reset_token": reset_token,
            "reset_token_expires": reset_expires.isoformat()
        }}
    )
    
    # Enviar email
    email_service = get_email_service()
    
    if email_service.is_configured():
        config = get_config()
        app_url = config.cors_origins.split(',')[0] if config.cors_origins != '*' else ''
        reset_link = f"{app_url}/reset-password?token={reset_token}"
        
        template = get_password_reset_email_template(
            user.get('name', 'Usuario'),
            reset_link,
            app_url
        )
        
        result = email_service.send_email(
            to_email=req.email,
            subject=template['subject'],
            html_content=template['html'],
            text_content=template['text']
        )
        
        if not result['success']:
            logger.error(f"Failed to send password reset email: {result['message']}")
    else:
        logger.warning("Email service not configured, password reset email not sent")
    
    return {
        "success": True,
        "message": "Si el email existe, recibirás un enlace para restablecer tu contraseña"
    }


@router.post("/auth/reset-password")
async def reset_password(req: PasswordResetConfirm):
    """Restablece la contraseña usando el token"""
    # Buscar usuario con el token
    user = await db.users.find_one({"reset_token": req.token})
    
    if not user:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    # Verificar expiración
    expires = user.get('reset_token_expires')
    if expires:
        expires_dt = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_dt:
            raise HTTPException(status_code=400, detail="Token expirado. Solicita uno nuevo.")
    
    # Actualizar contraseña y limpiar token
    await db.users.update_one(
        {"reset_token": req.token},
        {
            "$set": {"password": hash_password(req.new_password)},
            "$unset": {"reset_token": "", "reset_token_expires": ""}
        }
    )
    
    return {
        "success": True,
        "message": "Contraseña actualizada correctamente"
    }


@router.get("/auth/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """Verifica si un token de reset es válido"""
    user = await db.users.find_one({"reset_token": token})
    
    if not user:
        return {"valid": False, "message": "Token inválido"}
    
    # Verificar expiración
    expires = user.get('reset_token_expires')
    if expires:
        expires_dt = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires_dt:
            return {"valid": False, "message": "Token expirado"}
    
    return {"valid": True, "email": user.get('email')}


# ==================== HELPER FUNCTIONS ====================

async def send_welcome_email(user_email: str, user_name: str):
    """Envía email de bienvenida a un nuevo usuario"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        logger.info("Email service not configured, skipping welcome email")
        return
    
    try:
        config = get_config()
        app_url = config.cors_origins.split(',')[0] if config.cors_origins != '*' else ''
        
        template = get_welcome_email_template(user_name, app_url)
        
        email_service.send_email(
            to_email=user_email,
            subject=template['subject'],
            html_content=template['html'],
            text_content=template['text']
        )
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")


async def send_subscription_change_email(user_email: str, user_name: str, old_plan: str, new_plan: str):
    """Envía email de cambio de suscripción"""
    email_service = get_email_service()
    
    if not email_service.is_configured():
        logger.info("Email service not configured, skipping subscription change email")
        return
    
    try:
        config = get_config()
        app_url = config.cors_origins.split(',')[0] if config.cors_origins != '*' else ''
        
        template = get_subscription_change_email_template(user_name, old_plan, new_plan, app_url)
        
        email_service.send_email(
            to_email=user_email,
            subject=template['subject'],
            html_content=template['html'],
            text_content=template['text']
        )
    except Exception as e:
        logger.error(f"Error sending subscription change email: {e}")
