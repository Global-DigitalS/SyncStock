"""
Rutas de planes de suscripción para SuperAdmin.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from services.auth import get_superadmin_user
from services.database import db

sub_router = APIRouter()


# ==================== SUBSCRIPTION PLAN MODELS ====================

class SubscriptionPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    max_suppliers: int = 5
    max_catalogs: int = 3
    max_products: int = 1000
    max_stores: int = 1
    max_crm_connections: int = 1
    price_monthly: float = 0
    price_yearly: float = 0
    trial_days: int = 0
    features: List[str] = []
    is_default: bool = False
    sort_order: int = 0
    # Unified Auto-Sync options (for Suppliers, Stores, CRM)
    auto_sync_enabled: bool = False
    sync_intervals: List[int] = []
    # Legacy CRM-only Auto-Sync options (for backwards compatibility)
    crm_sync_enabled: bool = False
    crm_sync_intervals: List[int] = []

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_suppliers: Optional[int] = None
    max_catalogs: Optional[int] = None
    max_products: Optional[int] = None
    max_stores: Optional[int] = None
    max_crm_connections: Optional[int] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    trial_days: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    sort_order: Optional[int] = None
    # Unified Auto-Sync options (for Suppliers, Stores, CRM)
    auto_sync_enabled: Optional[bool] = None
    sync_intervals: Optional[List[int]] = None
    # Legacy CRM-only Auto-Sync options (for backwards compatibility)
    crm_sync_enabled: Optional[bool] = None
    crm_sync_intervals: Optional[List[int]] = None


# ==================== SUBSCRIPTION PLANS ENDPOINTS ====================

@sub_router.get("/admin/plans")
async def get_plans(user: dict = Depends(get_superadmin_user)):
    """Get all subscription plans"""
    plans = await db.subscription_plans.find({}, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return plans


@sub_router.post("/admin/plans")
async def create_plan(data: SubscriptionPlanCreate, user: dict = Depends(get_superadmin_user)):
    """Create a new subscription plan"""
    plan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # If this is the default plan, unset others
    if data.is_default:
        await db.subscription_plans.update_many({}, {"$set": {"is_default": False}})

    plan = {
        "id": plan_id,
        **data.model_dump(),
        "is_active": True,
        "created_at": now,
        "created_by": user["id"]
    }

    await db.subscription_plans.insert_one(plan)
    plan.pop("_id", None)

    return {"success": True, "plan": plan}


@sub_router.put("/admin/plans/{plan_id}")
async def update_plan(plan_id: str, data: SubscriptionPlanUpdate, user: dict = Depends(get_superadmin_user)):
    """Update a subscription plan"""
    existing = await db.subscription_plans.find_one({"id": plan_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # If setting as default, unset others
    if data.is_default:
        await db.subscription_plans.update_many(
            {"id": {"$ne": plan_id}},
            {"$set": {"is_default": False}}
        )

    await db.subscription_plans.update_one({"id": plan_id}, {"$set": update_data})

    plan = await db.subscription_plans.find_one({"id": plan_id}, {"_id": 0})
    return {"success": True, "plan": plan}


@sub_router.delete("/admin/plans/{plan_id}")
async def delete_plan(plan_id: str, user: dict = Depends(get_superadmin_user)):
    """Delete a subscription plan"""
    existing = await db.subscription_plans.find_one({"id": plan_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    # Check if any users are on this plan
    users_on_plan = await db.users.count_documents({"plan_id": plan_id})
    if users_on_plan > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar: {users_on_plan} usuario(s) tienen este plan asignado"
        )

    await db.subscription_plans.delete_one({"id": plan_id})
    return {"success": True, "message": "Plan eliminado"}
