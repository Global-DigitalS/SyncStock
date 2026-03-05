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

# Import emergentintegrations for Stripe checkout
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

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
    billing_cycle: str = "monthly"  # monthly or yearly


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


# ==================== HELPER FUNCTIONS ====================

async def fetch_stripe_config():
    """Get Stripe configuration from database"""
    config = await db.app_config.find_one({"type": "stripe"})
    if not config:
        return None
    return config


async def get_stripe_checkout(request: Request = None, webhook_url: str = None):
    """Get configured StripeCheckout instance using emergentintegrations"""
    config = await fetch_stripe_config()
    if not config or not config.get("enabled"):
        raise HTTPException(status_code=503, detail="Pagos con Stripe no están habilitados")
    
    if not config.get("stripe_secret_key"):
        raise HTTPException(status_code=503, detail="Stripe no está configurado correctamente")
    
    api_key = config.get("stripe_secret_key")
    
    # Create StripeCheckout instance
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    return stripe_checkout, config


# ==================== PUBLIC ENDPOINTS ====================

@router.get("/stripe/config/status")
async def get_stripe_status():
    """Check if Stripe payments are enabled (public endpoint)"""
    config = await fetch_stripe_config()
    if not config:
        return {"enabled": False, "configured": False}
    
    return {
        "enabled": config.get("enabled", False),
        "configured": bool(config.get("stripe_secret_key")),
        "is_live_mode": config.get("is_live_mode", False)
    }


# ==================== SUBSCRIPTION CHECKOUT ENDPOINTS ====================

