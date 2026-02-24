# =============================================================================
# CONFIGURACIÓN DE LA BASE DE DATOS - MongoDB
# =============================================================================
# Este archivo centraliza toda la configuración de la base de datos MongoDB.
# Los valores se obtienen de las variables de entorno definidas en .env
#
# Para configurar la conexión, modifica el archivo .env con los siguientes valores:
#   MONGO_URL      - URL de conexión a MongoDB (ej: mongodb://localhost:27017)
#   DB_NAME        - Nombre de la base de datos a utilizar
#
# =============================================================================

import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde el archivo .env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# =============================================================================
# CONFIGURACIÓN DE MONGODB
# =============================================================================

# URL de conexión a MongoDB
# Formato: mongodb://[usuario:contraseña@]host:puerto/[base_de_datos]
# Ejemplos:
#   - Local sin autenticación: mongodb://localhost:27017
#   - Local con autenticación: mongodb://admin:password@localhost:27017
#   - MongoDB Atlas: mongodb+srv://user:pass@cluster.mongodb.net/
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

# Nombre de la base de datos
# Esta es la base de datos donde se almacenarán todas las colecciones
DB_NAME = os.environ.get('DB_NAME', 'supplier_sync_db')

# =============================================================================
# OPCIONES DE CONEXIÓN (Opcionales - para ajustes avanzados)
# =============================================================================

# Tiempo máximo de espera para conexión (en milisegundos)
MONGO_CONNECT_TIMEOUT_MS = int(os.environ.get('MONGO_CONNECT_TIMEOUT_MS', 5000))

# Tiempo máximo de espera para operaciones de servidor (en milisegundos)
MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.environ.get('MONGO_SERVER_SELECTION_TIMEOUT_MS', 5000))

# Número máximo de conexiones en el pool
MONGO_MAX_POOL_SIZE = int(os.environ.get('MONGO_MAX_POOL_SIZE', 100))

# Número mínimo de conexiones en el pool
MONGO_MIN_POOL_SIZE = int(os.environ.get('MONGO_MIN_POOL_SIZE', 0))

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD JWT
# =============================================================================

# Clave secreta para firmar tokens JWT
# IMPORTANTE: Cambia este valor en producción por una clave segura y única
JWT_SECRET = os.environ.get('JWT_SECRET', 'stockhub-secret-key-2024-secure-token')

# Algoritmo de encriptación para JWT
JWT_ALGORITHM = "HS256"

# Tiempo de expiración del token (en horas)
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))

# =============================================================================
# CONFIGURACIÓN DE NOTIFICACIONES
# =============================================================================

# Umbral de cambio de precio para generar notificación (en porcentaje)
# Si el precio cambia más de este porcentaje, se generará una alerta
PRICE_CHANGE_THRESHOLD_PERCENT = float(os.environ.get('PRICE_CHANGE_THRESHOLD_PERCENT', 10.0))

# Umbral de stock bajo para generar notificación
LOW_STOCK_THRESHOLD = int(os.environ.get('LOW_STOCK_THRESHOLD', 5))

# =============================================================================
# CONFIGURACIÓN DE SINCRONIZACIÓN
# =============================================================================

# Intervalo de sincronización automática de proveedores (en horas)
SUPPLIER_SYNC_INTERVAL_HOURS = int(os.environ.get('SUPPLIER_SYNC_INTERVAL_HOURS', 6))

# Intervalo de sincronización automática de WooCommerce (en horas)
WOOCOMMERCE_SYNC_INTERVAL_HOURS = int(os.environ.get('WOOCOMMERCE_SYNC_INTERVAL_HOURS', 12))
