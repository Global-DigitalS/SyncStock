import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Configuración de timeouts
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


class DatabaseManager:
    """
    Gestor de conexión a MongoDB con soporte para recarga dinámica.
    Permite actualizar la conexión cuando cambia la configuración sin reiniciar el servidor.
    """
    
    def __init__(self):
        self._client = None
        self._db = None
        self._mongo_url = None
        self._db_name = None
        self._initialize()
    
    def _get_mongo_config(self):
        """
        Obtiene la configuración de MongoDB.
        Prioridad:
        1. Archivo config.json persistente (/etc/syncstock/)
        2. Variables de entorno
        3. Valores por defecto (solo para desarrollo local)
        """
        # Primero intentar cargar desde config.json (prioridad máxima después de /setup)
        try:
            from services.config_manager import get_config
            config = get_config()
            if config.mongo_url and config.mongo_url.strip() and config.is_configured:
                logger.info("Using MongoDB config from config.json")
                return config.mongo_url, config.db_name or 'syncstock_db'
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Error loading config.json: {e}")
        
        # Fallback a variables de entorno
        env_mongo_url = os.environ.get('MONGO_URL', '').strip()
        env_db_name = os.environ.get('DB_NAME', '').strip()
        
        if env_mongo_url:
            logger.info("Using MONGO_URL from environment variables")
            return env_mongo_url, env_db_name or 'syncstock_db'
        
        # Último recurso: localhost (desarrollo)
        logger.info("Using default localhost MongoDB config")
        return 'mongodb://localhost:27017', 'syncstock_db'
    
    def _initialize(self):
        """Inicializa o reinicializa la conexión a MongoDB."""
        self._mongo_url, self._db_name = self._get_mongo_config()
        
        # Crear nuevo cliente (no cerrar el anterior inmediatamente para evitar race conditions)
        old_client = self._client
        
        # Crear nuevo cliente
        self._client = AsyncIOMotorClient(
            self._mongo_url,
            connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
            serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
            maxPoolSize=MONGO_MAX_POOL_SIZE,
            minPoolSize=MONGO_MIN_POOL_SIZE,
        )
        self._db = self._client[self._db_name]
        
        # Cerrar cliente anterior después de crear el nuevo
        if old_client:
            try:
                old_client.close()
            except Exception:
                pass
        
        # Ocultar credenciales en el log
        safe_url = self._mongo_url[:40] + "..." if len(self._mongo_url) > 40 else self._mongo_url
        if "@" in safe_url:
            # Ocultar la contraseña
            parts = safe_url.split("@")
            if ":" in parts[0]:
                user_part = parts[0].split(":")
                safe_url = f"{user_part[0]}:****@{parts[1]}" if len(parts) > 1 else safe_url
        
        logger.info(f"MongoDB connection initialized: {safe_url} DB: {self._db_name}")
    
    def reload_config(self):
        """
        Recarga la configuración de MongoDB.
        Útil después de completar el setup inicial.
        """
        logger.info("Reloading MongoDB configuration...")
        self._initialize()
        return True
    
    def check_and_reload_if_needed(self):
        """
        Verifica si la configuración ha cambiado y recarga si es necesario.
        """
        try:
            from services.config_manager import get_config
            config = get_config()
            if config.mongo_url and config.mongo_url != self._mongo_url:
                logger.info("MongoDB URL changed, reloading connection...")
                self._initialize()
                return True
        except Exception as e:
            logger.warning(f"Error checking config: {e}")
        return False
    
    @property
    def client(self):
        return self._client
    
    @property
    def db(self):
        return self._db
    
    @property
    def mongo_url(self):
        return self._mongo_url
    
    @property
    def db_name(self):
        return self._db_name


# Instancia global del gestor de base de datos
_db_manager = DatabaseManager()


class DatabaseProxy:
    """
    Proxy para acceder siempre a la instancia actual de la base de datos.
    Esto evita problemas cuando la conexión se recarga.
    """
    def __getattr__(self, name):
        return getattr(_db_manager.db, name)
    
    def __getitem__(self, name):
        return _db_manager.db[name]


