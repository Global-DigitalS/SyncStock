"""
Rutas para configuración y envío de correos electrónicos.
Soporta múltiples cuentas de email para diferentes propósitos.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import secrets
import logging

from services.auth import get_current_user, get_superadmin_user, hash_password
from services.database import db
from services.config_manager import get_config, update_config
from services.encryption import encrypt_password, decrypt_password
from services.email_service import (
    EmailService,
    get_email_service,
    get_email_service_async,
    get_welcome_email_template,
    get_password_reset_email_template,
    get_subscription_change_email_template,
    get_superadmin_new_registration_email_template,
    get_superadmin_status_change_email_template,
    get_contact_form_email_template,
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
    smtp_from_name: Optional[str] = "SyncStock"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False


class EmailAccountConfig(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    enabled: bool = False


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


class SendTestEmailSimple(BaseModel):
    to_email: EmailStr


# Valid email account types
EMAIL_ACCOUNT_TYPES = ["transactional", "support", "billing"]


# ==================== MULTI-ACCOUNT EMAIL CONFIGURATION ====================

@router.get("/email/accounts")
async def get_all_email_accounts(user: dict = Depends(get_superadmin_user)):
    """Get all email account configurations"""
    result = {}
    for account_type in EMAIL_ACCOUNT_TYPES:
        config = await db.email_accounts.find_one({"type": account_type})
        if config:
            result[account_type] = {
                "smtp_host": config.get("smtp_host", ""),
                "smtp_port": config.get("smtp_port", 587),
                "smtp_user": config.get("smtp_user", ""),
                "smtp_password": "",  # Never return password
                "smtp_from_email": config.get("smtp_from_email", ""),
                "smtp_from_name": config.get("smtp_from_name", ""),
                "smtp_use_tls": config.get("smtp_use_tls", True),
                "smtp_use_ssl": config.get("smtp_use_ssl", False),
                "enabled": config.get("enabled", False),
                "has_password": bool(config.get("smtp_password"))
            }
        else:
            # Return default config
            default_names = {
                "transactional": "SyncStock",
                "support": "Soporte SyncStock",
                "billing": "Facturación SyncStock"
            }
            result[account_type] = {
                "smtp_host": "",
                "smtp_port": 587,
                "smtp_user": "",
                "smtp_password": "",
                "smtp_from_email": "",
                "smtp_from_name": default_names.get(account_type, "SyncStock"),
                "smtp_use_tls": True,
                "smtp_use_ssl": False,
                "enabled": False,
                "has_password": False
            }
    return result


@router.put("/email/accounts/{account_type}")
async def update_email_account(
    account_type: str,
    config: EmailAccountConfig,
    user: dict = Depends(get_superadmin_user)
):
    """Update a specific email account configuration"""
    if account_type not in EMAIL_ACCOUNT_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipo de cuenta inválido. Usa: {EMAIL_ACCOUNT_TYPES}")
    
    update_data = {
        "type": account_type,
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "smtp_user": config.smtp_user,
        "smtp_from_email": config.smtp_from_email,
        "smtp_from_name": config.smtp_from_name,
        "smtp_use_tls": config.smtp_use_tls,
        "smtp_use_ssl": config.smtp_use_ssl,
        "enabled": config.enabled,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user.get("email")
    }
    
    # Only update password if provided; encrypt before storing (A02)
    if config.smtp_password:
        update_data["smtp_password"] = encrypt_password(config.smtp_password)
    
    await db.email_accounts.update_one(
        {"type": account_type},
        {"$set": update_data},
        upsert=True
    )
    
    logger.info(f"Email account '{account_type}' updated by {user.get('email')}")
    return {"success": True, "message": f"Configuración de {account_type} actualizada"}


@router.post("/email/accounts/{account_type}/test-connection")
async def test_email_account_connection(
    account_type: str,
    user: dict = Depends(get_superadmin_user)
):
    """Test SMTP connection for a specific email account"""
    if account_type not in EMAIL_ACCOUNT_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de cuenta inválido")
    
    config = await db.email_accounts.find_one({"type": account_type})
    if not config or not config.get("smtp_host"):
        raise HTTPException(status_code=400, detail="Cuenta no configurada")
    
    try:
        import smtplib
        
        smtp_host = config.get("smtp_host")
        smtp_port = config.get("smtp_port", 587)
        smtp_user = config.get("smtp_user")
        smtp_password = decrypt_password(config.get("smtp_password", ""))
        use_tls = config.get("smtp_use_tls", True)
        use_ssl = config.get("smtp_use_ssl", False)
        
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            if use_tls:
                server.starttls()
        
        server.login(smtp_user, smtp_password)
        server.quit()
        
        return {"success": True, "message": "Conexión exitosa"}
    except Exception as e:
        logger.error(f"SMTP connection test failed for {account_type}: {e}")
        return {"success": False, "message": str(e)}


@router.post("/email/accounts/{account_type}/send-test")
async def send_test_email_from_account(
    account_type: str,
    request: SendTestEmailSimple,
    user: dict = Depends(get_superadmin_user)
):
    """Send a test email from a specific account"""
    if account_type not in EMAIL_ACCOUNT_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de cuenta inválido")
    
    config = await db.email_accounts.find_one({"type": account_type})
    if not config or not config.get("smtp_host"):
        raise HTTPException(status_code=400, detail="Cuenta no configurada")
    
    try:
        # Create email service with this specific config
        email_config = {
            "smtp_host": config.get("smtp_host"),
            "smtp_port": config.get("smtp_port", 587),
            "smtp_user": config.get("smtp_user"),
            "smtp_password": decrypt_password(config.get("smtp_password", "")),
            "smtp_from_email": config.get("smtp_from_email") or config.get("smtp_user"),
            "smtp_from_name": config.get("smtp_from_name", "SyncStock"),
            "smtp_use_tls": config.get("smtp_use_tls", True),
            "smtp_use_ssl": config.get("smtp_use_ssl", False)
        }
        
        email_service = EmailService(email_config)
        
        # Get appropriate test template
        account_labels = {
            "transactional": "Transaccional (Registro/Contraseñas)",
            "support": "Soporte",
            "billing": "Facturación"
        }
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4F46E5;">Email de prueba - {account_labels.get(account_type, account_type)}</h2>
            <p>Este es un email de prueba desde la cuenta <strong>{account_type}</strong>.</p>
            <p>Si recibes este mensaje, la configuración SMTP es correcta.</p>
            <hr style="border: 1px solid #E5E7EB; margin: 20px 0;">
            <p style="color: #6B7280; font-size: 12px;">
                Configuración utilizada:<br>
                - Servidor: {config.get('smtp_host')}:{config.get('smtp_port')}<br>
                - Remitente: {config.get('smtp_from_name')} &lt;{config.get('smtp_from_email') or config.get('smtp_user')}&gt;<br>
                - TLS: {'Sí' if config.get('smtp_use_tls') else 'No'}<br>
                - SSL: {'Sí' if config.get('smtp_use_ssl') else 'No'}
            </p>
        </body>
        </html>
        """
        
        result = email_service.send_email(
            to_email=request.to_email,
            subject=f"[TEST] Email de prueba - {account_labels.get(account_type, account_type)}",
            html_content=html_content,
            text_content=f"Email de prueba desde la cuenta {account_type}"
        )
        
        if result["success"]:
            return {"success": True, "message": "Email enviado correctamente"}
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email from {account_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LEGACY SMTP CONFIGURATION (kept for compatibility) ====================

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
async def save_email_config(req: SmtpConfigRequest, user: dict = Depends(get_superadmin_user)):
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
async def test_smtp_connection(req: SmtpTestRequest, _admin: dict = Depends(get_superadmin_user)):
    """Prueba la conexión SMTP sin guardar la configuración. Requiere SuperAdmin."""
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
async def send_test_email(req: SendTestEmailRequest, user: dict = Depends(get_superadmin_user)):
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
    
    # Generar token de reset (criptográficamente seguro)
    reset_token = secrets.token_urlsafe(32)
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
    
    return {"valid": True}


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


async def notify_superadmins_new_registration(new_user_name: str, new_user_email: str, new_user_company: str = None):
    """Envía notificación a todos los SuperAdmins cuando un usuario nuevo se registra"""
    email_service = get_email_service()

    if not email_service.is_configured():
        logger.info("Email service not configured, skipping superadmin new-registration notification")
        return

    try:
        superadmins = await db.users.find(
            {"role": "superadmin"},
            {"email": 1, "_id": 0}
        ).to_list(100)

        if not superadmins:
            return

        config = get_config()
        app_url = config.cors_origins.split(',')[0] if config.cors_origins != '*' else ''

        template = get_superadmin_new_registration_email_template(
            new_user_name, new_user_email, new_user_company or "", app_url
        )

        for sa in superadmins:
            email_service.send_email(
                to_email=sa["email"],
                subject=template["subject"],
                html_content=template["html"],
                text_content=template["text"],
            )
    except Exception as e:
        logger.error(f"Error sending new-registration notification to superadmins: {e}")


async def notify_superadmins_status_change(user_name: str, user_email: str, new_status: bool, changed_by: str):
    """Envía notificación a todos los SuperAdmins cuando el estado de un usuario cambia"""
    email_service = get_email_service()

    if not email_service.is_configured():
        logger.info("Email service not configured, skipping superadmin status-change notification")
        return

    try:
        superadmins = await db.users.find(
            {"role": "superadmin"},
            {"email": 1, "_id": 0}
        ).to_list(100)

        if not superadmins:
            return

        config = get_config()
        app_url = config.cors_origins.split(',')[0] if config.cors_origins != '*' else ''

        template = get_superadmin_status_change_email_template(
            user_name, user_email, new_status, changed_by, app_url
        )

        for sa in superadmins:
            email_service.send_email(
                to_email=sa["email"],
                subject=template["subject"],
                html_content=template["html"],
                text_content=template["text"],
            )
    except Exception as e:
        logger.error(f"Error sending status-change notification to superadmins: {e}")


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


# ==================== FORMULARIO DE CONTACTO PÚBLICO ====================

CONTACT_DESTINATION_EMAIL = "hola@sync-stock.com"


class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    subject: Optional[str] = ""
    message: str


@router.post("/contact")
async def submit_contact_form(request: ContactFormRequest):
    """
    Recibe las consultas del formulario de contacto de la landing page y las reenvía
    a hola@sync-stock.com. Endpoint público (sin autenticación).
    """
    if not request.name.strip() or not request.message.strip():
        raise HTTPException(status_code=422, detail="Nombre y mensaje son obligatorios")

    try:
        email_service = await get_email_service_async("transactional")

        template = get_contact_form_email_template(
            name=request.name.strip(),
            email=str(request.email),
            subject=request.subject.strip() if request.subject else "",
            message=request.message.strip(),
        )

        result = email_service.send_email(
            to_email=CONTACT_DESTINATION_EMAIL,
            subject=template["subject"],
            html_content=template["html"],
            text_content=template["text"],
        )

        if not result.get("success"):
            logger.error(f"Error enviando formulario de contacto: {result.get('message')}")
            raise HTTPException(status_code=502, detail="No se pudo enviar el mensaje. Inténtalo más tarde.")

        logger.info(f"Formulario de contacto recibido de {request.email} y reenviado a {CONTACT_DESTINATION_EMAIL}")
        return {"success": True, "message": "Mensaje enviado correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inesperado en formulario de contacto: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
