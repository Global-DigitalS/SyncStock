from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging

from services.database import db
from services.auth import get_current_user, get_superadmin_user, DEFAULT_LIMITS
from models.schemas import SubscriptionPlan, UserSubscription
from routes.email import send_subscription_change_email

router = APIRouter()
logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== SUBSCRIPTION PLANS (SuperAdmin) ====================

@router.get("/subscriptions/plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans(user: dict = Depends(get_current_user)):
    """Get all available subscription plans"""
    plans = await db.subscription_plans.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    # If no plans exist, create default ones
    if not plans:
        default_plans = [
            {
                "id": str(uuid.uuid4()),
                "name": "Free",
                "description": "Plan gratuito para empezar",
                "max_suppliers": 2,
                "max_catalogs": 1,
                "max_woocommerce_stores": 1,
                "price_monthly": 0,
                "price_yearly": 0,
                "trial_days": 14,  # 14 días de prueba con funciones premium
                "features": ["2 proveedores", "1 catálogo", "1 tienda WooCommerce", "Soporte por email", "14 días de prueba premium"],
                "is_active": True,
                "auto_sync_enabled": False,
                "sync_intervals": [],
                "crm_sync_enabled": False,
                "crm_sync_intervals": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Starter",
                "description": "Para pequeños negocios",
                "max_suppliers": 10,
                "max_catalogs": 5,
                "max_woocommerce_stores": 2,
                "price_monthly": 19.99,
                "price_yearly": 199.99,
                "trial_days": 0,
                "features": ["10 proveedores", "5 catálogos", "2 tiendas WooCommerce", "Sincronización cada 24h", "Soporte prioritario"],
                "is_active": True,
                "auto_sync_enabled": True,
                "sync_intervals": [24],  # Solo cada 24 horas
                "crm_sync_enabled": True,
                "crm_sync_intervals": [24],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Professional",
                "description": "Para negocios en crecimiento",
                "max_suppliers": 50,
                "max_catalogs": 20,
                "max_woocommerce_stores": 10,
                "price_monthly": 49.99,
                "price_yearly": 499.99,
                "trial_days": 0,
                "features": ["50 proveedores", "20 catálogos", "10 tiendas", "Sync cada 6-24h", "API REST", "Soporte 24/7"],
                "is_active": True,
                "auto_sync_enabled": True,
                "sync_intervals": [6, 12, 24],  # Cada 6, 12 o 24 horas
                "crm_sync_enabled": True,
                "crm_sync_intervals": [6, 12, 24],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Enterprise",
                "description": "Para grandes empresas",
                "max_suppliers": 999999,
                "max_catalogs": 999999,
                "max_woocommerce_stores": 999999,
                "price_monthly": 199.99,
                "price_yearly": 1999.99,
                "trial_days": 0,
                "features": ["Ilimitado", "Sync cada 1-24h", "Soporte dedicado", "Onboarding personalizado", "SLA garantizado"],
                "is_active": True,
                "auto_sync_enabled": True,
                "sync_intervals": [1, 6, 12, 24],  # Todos los intervalos
                "crm_sync_enabled": True,
                "crm_sync_intervals": [1, 6, 12, 24],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        for plan in default_plans:
            await db.subscription_plans.insert_one(plan)
        plans = default_plans
    
    return [SubscriptionPlan(**p) for p in plans]


@router.get("/subscriptions/plans/public")
async def get_public_subscription_plans():
    """Get available subscription plans (public endpoint for registration)"""
    plans = await db.subscription_plans.find(
        {"is_active": True}, 
        {"_id": 0}
    ).sort("price_monthly", 1).to_list(100)
    
    # Return simplified plan info for public display
    public_plans = []
    for plan in plans:
        public_plans.append({
            "id": plan["id"],
            "name": plan["name"],
            "description": plan.get("description", ""),
            "price_monthly": plan.get("price_monthly", 0),
            "price_yearly": plan.get("price_yearly", 0),
            "trial_days": plan.get("trial_days", 0),
            "features": plan.get("features", []),
            "max_suppliers": plan.get("max_suppliers", 0),
            "max_catalogs": plan.get("max_catalogs", 0),
            "max_woocommerce_stores": plan.get("max_woocommerce_stores", 0)
        })
    
    return public_plans


@router.post("/subscriptions/plans", response_model=SubscriptionPlan)
async def create_subscription_plan(plan: dict, superadmin: dict = Depends(get_superadmin_user)):
    """Create a new subscription plan (SuperAdmin only)"""
    plan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    plan_doc = {
        "id": plan_id,
        "name": plan.get("name", "New Plan"),
        "description": plan.get("description"),
        "max_suppliers": plan.get("max_suppliers", 10),
        "max_catalogs": plan.get("max_catalogs", 5),
        "max_woocommerce_stores": plan.get("max_woocommerce_stores", 2),
        "max_crm_connections": plan.get("max_crm_connections", 1),
        "max_stores": plan.get("max_stores", plan.get("max_woocommerce_stores", 2)),
        "max_products": plan.get("max_products", 1000),
        "price_monthly": plan.get("price_monthly", 0),
        "price_yearly": plan.get("price_yearly", 0),
        "trial_days": plan.get("trial_days", 0),
        "features": plan.get("features", []),
        "is_active": True,
        "auto_sync_enabled": plan.get("auto_sync_enabled", False),
        "sync_intervals": plan.get("sync_intervals", []),
        "crm_sync_enabled": plan.get("crm_sync_enabled", plan.get("auto_sync_enabled", False)),
        "crm_sync_intervals": plan.get("crm_sync_intervals", plan.get("sync_intervals", [])),
        "created_at": now
    }
    await db.subscription_plans.insert_one(plan_doc)
    return SubscriptionPlan(**plan_doc)


@router.put("/subscriptions/plans/{plan_id}", response_model=SubscriptionPlan)
async def update_subscription_plan(plan_id: str, plan: dict, superadmin: dict = Depends(get_superadmin_user)):
    """Update a subscription plan (SuperAdmin only)"""
    existing = await db.subscription_plans.find_one({"id": plan_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    update_data = {k: v for k, v in plan.items() if v is not None and k != "id"}
    if update_data:
        await db.subscription_plans.update_one({"id": plan_id}, {"$set": update_data})
    
    updated = await db.subscription_plans.find_one({"id": plan_id}, {"_id": 0})
    return SubscriptionPlan(**updated)


@router.delete("/subscriptions/plans/{plan_id}")
async def delete_subscription_plan(plan_id: str, superadmin: dict = Depends(get_superadmin_user)):
    """Deactivate a subscription plan (SuperAdmin only)"""
    result = await db.subscription_plans.update_one({"id": plan_id}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return {"message": "Plan desactivado"}


from pydantic import BaseModel, EmailStr
from typing import Optional as OptionalType


class BillingInfo(BaseModel):
    """Billing information for invoices"""
    company_name: str
    tax_id: str  # NIF/CIF
    address: str
    city: str
    postal_code: str
    country: str = "España"
    billing_email: OptionalType[EmailStr] = None


# ==================== USER SUBSCRIPTIONS ====================

@router.get("/subscriptions/my")
async def get_my_subscription(user: dict = Depends(get_current_user)):
    """Get current user's subscription"""
    subscription = await db.user_subscriptions.find_one(
        {"user_id": user["id"], "status": {"$in": ["active", "trial"]}},
        {"_id": 0}
    )
    
    # Get user's billing info
    billing_info = await db.billing_info.find_one({"user_id": user["id"]}, {"_id": 0})
    
    # Check if user is in trial period
    is_in_trial = False
    trial_days_left = 0
    trial_end = None
    
    if subscription and subscription.get("status") == "trial":
        trial_end_str = subscription.get("current_period_end")
        if trial_end_str:
            trial_end_dt = datetime.fromisoformat(trial_end_str.replace('Z', '+00:00'))
            if trial_end_dt > datetime.now(timezone.utc):
                is_in_trial = True
                trial_days_left = (trial_end_dt - datetime.now(timezone.utc)).days
                trial_end = trial_end_str
            else:
                # Trial has ended, update status
                await db.user_subscriptions.update_one(
                    {"id": subscription["id"]},
                    {"$set": {"status": "trial_ended"}}
                )
                subscription["status"] = "trial_ended"
    
    # Also check user-level trial_end (legacy support)
    user_trial_end = user.get("trial_end")
    if user_trial_end and not is_in_trial:
        try:
            trial_end_dt = datetime.fromisoformat(user_trial_end.replace('Z', '+00:00'))
            if trial_end_dt > datetime.now(timezone.utc):
                is_in_trial = True
                trial_days_left = (trial_end_dt - datetime.now(timezone.utc)).days
                trial_end = user_trial_end
        except (ValueError, AttributeError):
            pass
    
    if not subscription or subscription.get("status") in ["trial_ended", "cancelled", "expired"]:
        # Return free plan info
        return {
            "subscription": subscription,
            "plan": {
                "name": "Free",
                "max_suppliers": user.get("max_suppliers", 10),
                "max_catalogs": user.get("max_catalogs", 5),
                "max_woocommerce_stores": user.get("max_woocommerce_stores", 2),
                "max_crm_connections": user.get("max_crm_connections", 1)
            },
            "is_free": True,
            "is_in_trial": is_in_trial,
            "trial_days_left": trial_days_left,
            "trial_end": trial_end,
            "billing_info": billing_info
        }
    
    plan = await db.subscription_plans.find_one({"id": subscription["plan_id"]}, {"_id": 0})
    return {
        "subscription": subscription,
        "plan": plan,
        "is_free": False,
        "is_in_trial": is_in_trial,
        "trial_days_left": trial_days_left,
        "trial_end": trial_end,
        "billing_info": billing_info
    }


@router.post("/subscriptions/billing-info")
async def save_billing_info(billing: BillingInfo, user: dict = Depends(get_current_user)):
    """Save or update user's billing information"""
    billing_doc = {
        "user_id": user["id"],
        "company_name": billing.company_name,
        "tax_id": billing.tax_id.upper(),
        "address": billing.address,
        "city": billing.city,
        "postal_code": billing.postal_code,
        "country": billing.country,
        "billing_email": billing.billing_email or user.get("email"),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.billing_info.update_one(
        {"user_id": user["id"]},
        {"$set": billing_doc},
        upsert=True
    )
    
    return {"message": "Datos de facturación guardados", "billing_info": billing_doc}


@router.get("/subscriptions/billing-info")
async def get_billing_info(user: dict = Depends(get_current_user)):
    """Get user's billing information"""
    billing_info = await db.billing_info.find_one({"user_id": user["id"]}, {"_id": 0})
    return billing_info or {}


@router.post("/subscriptions/subscribe/{plan_id}")
async def subscribe_to_plan(plan_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Subscribe user to a plan - requires billing info for paid plans, supports trial periods"""
    plan = await db.subscription_plans.find_one({"id": plan_id, "is_active": True}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    billing_cycle = request.get("billing_cycle", "monthly")
    start_trial = request.get("start_trial", False)  # If user wants to start trial
    trial_days = plan.get("trial_days", 0)
    
    # For paid plans, require billing information unless starting a trial
    if plan.get("price_monthly", 0) > 0 and not start_trial:
        billing_info = await db.billing_info.find_one({"user_id": user["id"]})
        
        # Check if billing info was provided in the request
        if not billing_info and request.get("billing_info"):
            billing_data = request["billing_info"]
            billing_doc = {
                "user_id": user["id"],
                "company_name": billing_data.get("company_name", ""),
                "tax_id": billing_data.get("tax_id", "").upper(),
                "address": billing_data.get("address", ""),
                "city": billing_data.get("city", ""),
                "postal_code": billing_data.get("postal_code", ""),
                "country": billing_data.get("country", "España"),
                "billing_email": billing_data.get("billing_email") or user.get("email"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await db.billing_info.insert_one(billing_doc)
            billing_info = billing_doc
        
        if not billing_info:
            raise HTTPException(
                status_code=400, 
                detail="Se requieren datos de facturación para planes de pago"
            )
    
    # Get current subscription to know the old plan name
    current_subscription = await db.user_subscriptions.find_one(
        {"user_id": user["id"], "status": {"$in": ["active", "trial"]}},
        {"_id": 0}
    )
    old_plan_name = current_subscription.get("plan_name", "Free") if current_subscription else "Free"
    
    # Check if user already used trial for this plan
    existing_trial = await db.user_subscriptions.find_one({
        "user_id": user["id"],
        "plan_id": plan_id,
        "status": {"$in": ["trial", "trial_ended"]}
    })
    
    # Determine if we should start a trial
    is_trial = False
    if start_trial and trial_days > 0 and not existing_trial:
        is_trial = True
    
    # Cancel existing subscription
    await db.user_subscriptions.update_many(
        {"user_id": user["id"], "status": {"$in": ["active", "trial"]}},
        {"$set": {"status": "cancelled"}}
    )
    
    now = datetime.now(timezone.utc)
    
    if is_trial:
        # Trial period
        period_end = now + timedelta(days=trial_days)
        status = "trial"
    else:
        # Regular subscription
        period_end = now + timedelta(days=30 if billing_cycle == "monthly" else 365)
        status = "active"
    
    subscription_id = str(uuid.uuid4())
    subscription_doc = {
        "id": subscription_id,
        "user_id": user["id"],
        "plan_id": plan_id,
        "plan_name": plan["name"],
        "status": status,
        "billing_cycle": billing_cycle,
        "is_trial": is_trial,
        "trial_days": trial_days if is_trial else 0,
        "current_period_start": now.isoformat(),
        "current_period_end": period_end.isoformat(),
        "created_at": now.isoformat()
    }
    await db.user_subscriptions.insert_one(subscription_doc)
    
    # Update user limits based on plan
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "max_suppliers": plan["max_suppliers"],
            "max_catalogs": plan["max_catalogs"],
            "max_woocommerce_stores": plan.get("max_woocommerce_stores", plan.get("max_stores", 1)),
            "max_crm_connections": plan.get("max_crm_connections", 1),
            "trial_end": period_end.isoformat() if is_trial else None
        }}
    )
    
    # Remove _id added by MongoDB insert_one
    subscription_doc.pop("_id", None)
    
    # Send subscription change email
    try:
        await send_subscription_change_email(
            user_email=user.get("email"),
            user_name=user.get("name", "Usuario"),
            old_plan=old_plan_name,
            new_plan=plan["name"]
        )
        logger.info(f"Subscription change email sent to {user.get('email')}")
    except Exception as e:
        logger.error(f"Failed to send subscription change email: {e}")
    
    message = f"¡Periodo de prueba de {trial_days} días activado para el plan {plan['name']}!" if is_trial else f"Suscrito al plan {plan['name']} exitosamente"
    
    return {
        "message": message,
        "subscription": subscription_doc,
        "plan": plan,
        "is_trial": is_trial
    }


@router.post("/subscriptions/cancel")
async def cancel_subscription(user: dict = Depends(get_current_user)):
    """Cancel current subscription"""
    result = await db.user_subscriptions.update_one(
        {"user_id": user["id"], "status": "active"},
        {"$set": {"status": "cancelled"}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No hay suscripción activa")
    
    # Revert to free plan limits
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "max_suppliers": 2,
            "max_catalogs": 1,
            "max_woocommerce_stores": 1
        }}
    )
    
    return {"message": "Suscripción cancelada. Los límites se han revertido al plan gratuito."}


# ==================== BILLING HISTORY (Simulated) ====================

@router.get("/subscriptions/billing-history")
async def get_billing_history(user: dict = Depends(get_current_user)):
    """Get user's billing history"""
    history = await db.billing_history.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return history


@router.get("/subscriptions/stats")
async def get_subscription_stats(superadmin: dict = Depends(get_superadmin_user)):
    """Get subscription statistics (SuperAdmin only)"""
    total_subscriptions = await db.user_subscriptions.count_documents({"status": "active"})
    
    # Count by plan
    pipeline = [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$plan_name", "count": {"$sum": 1}}}
    ]
    by_plan = await db.user_subscriptions.aggregate(pipeline).to_list(100)
    
    # Monthly revenue estimate
    revenue_pipeline = [
        {"$match": {"status": "active"}},
        {"$lookup": {
            "from": "subscription_plans",
            "localField": "plan_id",
            "foreignField": "id",
            "as": "plan"
        }},
        {"$unwind": {"path": "$plan", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": None,
            "monthly_revenue": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$billing_cycle", "monthly"]},
                        "$plan.price_monthly",
                        {"$divide": ["$plan.price_yearly", 12]}
                    ]
                }
            }
        }}
    ]
    revenue_result = await db.user_subscriptions.aggregate(revenue_pipeline).to_list(1)
    monthly_revenue = revenue_result[0]["monthly_revenue"] if revenue_result else 0
    
    return {
        "total_active": total_subscriptions,
        "by_plan": {p["_id"]: p["count"] for p in by_plan},
        "estimated_monthly_revenue": round(monthly_revenue, 2)
    }
