from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta
import uuid
import secrets
from typing import List
from pydantic import BaseModel, EmailStr

from services.database import db
from services.auth import (
    hash_password, verify_password, create_token, get_current_user, 
    get_admin_user, get_superadmin_user, ROLE_PERMISSIONS, DEFAULT_LIMITS,
    get_user_resource_usage
)
from services.sanitizer import sanitize_string, sanitize_email, sanitize_password, sanitize_dict
from models.schemas import UserCreate, UserLogin, UserResponse, UserUpdate, UserLimits, UserFullUpdate
from services.email_service import get_email_service, get_password_reset_email_template
from services.config_manager import get_config
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== PASSWORD RESET MODELS ====================

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    # Sanitize inputs
    email = sanitize_email(user.email)
    name = sanitize_string(user.name, max_length=100)
    company = sanitize_string(user.company, max_length=200) if user.company else None
    password = sanitize_password(user.password)
    
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # First user becomes superadmin
    user_count = await db.users.count_documents({})
    role = "superadmin" if user_count == 0 else "user"
    
    # Get default limits for role
    limits = DEFAULT_LIMITS.get(role, DEFAULT_LIMITS["user"])
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id, "email": email,
        "password": hash_password(password),
        "name": name, "company": company,
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
        await send_welcome_email(email, name)
    except Exception as e:
        # Don't fail registration if email fails
        import logging
        logging.getLogger(__name__).warning(f"Failed to send welcome email: {e}")
    
    return {
        "token": token,
        "user": {
            "id": user_id, "email": email, "name": name, 
            "company": company, "role": role,
            "max_suppliers": limits["max_suppliers"],
            "max_catalogs": limits["max_catalogs"],
            "max_woocommerce_stores": limits["max_woocommerce_stores"]
        }
    }


@router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    # Sanitize inputs
    email = sanitize_email(credentials.email)
    password = sanitize_password(credentials.password)
    
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="USER_NOT_FOUND")
    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="INVALID_PASSWORD")
    
    # Check if user is active
    if user.get("is_active") == False:
        raise HTTPException(status_code=403, detail="ACCOUNT_DISABLED")
    
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


