"""
Servicio de encriptación para datos sensibles (ej: contraseñas FTP).
Usa Fernet (AES-128-CBC + HMAC-SHA256) de la librería cryptography.

Requiere la variable de entorno FERNET_KEY.
Generar una clave nueva con:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_FERNET_KEY = os.environ.get("FERNET_KEY")

if not _FERNET_KEY:
    # Fallback: intentar obtener de config.json persistente
    try:
        from services.config_manager import get_config as _get_config
        _app_cfg = _get_config()
        if _app_cfg.fernet_key:
            _FERNET_KEY = _app_cfg.fernet_key
    except Exception:
        pass

if not _FERNET_KEY:
    raise RuntimeError(
        "FERNET_KEY no está configurada. Las contraseñas FTP/SFTP no pueden guardarse de forma segura. "
        "Genera una clave con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

try:
    _fernet = Fernet(_FERNET_KEY.encode())
except Exception as e:
    raise RuntimeError(f"FERNET_KEY inválida: {e}") from e


def encrypt_password(password: str) -> str:
    """Encripta una contraseña con Fernet (AES-128-CBC + HMAC-SHA256)."""
    if not password:
        return password
    try:
        return _fernet.encrypt(password.encode()).decode()
    except Exception as e:
        logger.error(f"Error encriptando contraseña: {e}")
        raise RuntimeError("No se pudo encriptar la contraseña") from e


def decrypt_password(encrypted: str) -> str:
    """
    Desencripta una contraseña.
    Si Fernet no está configurado o el valor no está encriptado, devuelve el valor original.
    """
    if not encrypted or not _fernet:
        return encrypted
    try:
        return _fernet.decrypt(encrypted.encode()).decode()
    except InvalidToken:
        # El valor puede no estar encriptado aún (datos legacy)
        return encrypted
    except Exception as e:
        logger.error(f"Error desencriptando contraseña: {e}")
        return encrypted


def is_encryption_enabled() -> bool:
    return _fernet is not None
