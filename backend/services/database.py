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
        await _db.products.create_index([("user_id", 1), ("id", 1)], unique=True)
        await _db.products.create_index([("user_id", 1), ("supplier_id", 1)])
        await _db.products.create_index([("user_id", 1), ("ean", 1)])
        await _db.products.create_index([("user_id", 1), ("category", 1)])
        await _db.products.create_index([("user_id", 1), ("stock", 1)])
        await _db.products.create_index([("user_id", 1), ("price", 1)])
        # Índice compuesto para upsert por SKU + proveedor (incluye user_id para multi-tenancy)
        await _db.products.create_index([("user_id", 1), ("supplier_id", 1), ("sku", 1)], unique=True)
        # Índices para filtrado por subcategorías
        await _db.products.create_index([("user_id", 1), ("supplier_id", 1), ("category", 1), ("subcategory", 1)])
        await _db.products.create_index([("user_id", 1), ("supplier_id", 1), ("subcategory", 1)])
        await _db.products.create_index([("user_id", 1), ("supplier_id", 1), ("subcategory2", 1)])
        # Índice para filtrado por selección de productos
        await _db.products.create_index([("user_id", 1), ("supplier_id", 1), ("is_selected", 1)])
        await _db.products.create_index([("user_id", 1), ("is_selected", 1)])
        # text index para búsqueda full-text
        await _db.products.create_index(
            [("name", "text"), ("sku", "text"), ("ean", "text")],
            name="products_text_search",
        )
        # --- suppliers ---
        await _db.suppliers.create_index([("user_id", 1), ("id", 1)], unique=True)
        # --- catalogs ---
        await _db.catalogs.create_index([("user_id", 1), ("id", 1)], unique=True)
        # --- catalog_items ---
        await _db.catalog_items.create_index([("catalog_id", 1), ("product_id", 1)], unique=True)
        await _db.catalog_items.create_index([("catalog_id", 1), ("active", 1)])
        await _db.catalog_items.create_index([("user_id", 1)])
        # --- catalog_categories ---
        await _db.catalog_categories.create_index([("catalog_id", 1), ("id", 1)], unique=True)
        await _db.catalog_categories.create_index([("catalog_id", 1), ("parent_id", 1)])
        # --- price_history ---
        await _db.price_history.create_index([("user_id", 1), ("created_at", -1)])
        await _db.price_history.create_index([("product_id", 1), ("created_at", -1)])
        # --- notifications ---
        await _db.notifications.create_index([("user_id", 1), ("read", 1), ("created_at", -1)])
        # --- sync_history ---
        await _db.sync_history.create_index([("user_id", 1), ("started_at", -1)])
        # --- users ---
        await _db.users.create_index([("email", 1)], unique=True)
        await _db.users.create_index([("id", 1)], unique=True)
        # --- woocommerce_configs ---
        await _db.woocommerce_configs.create_index([("user_id", 1)])
        # --- sync_status (NEW: for optimized sync queue) ---
        await _db.sync_status.create_index([("id", 1)], unique=True)
        await _db.sync_status.create_index([("user_id", 1), ("created_at", -1)])
        await _db.sync_status.create_index([("status", 1), ("created_at", -1)])
        await _db.sync_status.create_index([("user_id", 1), ("status", 1)])
        # --- login_attempts (for account lockout) ---
        await _db.login_attempts.create_index([("email", 1)])
        await _db.login_attempts.create_index([("locked_until", 1)], expireAfterSeconds=0)  # TTL index
        # --- token_blacklist (revoked refresh tokens) ---
        await _db.token_blacklist.create_index([("jti", 1)], unique=True)
        await _db.token_blacklist.create_index([("expires_at", 1)], expireAfterSeconds=0)  # TTL auto-cleanup
        # --- competitors (monitorización de precios) ---
        await _db.competitors.create_index([("user_id", 1), ("id", 1)], unique=True)
        await _db.competitors.create_index([("user_id", 1), ("active", 1)])
        # --- price_snapshots (capturas de precios de competidores) ---
        await _db.price_snapshots.create_index([("sku", 1), ("competitor_id", 1), ("scraped_at", -1)])
        await _db.price_snapshots.create_index([("ean", 1), ("competitor_id", 1), ("scraped_at", -1)])
        await _db.price_snapshots.create_index([("competitor_id", 1), ("scraped_at", -1)])
        await _db.price_snapshots.create_index([("user_id", 1), ("scraped_at", -1)])
        # --- price_alerts (alertas de precio configuradas por el usuario) ---
        await _db.price_alerts.create_index([("user_id", 1), ("id", 1)], unique=True)
        await _db.price_alerts.create_index([("user_id", 1), ("active", 1)])
        await _db.price_alerts.create_index([("sku", 1), ("active", 1)])
        await _db.price_alerts.create_index([("ean", 1), ("active", 1)])
        # --- pending_matches (matches de baja confianza pendientes de revisión) ---
        await _db.pending_matches.create_index([("user_id", 1), ("status", 1)])
        await _db.pending_matches.create_index([("sku", 1)])

        # === ÍNDICES DE OPTIMIZACIÓN (rendimiento) ===
        # products: búsqueda directa por SKU del usuario
        await _db.products.create_index([("user_id", 1), ("sku", 1)])
        # catalog_margin_rules: búsquedas por usuario y por catálogo+prioridad
        await _db.catalog_margin_rules.create_index([("user_id", 1)])
        await _db.catalog_margin_rules.create_index([("catalog_id", 1), ("priority", -1)])
        # woocommerce_configs: filtro por conexión activa y por catálogo
        await _db.woocommerce_configs.create_index([("user_id", 1), ("is_connected", 1)])
        await _db.woocommerce_configs.create_index([("user_id", 1), ("catalog_id", 1)])
        # store_configs: tiendas online multi-plataforma
        await _db.store_configs.create_index([("user_id", 1)])
        await _db.store_configs.create_index([("user_id", 1), ("is_connected", 1)])
        # crm_connections y sync_jobs
        await _db.crm_connections.create_index([("user_id", 1)])
        await _db.sync_jobs.create_index([("connection_id", 1), ("user_id", 1), ("started_at", -1)])
        # catalog_items: índice compuesto para queries con user_id + active
        await _db.catalog_items.create_index([("user_id", 1), ("active", 1)])
        # marketplace_connections
        await _db.marketplace_connections.create_index([("user_id", 1)])

        # === TTL INDEXES - Limpieza automática de datos antiguos ===
        # price_history: eliminar registros > 180 días (6 meses)
        await _db.price_history.create_index(
            [("created_at", 1)], expireAfterSeconds=15552000, name="ttl_price_history_180d"
        )
        # notifications: eliminar notificaciones > 90 días
        await _db.notifications.create_index(
            [("created_at", 1)], expireAfterSeconds=7776000, name="ttl_notifications_90d"
        )
        # price_snapshots: eliminar snapshots > 90 días
        await _db.price_snapshots.create_index(
            [("scraped_at", 1)], expireAfterSeconds=7776000, name="ttl_price_snapshots_90d"
        )
        # sync_history: eliminar historial > 90 días
        await _db.sync_history.create_index(
            [("started_at", 1)], expireAfterSeconds=7776000, name="ttl_sync_history_90d"
        )
        # sync_status: eliminar estados > 30 días
        await _db.sync_status.create_index(
            [("created_at", 1)], expireAfterSeconds=2592000, name="ttl_sync_status_30d"
        )
        # sync_jobs: eliminar jobs > 90 días
        await _db.sync_jobs.create_index(
            [("started_at", 1)], expireAfterSeconds=7776000, name="ttl_sync_jobs_90d"
        )

        logger.info("MongoDB indexes ensured (incluidos índices de optimización y TTL)")
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
