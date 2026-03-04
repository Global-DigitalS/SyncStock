"""
Rutas para configuración y procesamiento de pagos con Stripe.
Incluye configuración de API keys, webhooks y procesamiento de suscripciones.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import os
import logging

from services.auth import get_superadmin_user, get_current_user
from services.database import db

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class StripeConfig(BaseModel):
    stripe_public_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    is_live_mode: bool = False
    enabled: bool = False


class StripeConfigUpdate(BaseModel):
    stripe_public_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    is_live_mode: Optional[bool] = None
    enabled: Optional[bool] = None


class CheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


# ==================== ADMIN CONFIG ENDPOINTS ====================

@router.get("/admin/stripe/config")
async def get_stripe_config(user: dict = Depends(get_superadmin_user)):
    """Get Stripe configuration (SuperAdmin only)"""
    config = await db.app_config.find_one({"type": "stripe"})
    if not config:
        return StripeConfig().model_dump()
    
    # Mask the secret key for security
    config_data = {
        "stripe_public_key": config.get("stripe_public_key", ""),
        "stripe_secret_key": config.get("stripe_secret_key", ""),
        "stripe_webhook_secret": config.get("stripe_webhook_secret", ""),
        "is_live_mode": config.get("is_live_mode", False),
        "enabled": config.get("enabled", False)
    }
    return config_data


@router.put("/admin/stripe/config")
async def update_stripe_config(config: StripeConfigUpdate, user: dict = Depends(get_superadmin_user)):
    """Update Stripe configuration (SuperAdmin only)"""
    update_data = {k: v for k, v in config.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user.get("email")
    
    await db.app_config.update_one(
        {"type": "stripe"},
        {"$set": {**update_data, "type": "stripe"}},
        upsert=True
    )
    
    logger.info(f"Stripe config updated by {user.get('email')}")
    return {"success": True, "message": "Configuración de Stripe actualizada"}


@router.post("/admin/stripe/test-connection")
async def test_stripe_connection(user: dict = Depends(get_superadmin_user)):
    """Test Stripe API connection"""
    config = await db.app_config.find_one({"type": "stripe"})
    if not config or not config.get("stripe_secret_key"):
        raise HTTPException(status_code=400, detail="No hay clave secreta configurada")
    
    try:
        import stripe
        stripe.api_key = config.get("stripe_secret_key")
        
        # Test connection by retrieving account info
        account = stripe.Account.retrieve()
        
        return {
            "success": True,
            "message": "Conexión exitosa con Stripe",
            "account_name": account.get("business_profile", {}).get("name") or account.get("email"),
            "account_id": account.get("id")
        }
    except Exception as e:
        logger.error(f"Stripe connection test failed: {e}")
        return {
            "success": False,
            "message": str(e)
        }


# ==================== SUBSCRIPTION CHECKOUT ENDPOINTS ====================

async def get_stripe_client():
    """Get configured Stripe client"""
    config = await db.app_config.find_one({"type": "stripe"})
    if not config or not config.get("enabled"):
        raise HTTPException(status_code=503, detail="Pagos con Stripe no están habilitados")
    
    if not config.get("stripe_secret_key"):
        raise HTTPException(status_code=503, detail="Stripe no está configurado")
    
    import stripe
    stripe.api_key = config.get("stripe_secret_key")
    return stripe, config


@router.post("/stripe/create-checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    user: dict = Depends(get_current_user)
):
    """Create a Stripe checkout session for subscription"""
    stripe, config = await get_stripe_client()
    
    # Get the plan
    plan = await db.subscription_plans.find_one({"id": request.plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Check if user already has a Stripe customer ID
    stripe_customer_id = user.get("stripe_customer_id")
    
    if not stripe_customer_id:
        # Create a new Stripe customer
        customer = stripe.Customer.create(
            email=user.get("email"),
            name=user.get("name"),
            metadata={"user_id": user.get("id")}
        )
        stripe_customer_id = customer.id
        
        # Save customer ID to user
        await db.users.update_one(
            {"id": user.get("id")},
            {"$set": {"stripe_customer_id": stripe_customer_id}}
        )
    
    # Determine price (monthly by default, could be yearly)
    amount = float(plan.get("price_monthly", 0))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Este plan no tiene precio configurado")
    
    # Build success and cancel URLs
    success_url = f"{request.origin_url}/subscriptions?session_id={{CHECKOUT_SESSION_ID}}&success=true"
    cancel_url = f"{request.origin_url}/subscriptions?canceled=true"
    
    try:
        # Create checkout session with subscription mode
        checkout_session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": plan.get("name"),
                        "description": plan.get("description") or f"Suscripción a {plan.get('name')}",
                    },
                    "unit_amount": int(amount * 100),  # Stripe uses cents
                    "recurring": {"interval": "month"}
                },
                "quantity": 1
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user.get("id"),
                "plan_id": request.plan_id,
                "plan_name": plan.get("name")
            }
        )
        
        # Record the transaction
        await db.payment_transactions.insert_one({
            "session_id": checkout_session.id,
            "user_id": user.get("id"),
            "user_email": user.get("email"),
            "plan_id": request.plan_id,
            "plan_name": plan.get("name"),
            "amount": amount,
            "currency": "eur",
            "status": "pending",
            "payment_status": "initiated",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear sesión de pago: {str(e)}")


@router.get("/stripe/checkout-status/{session_id}")
async def get_checkout_status(session_id: str, user: dict = Depends(get_current_user)):
    """Get the status of a checkout session"""
    stripe, _ = await get_stripe_client()
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Update transaction in database
        update_data = {
            "status": session.status,
            "payment_status": session.payment_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # If payment is complete, update user subscription
        if session.payment_status == "paid":
            # Get transaction to find plan details
            transaction = await db.payment_transactions.find_one({"session_id": session_id})
            if transaction and transaction.get("user_id") == user.get("id"):
                # Get plan details
                plan = await db.subscription_plans.find_one({"id": transaction.get("plan_id")})
                if plan:
                    # Update user subscription
                    await db.users.update_one(
                        {"id": user.get("id")},
                        {"$set": {
                            "subscription_plan_id": plan.get("id"),
                            "subscription_plan_name": plan.get("name"),
                            "max_suppliers": plan.get("max_suppliers", 5),
                            "max_catalogs": plan.get("max_catalogs", 3),
                            "max_products": plan.get("max_products", 1000),
                            "max_stores": plan.get("max_stores", 1),
                            "subscription_status": "active",
                            "subscription_updated_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    update_data["subscription_applied"] = True
        
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        
        return {
            "status": session.status,
            "payment_status": session.payment_status,
            "amount_total": session.amount_total,
            "currency": session.currency
        }
        
    except Exception as e:
        logger.error(f"Error retrieving checkout status: {e}")
        raise HTTPException(status_code=500, detail=f"Error al verificar estado: {str(e)}")


# ==================== WEBHOOK ENDPOINT ====================

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    config = await db.app_config.find_one({"type": "stripe"})
    if not config:
        raise HTTPException(status_code=503, detail="Stripe no configurado")
    
    webhook_secret = config.get("stripe_webhook_secret")
    
    try:
        import stripe
        stripe.api_key = config.get("stripe_secret_key")
        
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # If no webhook secret, parse the payload directly (not recommended for production)
            import json
            event = json.loads(payload)
        
        event_type = event.get("type") if isinstance(event, dict) else event.type
        event_data = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        
        logger.info(f"Stripe webhook received: {event_type}")
        
        # Handle different event types
        if event_type == "checkout.session.completed":
            session_id = event_data.get("id")
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "status": "complete",
                    "payment_status": "paid",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
        elif event_type == "customer.subscription.updated":
            subscription_id = event_data.get("id")
            customer_id = event_data.get("customer")
            status = event_data.get("status")
            
            # Find user by customer ID and update subscription status
            await db.users.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {
                    "subscription_status": status,
                    "stripe_subscription_id": subscription_id,
                    "subscription_updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
        elif event_type == "customer.subscription.deleted":
            customer_id = event_data.get("customer")
            
            # Mark subscription as canceled
            await db.users.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {
                    "subscription_status": "canceled",
                    "subscription_updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
        elif event_type == "invoice.payment_failed":
            customer_id = event_data.get("customer")
            
            # Mark subscription as past_due
            await db.users.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {
                    "subscription_status": "past_due",
                    "subscription_updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== USER SUBSCRIPTION INFO ====================

@router.get("/stripe/my-subscription")
async def get_my_subscription(user: dict = Depends(get_current_user)):
    """Get current user's subscription info"""
    return {
        "plan_id": user.get("subscription_plan_id"),
        "plan_name": user.get("subscription_plan_name"),
        "status": user.get("subscription_status", "none"),
        "max_suppliers": user.get("max_suppliers", 5),
        "max_catalogs": user.get("max_catalogs", 3),
        "max_products": user.get("max_products", 1000),
        "max_stores": user.get("max_stores", 1)
    }


@router.get("/stripe/plans")
async def get_available_plans():
    """Get all available subscription plans for purchase"""
    plans = await db.subscription_plans.find(
        {"is_active": {"$ne": False}},
        {"_id": 0}
    ).sort("price_monthly", 1).to_list(100)
    return plans
