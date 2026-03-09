import jwt
import bcrypt
import os
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
    JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-change-in-production')

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


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


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
