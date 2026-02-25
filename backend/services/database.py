import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Intentar cargar configuración desde config_manager
try:
    from services.config_manager import get_config
    config = get_config()
    MONGO_URL = config.mongo_url if config.mongo_url else os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME = config.db_name if config.db_name else os.environ.get('DB_NAME', 'supplier_sync_db')
except ImportError:
    # Fallback a variables de entorno
    MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME = os.environ.get('DB_NAME', 'supplier_sync_db')

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
