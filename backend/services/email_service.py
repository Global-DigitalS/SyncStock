"""
Servicio de envío de correos electrónicos via SMTP.
Soporta cualquier servidor SMTP (Gmail, Outlook, servidor propio, etc.)
"""
import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para envío de correos electrónicos via SMTP"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.smtp_host = self.config.get('smtp_host', '')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.smtp_user = self.config.get('smtp_user', '')
        self.smtp_password = self.config.get('smtp_password', '')
        self.smtp_from_email = self.config.get('smtp_from_email', '')
        self.smtp_from_name = self.config.get('smtp_from_name', 'SyncStock')
        self.smtp_use_tls = self.config.get('smtp_use_tls', True)
        self.smtp_use_ssl = self.config.get('smtp_use_ssl', False)
    
    def is_configured(self) -> bool:
        """Verifica si el servicio de email está configurado"""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)
    
    def test_connection(self) -> Dict[str, Any]:
        """Prueba la conexión SMTP"""
        if not self.is_configured():
            return {
                "success": False,
                "message": "Configuración SMTP incompleta"
            }
        
        try:
            if self.smtp_use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                if self.smtp_use_tls:
                    server.starttls()
            
            server.login(self.smtp_user, self.smtp_password)
            server.quit()
            
            return {
                "success": True,
                "message": f"Conexión exitosa a {self.smtp_host}:{self.smtp_port}"
            }
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP auth error: {e}")
            return {
                "success": False,
                "message": "Error de autenticación. Verifica usuario y contraseña."
            }
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connect error: {e}")
            return {
                "success": False,
                "message": f"No se puede conectar a {self.smtp_host}:{self.smtp_port}"
            }
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envía un correo electrónico"""
        if not self.is_configured():
            logger.warning("Email service not configured, skipping email send")
            return {"success": False, "message": "Servicio de email no configurado"}
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_from_name} <{self.smtp_from_email or self.smtp_user}>"
            msg['To'] = to_email
            
            # Texto plano como fallback
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            # HTML
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Conectar y enviar
            if self.smtp_use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                if self.smtp_use_tls:
                    server.starttls()
            
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_from_email or self.smtp_user, to_email, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return {"success": True, "message": "Email enviado correctamente"}
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {"success": False, "message": f"Error al enviar: {str(e)}"}


# ==================== EMAIL TEMPLATES ====================

def get_welcome_email_template(user_name: str, app_url: str) -> Dict[str, str]:
    """Template para email de bienvenida tras registro"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f7;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f7; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 40px 40px 30px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">SyncStock</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 14px;">Gestión inteligente de catálogos</p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #1e293b; margin: 0 0 20px; font-size: 24px;">¡Bienvenido, {user_name}!</h2>
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                    Tu cuenta ha sido creada exitosamente. Ahora puedes comenzar a gestionar tus proveedores, 
                                    productos y catálogos de forma eficiente.
                                </p>
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px;">
                                    <strong>¿Qué puedes hacer?</strong>
                                </p>
                                <ul style="color: #475569; font-size: 15px; line-height: 1.8; margin: 0 0 30px; padding-left: 20px;">
                                    <li>Conectar proveedores via FTP o URL</li>
                                    <li>Importar y unificar productos por EAN</li>
                                    <li>Crear catálogos con reglas de margen personalizadas</li>
                                    <li>Sincronizar con tiendas eCommerce</li>
                                </ul>
                                <table cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                                    <tr>
                                        <td style="background-color: #4f46e5; border-radius: 6px;">
                                            <a href="{app_url}" style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Acceder a mi cuenta
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #64748b; font-size: 13px; margin: 0;">
                                    © {datetime.now().year} SyncStock. Todos los derechos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    text = f"""
    ¡Bienvenido a SyncStock, {user_name}!
    
    Tu cuenta ha sido creada exitosamente.
    
    Accede a tu cuenta en: {app_url}
    
    © {datetime.now().year} SyncStock
    """
    
    return {"html": html, "text": text, "subject": f"¡Bienvenido a SyncStock, {user_name}!"}


