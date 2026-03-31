"""
Order management routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone

from services.auth import get_current_user
from services.database import db

router = APIRouter()


@router.get("/orders")
async def get_orders(
    user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """Get user's orders with optional filtering"""
    query = {"userId": user["id"]}

    if status:
        query["status"] = status

    if source:
        query["source"] = source

    orders = await db.orders.find(
        query,
        {"_id": 0}
    ).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)

    total = await db.orders.count_documents(query)

    return {
        "orders": orders,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/orders/{order_id}")
async def get_order(order_id: str, user: dict = Depends(get_current_user)):
    """Get order details"""
    order = await db.orders.find_one({
        "id": order_id,
        "userId": user["id"]
    }, {"_id": 0})

    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    return order


@router.get("/orders/status/failed")
async def get_failed_orders(
    user: dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0)
):
    """Get orders with errors"""
    query = {
        "userId": user["id"],
        "status": "error"
    }

    orders = await db.orders.find(
        query,
        {"_id": 0}
    ).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)

    total = await db.orders.count_documents(query)

    return {
        "failed_orders": orders,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/orders/status/summary")
async def get_orders_summary(user: dict = Depends(get_current_user)):
    """Get orders summary by status"""
    pipeline = [
        {"$match": {"userId": user["id"]}},
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "totalAmount": {"$sum": "$totalAmount"}
            }
        }
    ]

    summary = await db.orders.aggregate(pipeline).to_list(100)

    return {
        "by_status": {item["_id"]: {
            "count": item["count"],
            "totalAmount": item["totalAmount"]
        } for item in summary},
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/orders/{order_id}/retry")
async def retry_order(order_id: str, user: dict = Depends(get_current_user)):
    """Retry processing a failed order"""
    order = await db.orders.find_one({
        "id": order_id,
        "userId": user["id"],
        "status": "error"
    })

    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado o no está en error")

    # Re-process the order
    from services.orders import process_order_webhook

    # Get original webhook data from order
    webhook_data = order.get("originalData", {})

    if not webhook_data:
        raise HTTPException(status_code=400, detail="No se puede reintentaré sin datos originales")

    result = await process_order_webhook(
        webhook_data,
        order.get("source"),
        user["id"],
        order.get("storeId")
    )

    if result["status"] == "success":
        return {
            "status": "success",
            "message": "Pedido reintentado exitosamente",
            "order_id": result.get("order_id")
        }
    else:
        return {
            "status": "error",
            "message": result.get("message"),
            "order_id": order_id
        }


@router.get("/orders/stats/by-source")
async def get_orders_by_source(user: dict = Depends(get_current_user)):
    """Get order statistics by source platform"""
    pipeline = [
        {"$match": {"userId": user["id"]}},
        {
            "$group": {
                "_id": "$source",
                "count": {"$sum": 1},
                "completed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                },
                "errors": {
                    "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
                },
                "totalAmount": {"$sum": "$totalAmount"}
            }
        },
        {"$sort": {"count": -1}}
    ]

    stats = await db.orders.aggregate(pipeline).to_list(100)

    return {
        "by_source": {item["_id"]: {
            "count": item["count"],
            "completed": item["completed"],
            "errors": item["errors"],
            "totalAmount": item["totalAmount"],
            "success_rate": (item["completed"] / item["count"] * 100) if item["count"] > 0 else 0
        } for item in stats}
    }