class ClientProxy:
    """
    Proxy para acceder siempre al cliente actual de MongoDB.
    """
    def __getattr__(self, name):
        return getattr(_db_manager.client, name)


# Usar proxies en lugar de referencias directas
db = DatabaseProxy()
client = ClientProxy()
MONGO_URL = _db_manager.mongo_url
DB_NAME = _db_manager.db_name


async def ensure_indexes():
    """
    Crea los índices necesarios para un rendimiento óptimo.
    Se llama una vez al arranque del servidor.
    Todos los índices son idempotentes (create_index no falla si ya existen).
    Si MongoDB requiere autenticación o no está disponible, se registra el error sin crashear.
    """
    _db = _db_manager.db
    try:
        # --- products ---
        await _db.products.create_index([("user_id", 1), ("id", 1)], unique=True, background=True)
        await _db.products.create_index([("user_id", 1), ("supplier_id", 1)], background=True)
        await _db.products.create_index([("user_id", 1), ("ean", 1)], background=True)
        await _db.products.create_index([("user_id", 1), ("category", 1)], background=True)
        await _db.products.create_index([("user_id", 1), ("stock", 1)], background=True)
        await _db.products.create_index([("user_id", 1), ("price", 1)], background=True)
        await _db.products.create_index([("sku", 1), ("supplier_id", 1)], background=True)
        # text index para búsqueda full-text
        await _db.products.create_index(
            [("name", "text"), ("sku", "text"), ("ean", "text")],
            name="products_text_search",
            background=True,
        )
        # --- suppliers ---
        await _db.suppliers.create_index([("user_id", 1), ("id", 1)], unique=True, background=True)
        # --- catalogs ---
        await _db.catalogs.create_index([("user_id", 1), ("id", 1)], unique=True, background=True)
        # --- catalog_items ---
        await _db.catalog_items.create_index([("catalog_id", 1), ("product_id", 1)], unique=True, background=True)
        await _db.catalog_items.create_index([("catalog_id", 1), ("active", 1)], background=True)
        await _db.catalog_items.create_index([("user_id", 1)], background=True)
        # --- catalog_categories ---
        await _db.catalog_categories.create_index([("catalog_id", 1), ("id", 1)], unique=True, background=True)
        await _db.catalog_categories.create_index([("catalog_id", 1), ("parent_id", 1)], background=True)
        # --- price_history ---
        await _db.price_history.create_index([("user_id", 1), ("created_at", -1)], background=True)
        await _db.price_history.create_index([("product_id", 1), ("created_at", -1)], background=True)
        # --- notifications ---
        await _db.notifications.create_index([("user_id", 1), ("read", 1), ("created_at", -1)], background=True)
        # --- sync_history ---
        await _db.sync_history.create_index([("user_id", 1), ("started_at", -1)], background=True)
        # --- users ---
        await _db.users.create_index([("email", 1)], unique=True, background=True)
        await _db.users.create_index([("id", 1)], unique=True, background=True)
        # --- woocommerce_configs ---
        await _db.woocommerce_configs.create_index([("user_id", 1)], background=True)
        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.warning(f"No se pudieron crear los índices de MongoDB: {e}. Comprueba la URL de conexión y las credenciales.")


def get_db():
    """Obtiene la instancia de la base de datos actual."""
    return _db_manager.db


def get_client():
    """Obtiene el cliente de MongoDB actual."""
    return _db_manager.client


def reload_database_config():
    """
    Recarga la configuración de MongoDB.
    Llamar después de completar el setup para aplicar la nueva configuración.
    """
    global MONGO_URL, DB_NAME
    _db_manager.reload_config()
    MONGO_URL = _db_manager.mongo_url
    DB_NAME = _db_manager.db_name
    return True


logger.info(f"Database configured: {DB_NAME}")
