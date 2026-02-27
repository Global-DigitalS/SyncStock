import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

def get_mongo_config():
    """
    Obtiene la configuración de MongoDB.
    Prioridad:
    1. Archivo config.json (para configuración via UI)
    2. Variables de entorno
    3. Valores por defecto (solo para desarrollo local)
    """
    # Primero intentar cargar desde config.json (prioridad máxima después de /setup)
    try:
        from services.config_manager import get_config
        config = get_config()
        if config.mongo_url and config.mongo_url.strip() and config.is_configured:
            logger.info("Using MongoDB config from config.json")
            return config.mongo_url, config.db_name or 'supplier_sync_db'
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Error loading config.json: {e}")
    
    # Fallback a variables de entorno
    env_mongo_url = os.environ.get('MONGO_URL', '').strip()
    env_db_name = os.environ.get('DB_NAME', '').strip()
    
    if env_mongo_url:
        logger.info("Using MONGO_URL from environment variables")
        return env_mongo_url, env_db_name or 'supplier_sync_db'
    
    # Último recurso: localhost (desarrollo)
    logger.info("Using default localhost MongoDB config")
    return 'mongodb://localhost:27017', 'supplier_sync_db'


# Obtener configuración inicial
MONGO_URL, DB_NAME = get_mongo_config()

# Importar configuración de timeouts
try:
    from config import (
        MONGO_CONNECT_TIMEOUT_MS,
        MONGO_SERVER_SELECTION_TIMEOUT_MS,
        MONGO_MAX_POOL_SIZE,
        MONGO_MIN_POOL_SIZE,
    )
except ImportError:
    MONGO_CONNECT_TIMEOUT_MS = 5000
    MONGO_SERVER_SELECTION_TIMEOUT_MS = 5000
    MONGO_MAX_POOL_SIZE = 10
    MONGO_MIN_POOL_SIZE = 1

# Crear cliente global
client = AsyncIOMotorClient(
    MONGO_URL,
    connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
    serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
    maxPoolSize=MONGO_MAX_POOL_SIZE,
    minPoolSize=MONGO_MIN_POOL_SIZE,
)
db = client[DB_NAME]

logger.info(f"MongoDB connection initialized: {MONGO_URL[:40]}... DB: {DB_NAME}")

# Base de datos principal
db = client[DB_NAME]

logger.info(f"Database configured: {DB_NAME}")