@router.get("/users/{user_id}/stats")
async def get_user_stats(user_id: str, superadmin: dict = Depends(get_superadmin_user)):
    """Get detailed statistics for a user (SuperAdmin only)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Get resource counts
    suppliers_count = await db.suppliers.count_documents({"user_id": user_id})
    catalogs_count = await db.catalogs.count_documents({"user_id": user_id})
    products_count = await db.products.count_documents({"user_id": user_id})
    stores_count = await db.woocommerce_stores.count_documents({"user_id": user_id})
    
    # Get recent activity
    recent_syncs = await db.sync_history.find(
        {"user_id": user_id}
    ).sort("started_at", -1).limit(5).to_list(5)
    
    # Clean sync history for response
    for sync in recent_syncs:
        if "_id" in sync:
            del sync["_id"]
    
    # Get payment history
    payments = await db.payment_transactions.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    for payment in payments:
        if "_id" in payment:
            del payment["_id"]
    
    # Get subscription plan details if exists
    subscription_plan = None
    if user.get("subscription_plan_id"):
        subscription_plan = await db.subscription_plans.find_one(
            {"id": user.get("subscription_plan_id")},
            {"_id": 0}
        )
    
    return {
        "user": user,
        "usage": {
            "suppliers": suppliers_count,
            "catalogs": catalogs_count,
            "products": products_count,
            "stores": stores_count
        },
        "limits": {
            "max_suppliers": user.get("max_suppliers", 10),
            "max_catalogs": user.get("max_catalogs", 5),
            "max_products": user.get("max_products", 1000),
            "max_stores": user.get("max_stores") or user.get("max_woocommerce_stores", 2)
        },
        "subscription": {
            "plan_id": user.get("subscription_plan_id"),
            "plan_name": user.get("subscription_plan_name"),
            "status": user.get("subscription_status", "none"),
            "billing_cycle": user.get("subscription_billing_cycle"),
            "updated_at": user.get("subscription_updated_at"),
            "plan_details": subscription_plan
        },
        "recent_syncs": recent_syncs,
        "payment_history": payments
    }


@router.put("/users/{user_id}/full")
async def update_user_full(user_id: str, update: UserFullUpdate, superadmin: dict = Depends(get_superadmin_user)):
    """Update all user fields (SuperAdmin only)"""
    # Sanitize user_id
    user_id = sanitize_string(user_id, max_length=50)
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Build update dict, only include non-None values and sanitize
    update_data = {}
    for field, value in update.model_dump().items():
        if value is not None:
            if isinstance(value, str):
                if field == "email":
                    update_data[field] = sanitize_email(value)
                else:
                    update_data[field] = sanitize_string(value, max_length=500)
            else:
                update_data[field] = value
    
    # Check if email is being changed and if it's unique
    if "email" in update_data and update_data["email"] != user.get("email"):
        existing = await db.users.find_one({"email": update_data["email"], "id": {"$ne": user_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Este email ya está en uso por otro usuario")
    
    # Validate role if being changed
    if "role" in update_data:
        valid_roles = ["superadmin", "admin", "user", "viewer"]
        if update_data["role"] not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Rol inválido. Roles válidos: {valid_roles}")
    
    if not update_data:
        return {"message": "No hay cambios para guardar"}
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = superadmin.get("email")
    
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    return {"success": True, "message": "Usuario actualizado correctamente"}


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



# ==================== PASSWORD RESET ENDPOINTS ====================

@router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset email.
    Always returns success to prevent email enumeration attacks.
    """
    user = await db.users.find_one({"email": request.email})
    
    if user:
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Store reset token in database
        await db.password_resets.delete_many({"user_id": user["id"]})  # Remove old tokens
        await db.password_resets.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "email": user["email"],
            "token": reset_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "used": False
        })
        
        # Send email
        try:
            config = get_config()
            app_url = getattr(config, 'app_url', '') or 'https://app.sync-stock.com'
            reset_link = f"{app_url}/#/forgot-password?token={reset_token}"
            
            email_template = get_password_reset_email_template(
                user_name=user.get("name", "Usuario"),
                reset_link=reset_link,
                app_url=app_url
            )
            
            email_service = get_email_service()
            if email_service.is_configured():
                result = email_service.send_email(
                    to_email=user["email"],
                    subject=email_template["subject"],
                    html_content=email_template["html"],
                    text_content=email_template["text"]
                )
                if result["success"]:
                    logger.info(f"Password reset email sent to {user['email']}")
                else:
                    logger.warning(f"Failed to send password reset email: {result['message']}")
            else:
                logger.warning("Email service not configured, reset token generated but email not sent")
                
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
    
    # Always return success to prevent email enumeration
    return {"message": "Si el email está registrado, recibirás un enlace de recuperación"}


@router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using token from email.
    """
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    # Find valid reset token
    reset_record = await db.password_resets.find_one({
        "token": request.token,
        "used": False
    })
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Token inválido o ya utilizado")
    
    # Check expiration
    expires_at = datetime.fromisoformat(reset_record["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="El token ha expirado. Solicita un nuevo enlace.")
    
    # Update password
    hashed_password = hash_password(request.new_password)
    result = await db.users.update_one(
        {"id": reset_record["user_id"]},
        {"$set": {
            "password": hashed_password,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Mark token as used
    await db.password_resets.update_one(
        {"token": request.token},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    logger.info(f"Password reset successful for user {reset_record['email']}")
    
    return {"message": "Contraseña actualizada correctamente"}


@router.get("/auth/verify-reset-token/{token}")
async def verify_reset_token(token: str):
    """
    Verify if a reset token is valid (optional endpoint for frontend validation).
    """
    reset_record = await db.password_resets.find_one({
        "token": token,
        "used": False
    })
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Token inválido")
    
    expires_at = datetime.fromisoformat(reset_record["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Token expirado")
    
    return {"valid": True, "email": reset_record["email"]}
