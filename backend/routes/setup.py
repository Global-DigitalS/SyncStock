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
    Devuelve si la base de datos está conectada y si existe un SuperAdmin.
    """
    from services.database import db
    
    try:
        # Intentar conectar a la base de datos
        await db.command("ping")
        has_database = True
        database_name = db.name
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        has_database = False
        database_name = ""
    
    # Verificar si existe un SuperAdmin
    has_superadmin = False
    if has_database:
        try:
            superadmin = await db.users.find_one({"role": "superadmin"})
            has_superadmin = superadmin is not None
        except Exception as e:
            logger.error(f"Error checking superadmin: {e}")
    
    is_configured = has_database and has_superadmin
    
    if not has_database:
        message = "Base de datos no configurada. Por favor, configura la conexión a MongoDB."
    elif not has_superadmin:
        message = "No hay usuario SuperAdmin. Por favor, crea el primer usuario administrador."
    else:
        message = "Aplicación configurada correctamente."
    
    return SetupStatus(
        is_configured=is_configured,
        has_database=has_database,
        has_superadmin=has_superadmin,
        database_name=database_name,
        message=message
    )


@router.post("/setup/configure", response_model=SetupResponse)
async def configure_app(setup: SetupRequest):
    """
    Configura la aplicación con la conexión a MongoDB y crea el SuperAdmin.
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
            return SetupResponse(
                success=False,
                message="Ya existe un SuperAdmin. Si olvidaste las credenciales, contacta con soporte."
            )
        
        # Verificar si el email ya está en uso
        existing_user = await test_db.users.find_one({"email": setup.admin_email})
        if existing_user:
            return SetupResponse(
                success=False,
                message="El email ya está registrado en la base de datos."
            )
        
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
        
        # Crear token de autenticación
        token = create_token(user_id, "superadmin")
        
        # Guardar la configuración en un archivo si es necesario
        # (Nota: En producción, esto se haría mediante variables de entorno)
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            # Leer contenido existente
            env_content = ""
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_content = f.read()
            
            # Actualizar MONGO_URL si es diferente
            lines = env_content.split('\n')
            new_lines = []
            mongo_updated = False
            db_updated = False
            
            for line in lines:
                if line.startswith('MONGO_URL='):
                    new_lines.append(f'MONGO_URL={setup.mongo_url}')
                    mongo_updated = True
                elif line.startswith('DB_NAME='):
                    new_lines.append(f'DB_NAME={setup.db_name}')
                    db_updated = True
                else:
                    new_lines.append(line)
            
            if not mongo_updated:
                new_lines.append(f'MONGO_URL={setup.mongo_url}')
            if not db_updated:
                new_lines.append(f'DB_NAME={setup.db_name}')
            
            with open(env_path, 'w') as f:
                f.write('\n'.join(new_lines))
            
            logger.info("Environment file updated successfully")
        except Exception as e:
            logger.warning(f"Could not update .env file: {e}")
        
        test_client.close()
        
        return SetupResponse(
            success=True,
            message="Configuración completada. SuperAdmin creado exitosamente.",
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
            }
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
