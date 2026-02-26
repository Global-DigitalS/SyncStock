import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

def get_mongo_config():
    """
    Obtiene la configuración de MongoDB.
    Prioridad:
    1. Variables de entorno (para producción/Kubernetes)
    2. Archivo config.json (para configuración via UI)
    3. Valores por defecto (solo para desarrollo local)
    """
    # Primero verificar variables de entorno (prioridad máxima en producción)
    env_mongo_url = os.environ.get('MONGO_URL', '').strip()
    env_db_name = os.environ.get('DB_NAME', '').strip()
    
    # Si MONGO_URL está en las variables de entorno y NO es localhost, usarla
    if env_mongo_url and 'localhost' not in env_mongo_url and '127.0.0.1' not in env_mongo_url:
        logger.info("Using MONGO_URL from environment variables (production mode)")
        return env_mongo_url, env_db_name or 'supplier_sync_db'
    
    # Intentar cargar desde config.json
    try:
        from services.config_manager import get_config
        config = get_config()
        if config.mongo_url and config.mongo_url.strip():
            logger.info("Using MongoDB config from config.json")
            return config.mongo_url, config.db_name or 'supplier_sync_db'
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Error loading config.json: {e}")
    
    # Fallback a variables de entorno o localhost (desarrollo)
    mongo_url = env_mongo_url if env_mongo_url else 'mongodb://localhost:27017'
    db_name = env_db_name if env_db_name else 'supplier_sync_db'
    logger.info(f"Using fallback MongoDB config: {mongo_url[:30]}...")
    return mongo_url, db_name

MONGO_URL, DB_NAME = get_mongo_config()

# Importar configuración centralizada para timeouts y pool
from config import (
    MONGO_CONNECT_TIMEOUT_MS,
    MONGO_SERVER_SELECTION_TIMEOUT_MS,
    MONGO_MAX_POOL_SIZE,
    MONGO_MIN_POOL_SIZE,
)

# Configurar cliente de MongoDB con opciones avanzadas
client = AsyncIOMotorClient(
    MONGO_URL,
    connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
    serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
    maxPoolSize=MONGO_MAX_POOL_SIZE,
    minPoolSize=MONGO_MIN_POOL_SIZE,
)

# Base de datos principal
db = client[DB_NAME]

logger.info(f"Database configured: {DB_NAME}")