def get_password_reset_email_template(user_name: str, reset_link: str, app_url: str) -> Dict[str, str]:
    """Template para email de recuperación de contraseña"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f7;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f7; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 40px 40px 30px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">SyncStock</h1>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #1e293b; margin: 0 0 20px; font-size: 24px;">Restablecer contraseña</h2>
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                    Hola {user_name},
                                </p>
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                    Hemos recibido una solicitud para restablecer la contraseña de tu cuenta. 
                                    Si no has sido tú, puedes ignorar este correo.
                                </p>
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px;">
                                    Para restablecer tu contraseña, haz clic en el siguiente botón:
                                </p>
                                <table cellpadding="0" cellspacing="0" style="margin: 0 auto 30px;">
                                    <tr>
                                        <td style="background-color: #4f46e5; border-radius: 6px;">
                                            <a href="{reset_link}" style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Restablecer contraseña
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Este enlace expirará en 1 hora por seguridad.
                                </p>
                                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 20px 0 0; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                                    Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                                    <a href="{reset_link}" style="color: #4f46e5; word-break: break-all;">{reset_link}</a>
                                </p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #64748b; font-size: 13px; margin: 0;">
                                    © {datetime.now().year} SyncStock. Todos los derechos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    text = f"""
    Restablecer contraseña - SyncStock
    
    Hola {user_name},
    
    Hemos recibido una solicitud para restablecer tu contraseña.
    
    Para restablecer tu contraseña, visita: {reset_link}
    
    Este enlace expirará en 1 hora.
    
    Si no solicitaste esto, ignora este correo.
    
    © {datetime.now().year} SyncStock
    """
    
    return {"html": html, "text": text, "subject": "Restablecer contraseña - SyncStock"}


def get_subscription_change_email_template(
    user_name: str, 
    old_plan: str, 
    new_plan: str, 
    app_url: str
) -> Dict[str, str]:
    """Template para email de cambio de plan de suscripción"""
    
    is_upgrade = True  # Podríamos determinar esto comparando los planes
    action_text = "actualizado" if is_upgrade else "modificado"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f7;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f7; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 40px 30px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">SyncStock</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0; font-size: 14px;">Cambio de suscripción</p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #1e293b; margin: 0 0 20px; font-size: 24px;">¡Plan {action_text}!</h2>
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
                                    Hola {user_name},
                                </p>
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px;">
                                    Tu plan de suscripción ha sido {action_text} correctamente.
                                </p>
                                
                                <!-- Plan comparison -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                    <tr>
                                        <td width="45%" style="padding: 20px; background-color: #f1f5f9; border-radius: 8px; text-align: center;">
                                            <p style="color: #94a3b8; font-size: 12px; margin: 0 0 5px; text-transform: uppercase;">Plan anterior</p>
                                            <p style="color: #64748b; font-size: 18px; font-weight: 600; margin: 0;">{old_plan}</p>
                                        </td>
                                        <td width="10%" style="text-align: center; color: #10b981; font-size: 24px;">→</td>
                                        <td width="45%" style="padding: 20px; background-color: #ecfdf5; border-radius: 8px; text-align: center; border: 2px solid #10b981;">
                                            <p style="color: #10b981; font-size: 12px; margin: 0 0 5px; text-transform: uppercase;">Nuevo plan</p>
                                            <p style="color: #059669; font-size: 18px; font-weight: 600; margin: 0;">{new_plan}</p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px;">
                                    Los cambios ya están activos en tu cuenta. Puedes acceder a todas las nuevas 
                                    funcionalidades de tu plan inmediatamente.
                                </p>
                                
                                <table cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                                    <tr>
                                        <td style="background-color: #10b981; border-radius: 6px;">
                                            <a href="{app_url}" style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Ir a mi cuenta
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #64748b; font-size: 13px; margin: 0 0 10px;">
                                    ¿Tienes preguntas sobre tu nuevo plan? Contacta con nosotros.
                                </p>
                                <p style="color: #64748b; font-size: 13px; margin: 0;">
                                    © {datetime.now().year} SyncStock. Todos los derechos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    text = f"""
    Cambio de plan - SyncStock
    
    Hola {user_name},
    
    Tu plan ha sido {action_text} correctamente.
    
    Plan anterior: {old_plan}
    Nuevo plan: {new_plan}
    
    Los cambios ya están activos en tu cuenta.
    
    Accede a tu cuenta en: {app_url}
    
    © {datetime.now().year} SyncStock
    """
    
    return {"html": html, "text": text, "subject": f"Tu plan ha sido {action_text} - SyncStock"}


# ==================== EMAIL SERVICE INSTANCE ====================

def get_email_service(account_type: str = "transactional") -> EmailService:
    """
    Obtiene una instancia del servicio de email con la configuración de la cuenta especificada.
    
    Args:
        account_type: Tipo de cuenta (transactional, support, billing)
                     Por defecto usa 'transactional' para emails del sistema.
    
    Returns:
        EmailService configurado o vacío si no hay configuración
    """
    try:
        import asyncio
        from services.database import db
        
        async def get_email_config():
            # Try to get the specific account type
            config = await db.email_accounts.find_one({"type": account_type, "enabled": True})
            
            # If not found or not enabled, fallback to transactional
            if not config and account_type != "transactional":
                config = await db.email_accounts.find_one({"type": "transactional", "enabled": True})
            
            # If still no config, try the legacy config_manager
            if not config:
                from services.config_manager import get_config
                legacy_config = get_config()
                return {
                    'smtp_host': getattr(legacy_config, 'smtp_host', ''),
                    'smtp_port': getattr(legacy_config, 'smtp_port', 587),
                    'smtp_user': getattr(legacy_config, 'smtp_user', ''),
                    'smtp_password': getattr(legacy_config, 'smtp_password', ''),
                    'smtp_from_email': getattr(legacy_config, 'smtp_from_email', ''),
                    'smtp_from_name': getattr(legacy_config, 'smtp_from_name', 'SyncStock'),
                    'smtp_use_tls': getattr(legacy_config, 'smtp_use_tls', True),
                    'smtp_use_ssl': getattr(legacy_config, 'smtp_use_ssl', False),
                }
            
            return {
                'smtp_host': config.get('smtp_host', ''),
                'smtp_port': config.get('smtp_port', 587),
                'smtp_user': config.get('smtp_user', ''),
                'smtp_password': config.get('smtp_password', ''),
                'smtp_from_email': config.get('smtp_from_email', '') or config.get('smtp_user', ''),
                'smtp_from_name': config.get('smtp_from_name', 'SyncStock'),
                'smtp_use_tls': config.get('smtp_use_tls', True),
                'smtp_use_ssl': config.get('smtp_use_ssl', False),
            }
        
        # Run async function
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, get_email_config())
                    email_config = future.result()
            else:
                email_config = loop.run_until_complete(get_email_config())
        except RuntimeError:
            email_config = asyncio.run(get_email_config())
        
        return EmailService(email_config)
        
    except Exception as e:
        logger.error(f"Error creating email service for {account_type}: {e}")
        # Fallback to legacy config
        try:
            from services.config_manager import get_config
            config = get_config()
            email_config = {
                'smtp_host': getattr(config, 'smtp_host', ''),
                'smtp_port': getattr(config, 'smtp_port', 587),
                'smtp_user': getattr(config, 'smtp_user', ''),
                'smtp_password': getattr(config, 'smtp_password', ''),
                'smtp_from_email': getattr(config, 'smtp_from_email', ''),
                'smtp_from_name': getattr(config, 'smtp_from_name', 'SyncStock'),
                'smtp_use_tls': getattr(config, 'smtp_use_tls', True),
                'smtp_use_ssl': getattr(config, 'smtp_use_ssl', False),
            }
            return EmailService(email_config)
        except Exception as e2:
            logger.error(f"Fallback email config also failed: {e2}")
            return EmailService({})


# Helper function to get email service asynchronously
async def get_email_service_async(account_type: str = "transactional") -> EmailService:
    """
    Versión asíncrona de get_email_service para usar en contextos async.
    """
    from services.database import db
    
    try:
        # Try to get the specific account type
        config = await db.email_accounts.find_one({"type": account_type, "enabled": True})
        
        # If not found or not enabled, fallback to transactional
        if not config and account_type != "transactional":
            config = await db.email_accounts.find_one({"type": "transactional", "enabled": True})
        
        # If still no config, try the legacy config_manager
        if not config:
            from services.config_manager import get_config
            legacy_config = get_config()
            email_config = {
                'smtp_host': getattr(legacy_config, 'smtp_host', ''),
                'smtp_port': getattr(legacy_config, 'smtp_port', 587),
                'smtp_user': getattr(legacy_config, 'smtp_user', ''),
                'smtp_password': getattr(legacy_config, 'smtp_password', ''),
                'smtp_from_email': getattr(legacy_config, 'smtp_from_email', ''),
                'smtp_from_name': getattr(legacy_config, 'smtp_from_name', 'SyncStock'),
                'smtp_use_tls': getattr(legacy_config, 'smtp_use_tls', True),
                'smtp_use_ssl': getattr(legacy_config, 'smtp_use_ssl', False),
            }
            return EmailService(email_config)
        
        email_config = {
            'smtp_host': config.get('smtp_host', ''),
            'smtp_port': config.get('smtp_port', 587),
            'smtp_user': config.get('smtp_user', ''),
            'smtp_password': config.get('smtp_password', ''),
            'smtp_from_email': config.get('smtp_from_email', '') or config.get('smtp_user', ''),
            'smtp_from_name': config.get('smtp_from_name', 'SyncStock'),
            'smtp_use_tls': config.get('smtp_use_tls', True),
            'smtp_use_ssl': config.get('smtp_use_ssl', False),
        }
        return EmailService(email_config)
        
    except Exception as e:
        logger.error(f"Error in get_email_service_async for {account_type}: {e}")
        return EmailService({})
