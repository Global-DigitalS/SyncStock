import logging
from motor.motor_asyncio import AsyncIOMotorClient

# Importar configuración centralizada
from config import (
    MONGO_URL,
    DB_NAME,
    MONGO_CONNECT_TIMEOUT_MS,
    MONGO_SERVER_SELECTION_TIMEOUT_MS,
    MONGO_MAX_POOL_SIZE,
    MONGO_MIN_POOL_SIZE,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
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

logger = logging.getLogger(__name__)
