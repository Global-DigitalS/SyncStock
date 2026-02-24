from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
import uuid
from typing import List

from services.database import db
from services.auth import hash_password, verify_password, create_token, get_current_user, get_admin_user, ROLE_PERMISSIONS
from models.schemas import UserCreate, UserLogin, UserResponse, UserUpdate

router = APIRouter()


@router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # First user becomes admin
    user_count = await db.users.count_documents({})
    role = "admin" if user_count == 0 else "user"
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id, "email": user.email,
        "password": hash_password(user.password),
        "name": user.name, "company": user.company,
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, role)
    return {
        "token": token,
        "user": {"id": user_id, "email": user.email, "name": user.name, "company": user.company, "role": role}
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
            "company": user.get("company"), "role": role
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


# ==================== USER MANAGEMENT (Admin only) ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(admin: dict = Depends(get_admin_user)):
    """List all users (admin only)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [UserResponse(**u) for u in users]


@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, admin: dict = Depends(get_admin_user)):
    """Update user role (admin only)"""
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Rol inválido. Roles válidos: {list(ROLE_PERMISSIONS.keys())}")
    
    # Prevent admin from demoting themselves
    if user_id == admin["id"] and role != "admin":
        raise HTTPException(status_code=400, detail="No puedes cambiar tu propio rol de administrador")
    
    result = await db.users.update_one({"id": user_id}, {"$set": {"role": role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": f"Rol actualizado a '{role}'"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Delete user (admin only)"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Usuario eliminado"}
