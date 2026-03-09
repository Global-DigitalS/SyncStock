"""
Servicio de encriptación para datos sensibles (ej: contraseñas FTP).
Usa Fernet (AES-128-CBC + HMAC-SHA256) de la librería cryptography.

Requiere la variable de entorno FERNET_KEY.
Generar una clave nueva con:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_FERNET_KEY = os.environ.get("FERNET_KEY")

if not _FERNET_KEY:
    logger.warning(
        "FERNET_KEY no configurada. Las contraseñas FTP se guardarán sin encriptar. "
        "Genera una clave con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )
    _fernet = None
else:
    try:
        _fernet = Fernet(_FERNET_KEY.encode())
    except Exception as e:
        logger.error(f"FERNET_KEY inválida: {e}")
        _fernet = None


def encrypt_password(password: str) -> str:
    """Encripta una contraseña. Si Fernet no está configurado, devuelve el valor original."""
    if not password or not _fernet:
        return password
    try:
        return _fernet.encrypt(password.encode()).decode()
    except Exception as e:
        logger.error(f"Error encriptando contraseña: {e}")
        return password


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
