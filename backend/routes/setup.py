"""
Módulo de configuración inicial de la aplicación.
Permite configurar la conexión a MongoDB, JWT, CORS y crear el usuario SuperAdmin
completamente desde la interfaz web cuando la aplicación se despliega por primera vez.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
import uuid
import secrets
import logging

from services.auth import hash_password, create_token
from services.config_manager import (
    get_config, update_config, save_config, generate_jwt_secret,
    is_app_configured, AppConfig
)

router = APIRouter()
logger = logging.getLogger(__name__)


class SetupStatus(BaseModel):
    is_configured: bool
    has_database: bool
    has_superadmin: bool
    database_name: str = ""
    message: str = ""
    # Información adicional para el setup
    needs_mongo_config: bool = True
    needs_jwt_config: bool = True
    current_cors: str = "*"


class SetupRequest(BaseModel):
    mongo_url: str
    db_name: str = "supplier_sync_db"
    jwt_secret: str = ""  # Si vacío, se genera automáticamente
    cors_origins: str = "*"
    admin_email: EmailStr
    admin_password: str
    admin_name: str
    company: str = ""
    # SMTP Configuration (optional)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "SupplierSync Pro"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False


class SetupResponse(BaseModel):
    success: bool
    message: str
    token: str = ""
    user: dict = {}
    requires_restart: bool = False


@router.get("/setup/status", response_model=SetupStatus)
async def get_setup_status():
    """
    Verifica el estado de configuración de la aplicación.
    Devuelve si la base de datos está conectada, si existe un SuperAdmin,
    y qué configuraciones faltan.
    """
    config = get_config()
    
    has_database = False
    has_superadmin = False
    database_name = ""
    
    # Verificar conexión a MongoDB si hay URL configurada
    if config.mongo_url:
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            test_client = AsyncIOMotorClient(
                config.mongo_url,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
            )
            await test_client.admin.command("ping")
            has_database = True
            database_name = config.db_name
            
            # Verificar si existe un SuperAdmin
            test_db = test_client[config.db_name]
            superadmin = await test_db.users.find_one({"role": "superadmin"})
            has_superadmin = superadmin is not None
            
            test_client.close()
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            has_database = False
    
    is_configured = has_database and has_superadmin and bool(config.jwt_secret)
    
    # Determinar qué falta configurar
    needs_mongo_config = not config.mongo_url or not has_database
    needs_jwt_config = not config.jwt_secret
    
    if needs_mongo_config:
        message = "Configura la conexión a MongoDB para comenzar."
    elif needs_jwt_config:
        message = "Falta configurar la seguridad de la aplicación."
    elif not has_superadmin:
        message = "Crea el usuario SuperAdmin para completar la configuración."
    else:
        message = "Aplicación configurada correctamente."
    
    return SetupStatus(
        is_configured=is_configured,
        has_database=has_database,
        has_superadmin=has_superadmin,
        database_name=database_name,
        message=message,
        needs_mongo_config=needs_mongo_config,
        needs_jwt_config=needs_jwt_config,
        current_cors=config.cors_origins
    )


@router.post("/setup/configure", response_model=SetupResponse)
async def configure_app(setup: SetupRequest):
    """
    Configura la aplicación completamente desde la interfaz web:
    - Conexión a MongoDB
    - JWT Secret (genera uno si no se proporciona)
    - Orígenes CORS
    - Crea el usuario SuperAdmin
    
    Este endpoint solo funciona si no hay ningún SuperAdmin existente.
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Intentar conectar con la nueva URL de MongoDB
    try:
        test_client = AsyncIOMotorClient(
            setup.mongo_url,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
        )
        # Probar la conexión
        await test_client.admin.command("ping")
        test_db = test_client[setup.db_name]
        
        # Verificar si ya existe un SuperAdmin
        existing_superadmin = await test_db.users.find_one({"role": "superadmin"})
        if existing_superadmin:
            test_client.close()
            return SetupResponse(
                success=False,
                message="Ya existe un SuperAdmin. Si olvidaste las credenciales, contacta con soporte."
            )
        
        # Verificar si el email ya está en uso
        existing_user = await test_db.users.find_one({"email": setup.admin_email})
        if existing_user:
            test_client.close()
            return SetupResponse(
                success=False,
                message="El email ya está registrado en la base de datos."
            )
        
        # Generar JWT secret si no se proporcionó
        jwt_secret = setup.jwt_secret if setup.jwt_secret else generate_jwt_secret()
        
        # Guardar la configuración (incluyendo SMTP si se proporciona)
        new_config = AppConfig(
            mongo_url=setup.mongo_url,
            db_name=setup.db_name,
            jwt_secret=jwt_secret,
            cors_origins=setup.cors_origins,
            is_configured=True,
            # SMTP Configuration
            smtp_host=setup.smtp_host,
            smtp_port=setup.smtp_port,
            smtp_user=setup.smtp_user,
            smtp_password=setup.smtp_password,
            smtp_from_email=setup.smtp_from_email or setup.smtp_user,
            smtp_from_name=setup.smtp_from_name,
            smtp_use_tls=setup.smtp_use_tls,
            smtp_use_ssl=setup.smtp_use_ssl,
            smtp_configured=bool(setup.smtp_host and setup.smtp_user and setup.smtp_password)
        )
        save_config(new_config)
        logger.info("Configuration saved successfully")
        
        # Crear el SuperAdmin
        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        user_doc = {
            "id": user_id,
            "email": setup.admin_email,
            "password": hash_password(setup.admin_password),
            "name": setup.admin_name,
            "company": setup.company,
            "role": "superadmin",
            "max_suppliers": 999,
            "max_catalogs": 999,
            "max_woocommerce_stores": 999,
            "created_at": now
        }
        
        await test_db.users.insert_one(user_doc)
        logger.info(f"SuperAdmin created: {setup.admin_email}")
        
        # Crear token de autenticación usando el nuevo secret
        # Nota: Usamos una función especial ya que el secret cambió
        import jwt as pyjwt
        token_data = {
            "user_id": user_id,
            "role": "superadmin",
            "exp": datetime.now(timezone.utc).timestamp() + 86400 * 7  # 7 días
        }
        token = pyjwt.encode(token_data, jwt_secret, algorithm="HS256")
        
        test_client.close()
        
        # Programar reinicio del backend en segundo plano (después de responder)
        import subprocess
        import threading
        
        def restart_backend():
            import time
            time.sleep(2)  # Esperar 2 segundos para que la respuesta llegue al cliente
            try:
                # Intentar reiniciar el servicio systemd
                subprocess.run(['systemctl', 'restart', 'suppliersync-backend'], 
                             capture_output=True, timeout=10)
                logger.info("Backend service restarted via systemctl")
            except Exception as e:
                logger.warning(f"Could not restart via systemctl: {e}")
                try:
                    # Fallback: reiniciar via supervisorctl (para desarrollo)
                    subprocess.run(['supervisorctl', 'restart', 'backend'], 
                                 capture_output=True, timeout=10)
                    logger.info("Backend service restarted via supervisorctl")
                except Exception as e2:
                    logger.warning(f"Could not restart via supervisorctl: {e2}")
        
        # Iniciar el reinicio en un hilo separado
        restart_thread = threading.Thread(target=restart_backend, daemon=True)
        restart_thread.start()
        logger.info("Backend restart scheduled in 2 seconds")
        
        return SetupResponse(
            success=True,
            message="¡Configuración completada! El servidor se reiniciará automáticamente.",
            token=token,
            user={
                "id": user_id,
                "email": setup.admin_email,
                "name": setup.admin_name,
                "company": setup.company,
                "role": "superadmin",
                "max_suppliers": 999,
                "max_catalogs": 999,
                "max_woocommerce_stores": 999
            },
            requires_restart=True
        )
        
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return SetupResponse(
            success=False,
            message=f"Error de conexión a MongoDB: {str(e)}. Verifica la URL y las credenciales."
        )


