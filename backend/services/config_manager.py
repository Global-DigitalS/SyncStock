"""
Gestión de configuración de la aplicación.
Permite configurar la aplicación completamente desde la interfaz web.
La configuración se guarda en un archivo JSON FUERA del directorio de la aplicación
para que persista entre actualizaciones.

Ubicaciones de configuración (en orden de prioridad):
0. Variable de entorno CONFIG_PATH (establecida por install.sh/update.sh para instalaciones de dominio)
1. /etc/syncstock/config.json (producción - persistente entre actualizaciones)
2. /etc/syncstock/<subdir>/config.json (instalaciones multi-dominio de Plesk)
3. ~/.syncstock/config.json (desarrollo local)
4. [APP_DIR]/backend/config.json (fallback, sobrescrito en actualizaciones)
"""
import os
import json
import secrets
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Rutas de configuración en orden de prioridad
SYSTEM_CONFIG_DIR = Path("/etc/syncstock")
USER_CONFIG_DIR = Path.home() / ".syncstock"
APP_CONFIG_DIR = Path(__file__).parent.parent

# Determinar la ruta del archivo de configuración
def get_config_path() -> Path:
    """
    Determina la ruta del archivo de configuración.
    Prioriza ubicaciones persistentes que no se sobrescriben en actualizaciones.
    """
    # 0. Variable de entorno CONFIG_PATH (instalaciones Plesk con dominio específico)
    env_config_path = os.environ.get('CONFIG_PATH', '').strip()
    if env_config_path:
        env_config = Path(env_config_path)
        if env_config.exists():
            logger.info(f"Using config from CONFIG_PATH env var: {env_config}")
            return env_config

    # 1. Ubicación del sistema (producción) - más persistente
    system_config = SYSTEM_CONFIG_DIR / "config.json"
    if system_config.exists():
        return system_config

    # 2. Buscar en subdirectorios de /etc/syncstock/ (instalaciones multi-dominio Plesk)
    if SYSTEM_CONFIG_DIR.exists():
        for subdir in sorted(SYSTEM_CONFIG_DIR.iterdir()):
            if subdir.is_dir():
                candidate = subdir / "config.json"
                if candidate.exists():
                    logger.info(f"Found domain-specific config: {candidate}")
                    return candidate

    # 3. Ubicación del usuario (desarrollo)
    user_config = USER_CONFIG_DIR / "config.json"
    if user_config.exists():
        return user_config

    # 4. Ubicación de la aplicación (fallback)
    app_config = APP_CONFIG_DIR / "config.json"
    if app_config.exists():
        return app_config

    # Si no existe ninguno, usar la ubicación del sistema si es posible crear
    try:
        SYSTEM_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return system_config
    except PermissionError:
        # Si no tenemos permisos, usar ubicación del usuario
        try:
            USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            return user_config
        except Exception:
            # Último recurso: ubicación de la aplicación
            return app_config

CONFIG_FILE = get_config_path()


class AppConfig(BaseModel):
    """Modelo de configuración de la aplicación"""
    mongo_url: str = ""
    db_name: str = "syncstock_db"
    jwt_secret: str = ""
    fernet_key: str = ""
    cors_origins: str = "*"
    is_configured: bool = False
    # SMTP Email Configuration
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "SyncStock"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_configured: bool = False


def generate_jwt_secret() -> str:
    """Genera un JWT secret seguro"""
    return secrets.token_urlsafe(64)


def _get_all_config_locations() -> list:
    """Devuelve todas las ubicaciones posibles del archivo de configuración en orden de prioridad."""
    locations = []
    # 0. CONFIG_PATH env var (Plesk domain-specific installs)
    env_config_path = os.environ.get('CONFIG_PATH', '').strip()
    if env_config_path:
        locations.append(Path(env_config_path))
    # 1. Ubicación del sistema
    locations.append(SYSTEM_CONFIG_DIR / "config.json")
    # 2. Subdirectorios de dominio bajo /etc/syncstock/ (Plesk multi-dominio)
    if SYSTEM_CONFIG_DIR.exists():
        for subdir in sorted(SYSTEM_CONFIG_DIR.iterdir()):
            if subdir.is_dir():
                locations.append(subdir / "config.json")
    # 3. Ubicación del usuario
    locations.append(USER_CONFIG_DIR / "config.json")
    # 4. Ubicación de la aplicación (fallback)
    locations.append(APP_CONFIG_DIR / "config.json")
    return locations


def load_config() -> AppConfig:
    """
    Carga la configuración desde el archivo JSON.
    Busca en múltiples ubicaciones para soportar migración y persistencia.
    También considera las variables de entorno como fallback.
    """
    global CONFIG_FILE
    config = AppConfig()

    # Buscar configuración en todas las ubicaciones posibles
    config_locations = _get_all_config_locations()
    
    config_loaded = False
    for config_path in config_locations:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    config = AppConfig(**data)
                    CONFIG_FILE = config_path  # Actualizar la ruta actual
                    logger.info(f"Configuration loaded from {config_path}")
                    config_loaded = True
                    
                    # Si encontramos config en ubicación de app, migrar a ubicación persistente
                    if str(config_path).startswith(str(APP_CONFIG_DIR)) and config.is_configured:
                        try:
                            SYSTEM_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                            new_path = SYSTEM_CONFIG_DIR / "config.json"
                            with open(new_path, 'w') as nf:
                                json.dump(data, nf, indent=2)
                            CONFIG_FILE = new_path
                            logger.info(f"Configuration migrated to persistent location: {new_path}")
                        except Exception as e:
                            logger.warning(f"Could not migrate config: {e}")
                    
                    break
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
    
    if not config_loaded:
        logger.info("No configuration file found, using defaults/environment")
    
    # Fallback a variables de entorno si el archivo no tiene valores
    if not config.mongo_url:
        config.mongo_url = os.environ.get('MONGO_URL', '')
    if not config.db_name:
        config.db_name = os.environ.get('DB_NAME', 'syncstock_db')
    if not config.jwt_secret:
        config.jwt_secret = os.environ.get('JWT_SECRET', '')
    if not config.fernet_key:
        config.fernet_key = os.environ.get('FERNET_KEY', '')
    if config.cors_origins == "*":
        env_cors = os.environ.get('CORS_ORIGINS', '*')
        if env_cors:
            config.cors_origins = env_cors
    
    return config