@router.post("/stripe/create-checkout")
async def create_checkout_session(
    checkout_request: CheckoutRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Create a Stripe checkout session for subscription using emergentintegrations"""
    
    # Build webhook URL
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/stripe/webhook"
    
    stripe_checkout, config = await get_stripe_checkout(request, webhook_url)
    
    # Get the plan from database (server-side - never trust frontend amounts)
    plan = await db.subscription_plans.find_one({"id": checkout_request.plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Determine price based on billing cycle (server-side calculation)
    if checkout_request.billing_cycle == "yearly":
        amount = float(plan.get("price_yearly", 0))
    else:
        amount = float(plan.get("price_monthly", 0))
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Este plan no tiene precio configurado")
    
    # Build success and cancel URLs from frontend origin (dynamic)
    origin = checkout_request.origin_url.rstrip("/")
    # Use hash router format for proper navigation
    success_url = f"{origin}/#/subscriptions?session_id={{CHECKOUT_SESSION_ID}}&success=true"
    cancel_url = f"{origin}/#/subscriptions?canceled=true"
    
    try:
        # Create checkout session using emergentintegrations
        checkout_req = CheckoutSessionRequest(
            amount=amount,  # Keep as float
            currency="eur",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user.get("id"),
                "user_email": user.get("email"),
                "plan_id": checkout_request.plan_id,
                "plan_name": plan.get("name"),
                "billing_cycle": checkout_request.billing_cycle
            }
        )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_req)
        
        # MANDATORY: Record the transaction BEFORE redirect
        await db.payment_transactions.insert_one({
            "session_id": session.session_id,
            "user_id": user.get("id"),
            "user_email": user.get("email"),
            "plan_id": checkout_request.plan_id,
            "plan_name": plan.get("name"),
            "billing_cycle": checkout_request.billing_cycle,
            "amount": amount,
            "currency": "eur",
            "status": "pending",
            "payment_status": "initiated",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Checkout session created for user {user.get('email')}, plan {plan.get('name')}, session {session.session_id}")
        
        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear sesión de pago: {str(e)}")


@router.get("/stripe/checkout-status/{session_id}")
async def get_checkout_status(session_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Get the status of a checkout session and update user subscription if paid"""
    
    # Build webhook URL (needed for StripeCheckout init)
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/stripe/webhook"
    
    stripe_checkout, _ = await get_stripe_checkout(request, webhook_url)
    
    try:
        # Get checkout status using emergentintegrations
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Get transaction from database
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        
        # Update transaction status
        update_data = {
            "status": status.status,
            "payment_status": status.payment_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # If payment is complete and hasn't been processed yet, update user subscription
        if status.payment_status == "paid":
            if transaction and not transaction.get("subscription_applied"):
                # Verify transaction belongs to requesting user
                if transaction.get("user_id") == user.get("id"):
                    # Get plan details
                    plan = await db.subscription_plans.find_one({"id": transaction.get("plan_id")})
                    if plan:
                        # Update user subscription limits
                        await db.users.update_one(
                            {"id": user.get("id")},
                            {"$set": {
                                "subscription_plan_id": plan.get("id"),
                                "subscription_plan_name": plan.get("name"),
                                "max_suppliers": plan.get("max_suppliers", 5),
                                "max_catalogs": plan.get("max_catalogs", 3),
                                "max_products": plan.get("max_products", 1000),
                                "max_stores": plan.get("max_stores") or plan.get("max_woocommerce_stores", 1),
                                "subscription_status": "active",
                                "subscription_billing_cycle": transaction.get("billing_cycle", "monthly"),
                                "subscription_updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        
                        # Mark as applied to prevent duplicate processing
                        update_data["subscription_applied"] = True
                        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
                        
                        logger.info(f"Subscription activated for user {user.get('email')}, plan {plan.get('name')}")
        
        # Update transaction record
        if transaction:
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "subscription_applied": update_data.get("subscription_applied", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving checkout status: {e}")
        raise HTTPException(status_code=500, detail=f"Error al verificar estado: {str(e)}")


# ==================== WEBHOOK ENDPOINT ====================

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks using emergentintegrations"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    config = await fetch_stripe_config()
    if not config:
        raise HTTPException(status_code=503, detail="Stripe no configurado")
    
    try:
        # Build webhook URL for StripeCheckout init
        host_url = str(request.base_url).rstrip("/")
        webhook_url = f"{host_url}/api/stripe/webhook"
        
        stripe_checkout = StripeCheckout(
            api_key=config.get("stripe_secret_key"),
            webhook_url=webhook_url
        )
        
        # Handle webhook using emergentintegrations
        webhook_response = await stripe_checkout.handle_webhook(payload, sig_header)
        
        event_type = webhook_response.event_type
        session_id = webhook_response.session_id
        payment_status = webhook_response.payment_status
        
        logger.info(f"Stripe webhook received: {event_type}, session: {session_id}, status: {payment_status}")
        
        # Update transaction based on event
        if session_id:
            update_data = {
                "webhook_event": event_type,
                "payment_status": payment_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # If payment completed, mark as complete
            if payment_status == "paid":
                update_data["status"] = "complete"
                update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                # Get transaction and apply subscription if not already done
                transaction = await db.payment_transactions.find_one({"session_id": session_id})
                if transaction and not transaction.get("subscription_applied"):
                    plan = await db.subscription_plans.find_one({"id": transaction.get("plan_id")})
                    if plan:
                        await db.users.update_one(
                            {"id": transaction.get("user_id")},
                            {"$set": {
                                "subscription_plan_id": plan.get("id"),
                                "subscription_plan_name": plan.get("name"),
                                "max_suppliers": plan.get("max_suppliers", 5),
                                "max_catalogs": plan.get("max_catalogs", 3),
                                "max_products": plan.get("max_products", 1000),
                                "max_stores": plan.get("max_stores") or plan.get("max_woocommerce_stores", 1),
                                "subscription_status": "active",
                                "subscription_billing_cycle": transaction.get("billing_cycle", "monthly"),
                                "subscription_updated_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        update_data["subscription_applied"] = True
                        logger.info(f"Subscription applied via webhook for user {transaction.get('user_email')}")
            
            elif payment_status == "expired":
                update_data["status"] = "expired"
            
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
        
        return {"status": "success", "event_type": event_type}
        
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
