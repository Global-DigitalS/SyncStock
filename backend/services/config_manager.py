"""
Gestión de configuración de la aplicación.
Permite configurar la aplicación completamente desde la interfaz web.
La configuración se guarda en un archivo JSON y se carga al iniciar.
"""
import os
import json
import secrets
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Ruta del archivo de configuración
CONFIG_DIR = Path(__file__).parent.parent
CONFIG_FILE = CONFIG_DIR / "config.json"


class AppConfig(BaseModel):
    """Modelo de configuración de la aplicación"""
    mongo_url: str = ""
    db_name: str = "supplier_sync_db"
    jwt_secret: str = ""
    cors_origins: str = "*"
    is_configured: bool = False


def generate_jwt_secret() -> str:
    """Genera un JWT secret seguro"""
    return secrets.token_urlsafe(64)


def load_config() -> AppConfig:
    """
    Carga la configuración desde el archivo JSON.
    Si no existe, crea una configuración vacía.
    También considera las variables de entorno como fallback.
    """
    config = AppConfig()
    
    # Primero intentar cargar desde archivo
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                config = AppConfig(**data)
                logger.info(f"Configuration loaded from {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    # Fallback a variables de entorno si el archivo no tiene valores
    if not config.mongo_url:
        config.mongo_url = os.environ.get('MONGO_URL', '')
    if not config.db_name:
        config.db_name = os.environ.get('DB_NAME', 'supplier_sync_db')
    if not config.jwt_secret:
        config.jwt_secret = os.environ.get('JWT_SECRET', '')
    if config.cors_origins == "*":
        env_cors = os.environ.get('CORS_ORIGINS', '*')
        if env_cors:
            config.cors_origins = env_cors
    
    return config


def save_config(config: AppConfig) -> bool:
    """
    Guarda la configuración en el archivo JSON.
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config.model_dump(), f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving config file: {e}")
        return False


def get_config() -> AppConfig:
    """
    Obtiene la configuración actual.
    """
    return load_config()


def update_config(
    mongo_url: Optional[str] = None,
    db_name: Optional[str] = None,
    jwt_secret: Optional[str] = None,
    cors_origins: Optional[str] = None,
    is_configured: Optional[bool] = None
) -> AppConfig:
    """
    Actualiza la configuración con los valores proporcionados.
    """
    config = load_config()
    
    if mongo_url is not None:
        config.mongo_url = mongo_url
    if db_name is not None:
        config.db_name = db_name
    if jwt_secret is not None:
        config.jwt_secret = jwt_secret
    if cors_origins is not None:
        config.cors_origins = cors_origins
    if is_configured is not None:
        config.is_configured = is_configured
    
    save_config(config)
    return config


def is_app_configured() -> bool:
    """
    Verifica si la aplicación está configurada.
    """
    config = load_config()
    return config.is_configured and bool(config.mongo_url) and bool(config.jwt_secret)


def ensure_jwt_secret() -> str:
    """
    Asegura que existe un JWT secret.
    Si no existe, genera uno nuevo y lo guarda.
    """
    config = load_config()
    
    if not config.jwt_secret:
        config.jwt_secret = generate_jwt_secret()
        save_config(config)
        logger.info("Generated new JWT secret")
    
    return config.jwt_secret