def save_config(config: AppConfig) -> bool:
    """
    Guarda la configuración en el archivo JSON y actualiza el .env
    Intenta guardar en ubicación persistente (/etc/syncstock) primero.
    """
    global CONFIG_FILE
    
    try:
        # Intentar guardar en ubicación del sistema primero
        config_path = CONFIG_FILE
        config_dir = config_path.parent
        
        # Si estamos en ubicación de app, intentar migrar a ubicación del sistema
        if str(config_path).startswith(str(APP_CONFIG_DIR)):
            try:
                SYSTEM_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                config_path = SYSTEM_CONFIG_DIR / "config.json"
                config_dir = SYSTEM_CONFIG_DIR
                CONFIG_FILE = config_path  # Actualizar la variable global
                logger.info(f"Migrating config to persistent location: {config_path}")
            except PermissionError:
                logger.warning(f"Cannot create system config dir, using: {config_path}")
        
        # Asegurar que el directorio existe
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar en config.json
        with open(config_path, 'w') as f:
            json.dump(config.model_dump(), f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
        
        # También actualizar el archivo .env para compatibilidad
        env_file = APP_CONFIG_DIR / ".env"
        env_lines = [
            f"MONGO_URL={config.mongo_url}",
            f"DB_NAME={config.db_name}",
            f"CORS_ORIGINS={config.cors_origins}",
        ]
        if config.jwt_secret:
            env_lines.append(f"JWT_SECRET={config.jwt_secret}")
        if config.fernet_key:
            env_lines.append(f"FERNET_KEY={config.fernet_key}")
        env_content = "\n".join(env_lines) + "\n"
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            logger.info(f"Environment file updated: {env_file}")
        except Exception as e:
            logger.warning(f"Could not update .env file: {e}")
        
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
    is_configured: Optional[bool] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
    smtp_from_email: Optional[str] = None,
    smtp_from_name: Optional[str] = None,
    smtp_use_tls: Optional[bool] = None,
    smtp_use_ssl: Optional[bool] = None,
    smtp_configured: Optional[bool] = None
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
    # SMTP fields
    if smtp_host is not None:
        config.smtp_host = smtp_host
    if smtp_port is not None:
        config.smtp_port = smtp_port
    if smtp_user is not None:
        config.smtp_user = smtp_user
    if smtp_password is not None:
        config.smtp_password = smtp_password
    if smtp_from_email is not None:
        config.smtp_from_email = smtp_from_email
    if smtp_from_name is not None:
        config.smtp_from_name = smtp_from_name
    if smtp_use_tls is not None:
        config.smtp_use_tls = smtp_use_tls
    if smtp_use_ssl is not None:
        config.smtp_use_ssl = smtp_use_ssl
    if smtp_configured is not None:
        config.smtp_configured = smtp_configured
    
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



def get_config_info() -> dict:
    """
    Devuelve información sobre la ubicación y estado de la configuración.
    Útil para debugging y para mostrar al usuario dónde se guarda la config.
    """
    config = load_config()
    
    return {
        "config_path": str(CONFIG_FILE),
        "is_persistent": str(CONFIG_FILE).startswith("/etc/syncstock"),
        "is_configured": config.is_configured,
        "locations_checked": [
            {"path": str(p), "exists": p.exists(), "type": "config"}
            for p in _get_all_config_locations()
        ],
        "recommendation": "La configuración se guarda en /etc/syncstock/ para persistir entre actualizaciones." if str(CONFIG_FILE).startswith("/etc/syncstock") else "Considera mover la configuración a /etc/syncstock/ para que persista entre actualizaciones."
    }


def backup_config() -> Optional[str]:
    """
    Crea una copia de seguridad de la configuración actual.
    Útil antes de actualizar la aplicación.
    """
    config = load_config()
    if not config.is_configured:
        return None
    
    from datetime import datetime
    backup_dir = SYSTEM_CONFIG_DIR / "backups"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"config_backup_{timestamp}.json"
        
        with open(backup_path, 'w') as f:
            json.dump(config.model_dump(), f, indent=2)
        
        logger.info(f"Configuration backup created: {backup_path}")
        return str(backup_path)
    except Exception as e:
        logger.error(f"Could not create backup: {e}")
        return None


def restore_config(backup_path: str) -> bool:
    """
    Restaura la configuración desde una copia de seguridad.
    """
    try:
        with open(backup_path, 'r') as f:
            data = json.load(f)
            config = AppConfig(**data)
            save_config(config)
            logger.info(f"Configuration restored from {backup_path}")
            return True
    except Exception as e:
        logger.error(f"Could not restore backup: {e}")
        return False


def list_backups() -> list:
    """
    Lista las copias de seguridad disponibles.
    """
    backup_dir = SYSTEM_CONFIG_DIR / "backups"
    backups = []
    
    if backup_dir.exists():
        for backup_file in sorted(backup_dir.glob("config_backup_*.json"), reverse=True):
            backups.append({
                "path": str(backup_file),
                "filename": backup_file.name,
                "created": backup_file.stat().st_mtime
            })
    
    return backups