@router.post("/setup/test-connection")
async def test_mongo_connection(data: dict):
    """
    Prueba la conexión a MongoDB sin crear ningún usuario.
    Útil para verificar la URL antes de completar la configuración.
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_url = data.get("mongo_url", "")
    db_name = data.get("db_name", "supplier_sync_db")
    
    if not mongo_url:
        return {"success": False, "message": "URL de MongoDB requerida"}
    
    try:
        test_client = AsyncIOMotorClient(
            mongo_url,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
        )
        
        # Probar la conexión
        await test_client.admin.command("ping")
        
        # Obtener información del servidor
        server_info = await test_client.server_info()
        version = server_info.get("version", "desconocida")
        
        # Verificar si la base de datos existe y tiene datos
        test_db = test_client[db_name]
        collections = await test_db.list_collection_names()
        
        test_client.close()
        
        return {
            "success": True,
            "message": f"Conexión exitosa a MongoDB v{version}",
            "database": db_name,
            "collections_count": len(collections),
            "has_data": len(collections) > 0
        }
        
    except Exception as e:
        logger.error(f"Connection test error: {e}")
        error_msg = str(e)
        
        # Mensajes de error más amigables
        if "Authentication failed" in error_msg:
            error_msg = "Error de autenticación. Verifica el usuario y contraseña."
        elif "ServerSelectionTimeoutError" in error_msg:
            error_msg = "No se pudo conectar al servidor. Verifica la URL y que el servidor esté accesible."
        elif "Invalid URI" in error_msg:
            error_msg = "URL de MongoDB inválida. Formato correcto: mongodb://[usuario:contraseña@]host:puerto"
        
        return {
            "success": False,
            "message": error_msg
        }
