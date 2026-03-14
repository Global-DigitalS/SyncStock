import jwt
import bcrypt
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.database import db

# Cargar JWT config desde config_manager o variables de entorno
try:
    from services.config_manager import get_config, ensure_jwt_secret
    config = get_config()
    JWT_SECRET = config.jwt_secret if config.jwt_secret else ensure_jwt_secret()
except ImportError:
    JWT_SECRET = os.environ.get('JWT_SECRET')

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET no está configurado. "
        "Define la variable de entorno JWT_SECRET con un valor aleatorio seguro (mín. 64 chars). "
        "Ejemplo: python -c \"import secrets; print(secrets.token_hex(64))\""
    )

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 168))  # 7 días por defecto

security = HTTPBearer(auto_error=False)

# Role permissions - superadmin tiene control total
ROLE_PERMISSIONS = {
    "superadmin": ["read", "write", "delete", "manage_users", "manage_limits", "manage_settings", "sync", "export", "unlimited"],
    "admin": ["read", "write", "delete", "manage_settings", "sync", "export"],
    "user": ["read", "write", "delete", "sync", "export"],
    "viewer": ["read"]
}

# Default limits for new users
DEFAULT_LIMITS = {
    "superadmin": {"max_suppliers": 999999, "max_catalogs": 999999, "max_woocommerce_stores": 999999},
    "admin": {"max_suppliers": 50, "max_catalogs": 20, "max_woocommerce_stores": 10},
    "user": {"max_suppliers": 10, "max_catalogs": 5, "max_woocommerce_stores": 2},
    "viewer": {"max_suppliers": 0, "max_catalogs": 0, "max_woocommerce_stores": 0}
}


# Pre-computed dummy hash used for constant-time comparison when a user is not found,
# preventing timing-based email enumeration attacks.
_DUMMY_HASH = bcrypt.hashpw(b"__dummy__", bcrypt.gensalt()).decode("utf-8")

# ── Lockout configuration ──────────────────────────────────────────────────────
_MAX_FAILED_ATTEMPTS = 5          # lock after this many consecutive failures
_LOCKOUT_MINUTES = 15             # lock duration in minutes
_ATTEMPT_WINDOW_MINUTES = 15      # rolling window for counting failures


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def validate_password_strength(password: str) -> None:
    """
    Raise ValueError if the password does not meet complexity requirements:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una letra minúscula")
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe contener al menos un número")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("La contraseña debe contener al menos un carácter especial (!@#$%^&* …)")


def create_token(user_id: str, role: str = "user") -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def check_permission(user: dict, permission: str) -> bool:
    """Check if user has a specific permission"""
    role = user.get("role", "user")
    permissions = ROLE_PERMISSIONS.get(role, [])
    return permission in permissions


def require_permission(permission: str):
    """Decorator factory to check permissions"""
    async def permission_checker(user: dict = Depends(get_current_user)):
        if not check_permission(user, permission):
            raise HTTPException(status_code=403, detail=f"No tienes permiso para: {permission}")
        return user
    return permission_checker


async def check_user_limit(user: dict, resource_type: str) -> bool:
    """Check if user has reached their resource limit"""
    role = user.get("role", "user")
    
    # Superadmin has no limits
    if role == "superadmin" or "unlimited" in ROLE_PERMISSIONS.get(role, []):
        return True
    
    limit_field = f"max_{resource_type}"
    user_limit = user.get(limit_field, DEFAULT_LIMITS.get(role, {}).get(limit_field, 0))
    
    # Count current resources
    if resource_type == "suppliers":
        count = await db.suppliers.count_documents({"user_id": user["id"]})
    elif resource_type == "catalogs":
        count = await db.catalogs.count_documents({"user_id": user["id"]})
    elif resource_type == "woocommerce_stores":
        count = await db.woocommerce_configs.count_documents({"user_id": user["id"]})
    else:
        return True
    
    return count < user_limit


async def get_user_resource_usage(user: dict) -> dict:
    """Get current resource usage for a user"""
    suppliers = await db.suppliers.count_documents({"user_id": user["id"]})
    catalogs = await db.catalogs.count_documents({"user_id": user["id"]})
    stores = await db.woocommerce_configs.count_documents({"user_id": user["id"]})
    
    role = user.get("role", "user")
    defaults = DEFAULT_LIMITS.get(role, DEFAULT_LIMITS["user"])
    
    return {
        "suppliers": {"used": suppliers, "max": user.get("max_suppliers", defaults["max_suppliers"])},
        "catalogs": {"used": catalogs, "max": user.get("max_catalogs", defaults["max_catalogs"])},
        "woocommerce_stores": {"used": stores, "max": user.get("max_woocommerce_stores", defaults["max_woocommerce_stores"])}
    }


async def _extract_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    """Extract JWT token from httpOnly cookie or Authorization header."""
    token = request.cookies.get("auth_token")
    if not token and credentials:
        token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    return token


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    token = await _extract_token(request, credentials)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        if "role" not in user:
            user["role"] = "user"
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


async def get_admin_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Get current user and verify admin role"""
    user = await get_current_user(request, credentials)
    if user.get("role") not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador")
    return user


async def get_superadmin_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Get current user and verify superadmin role"""
    user = await get_current_user(request, credentials)
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Se requiere rol de SuperAdmin")
    return user


# ── Account lockout helpers ────────────────────────────────────────────────────

async def check_account_lockout(email: str) -> None:
    """Raise 429 if the account is currently locked out."""
    now = datetime.now(timezone.utc)
    record = await db.login_attempts.find_one({"email": email})
    if not record:
        return
    locked_until = record.get("locked_until")
    if locked_until:
        lu = datetime.fromisoformat(locked_until)
        if lu.tzinfo is None:
            lu = lu.replace(tzinfo=timezone.utc)
        if now < lu:
            remaining = int((lu - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Cuenta bloqueada por demasiados intentos fallidos. Inténtalo en {remaining} minutos."
            )


async def record_failed_login(email: str) -> None:
    """Increment failed-attempt counter and lock if threshold reached."""
    now = datetime.now(timezone.utc)
    window_start = (now - timedelta(minutes=_ATTEMPT_WINDOW_MINUTES)).isoformat()

    record = await db.login_attempts.find_one({"email": email})
    attempts = 1
    if record:
        # Count attempts within the rolling window only
        last = record.get("last_attempt", "")
        if last and last >= window_start:
            attempts = record.get("attempts", 0) + 1
        # else window expired, reset

    update: dict = {
        "email": email,
        "attempts": attempts,
        "last_attempt": now.isoformat(),
    }
    if attempts >= _MAX_FAILED_ATTEMPTS:
        update["locked_until"] = (now + timedelta(minutes=_LOCKOUT_MINUTES)).isoformat()

    await db.login_attempts.update_one(
        {"email": email}, {"$set": update}, upsert=True
    )


async def reset_failed_logins(email: str) -> None:
    """Clear failed-attempt counter after a successful login."""
    await db.login_attempts.delete_one({"email": email})
