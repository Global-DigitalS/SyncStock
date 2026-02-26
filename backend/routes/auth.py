from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import uuid
from typing import List

from services.database import db
from services.auth import (
    hash_password, verify_password, create_token, get_current_user, 
    get_admin_user, get_superadmin_user, ROLE_PERMISSIONS, DEFAULT_LIMITS,
    get_user_resource_usage
)
from models.schemas import UserCreate, UserLogin, UserResponse, UserUpdate, UserLimits

router = APIRouter()


@router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # First user becomes superadmin
    user_count = await db.users.count_documents({})
    role = "superadmin" if user_count == 0 else "user"
    
    # Get default limits for role
    limits = DEFAULT_LIMITS.get(role, DEFAULT_LIMITS["user"])
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id, "email": user.email,
        "password": hash_password(user.password),
        "name": user.name, "company": user.company,
        "role": role,
        "max_suppliers": limits["max_suppliers"],
        "max_catalogs": limits["max_catalogs"],
        "max_woocommerce_stores": limits["max_woocommerce_stores"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, role)
    
    # Send welcome email (async, don't block registration)
    try:
        from routes.email import send_welcome_email
        await send_welcome_email(user.email, user.name)
    except Exception as e:
        # Don't fail registration if email fails
        import logging
        logging.getLogger(__name__).warning(f"Failed to send welcome email: {e}")
    
    return {
        "token": token,
        "user": {
            "id": user_id, "email": user.email, "name": user.name, 
            "company": user.company, "role": role,
            "max_suppliers": limits["max_suppliers"],
            "max_catalogs": limits["max_catalogs"],
            "max_woocommerce_stores": limits["max_woocommerce_stores"]
        }
    }


@router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    role = user.get("role", "user")
    token = create_token(user["id"], role)
    return {
        "token": token,
        "user": {
            "id": user["id"], "email": user["email"], "name": user["name"],
            "company": user.get("company"), "role": role,
            "max_suppliers": user.get("max_suppliers", DEFAULT_LIMITS.get(role, {}).get("max_suppliers", 10)),
            "max_catalogs": user.get("max_catalogs", DEFAULT_LIMITS.get(role, {}).get("max_catalogs", 5)),
            "max_woocommerce_stores": user.get("max_woocommerce_stores", DEFAULT_LIMITS.get(role, {}).get("max_woocommerce_stores", 2))
        }
    }


@router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**user)


@router.get("/auth/permissions")
async def get_my_permissions(user: dict = Depends(get_current_user)):
    """Get current user's permissions based on role"""
    role = user.get("role", "user")
    return {
        "role": role,
        "permissions": ROLE_PERMISSIONS.get(role, [])
    }


@router.get("/auth/limits")
async def get_my_limits(user: dict = Depends(get_current_user)):
    """Get current user's resource limits and usage"""
    usage = await get_user_resource_usage(user)
    return usage


# ==================== USER MANAGEMENT (Admin/SuperAdmin) ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(admin: dict = Depends(get_admin_user)):
    """List all users (admin/superadmin only)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]


@router.get("/users/{user_id}")
async def get_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Get user details with resource usage"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usage = await get_user_resource_usage(user)
    return {**user, "usage": usage}


@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, admin: dict = Depends(get_admin_user)):
    """Update user role (admin/superadmin only)"""
    # Only superadmin can assign superadmin or admin roles
    if role in ["superadmin", "admin"] and admin.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Solo SuperAdmin puede asignar roles de admin")
    
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Rol inválido. Roles válidos: {list(ROLE_PERMISSIONS.keys())}")
    
    # Prevent changing own role
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol")
    
    # Get default limits for new role
    limits = DEFAULT_LIMITS.get(role, DEFAULT_LIMITS["user"])
    
    result = await db.users.update_one(
        {"id": user_id}, 
        {"$set": {
            "role": role,
            "max_suppliers": limits["max_suppliers"],
            "max_catalogs": limits["max_catalogs"],
            "max_woocommerce_stores": limits["max_woocommerce_stores"]
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": f"Rol actualizado a '{role}' con límites por defecto"}


@router.put("/users/{user_id}/limits")
async def update_user_limits(user_id: str, limits: UserLimits, superadmin: dict = Depends(get_superadmin_user)):
    """Update user resource limits (superadmin only)"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "max_suppliers": limits.max_suppliers,
            "max_catalogs": limits.max_catalogs,
            "max_woocommerce_stores": limits.max_woocommerce_stores
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Límites actualizados correctamente"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Delete user (admin/superadmin only)"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    # Only superadmin can delete admins
    target_user = await db.users.find_one({"id": user_id})
    if target_user and target_user.get("role") in ["admin", "superadmin"] and admin.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Solo SuperAdmin puede eliminar administradores")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Usuario eliminado"}
