from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import io
import csv

from services.database import db
from services.auth import get_current_user
from services.sync import calculate_final_price
from models.schemas import (
    DashboardStats, NotificationResponse, PriceHistoryResponse, ExportRequest, SyncHistoryResponse
)

router = APIRouter()


# ==================== DASHBOARD ====================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    total_suppliers = await db.suppliers.count_documents({"user_id": user["id"]})
    total_products = await db.products.count_documents({"user_id": user["id"]})
    total_catalog_items = await db.catalog_items.count_documents({"user_id": user["id"]})
    total_catalogs = await db.catalogs.count_documents({"user_id": user["id"]})
    low_stock_count = await db.products.count_documents({"user_id": user["id"], "stock": {"$gt": 0, "$lte": 5}})
    out_of_stock_count = await db.products.count_documents({"user_id": user["id"], "stock": 0})
    unread_notifications = await db.notifications.count_documents({"user_id": user["id"], "read": False})
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_price_changes = await db.price_history.count_documents({"user_id": user["id"], "created_at": {"$gte": week_ago}})
    wc_configs = await db.woocommerce_configs.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    return DashboardStats(
        total_suppliers=total_suppliers, total_products=total_products,
        total_catalog_items=total_catalog_items, total_catalogs=total_catalogs,
        low_stock_count=low_stock_count, out_of_stock_count=out_of_stock_count,
        unread_notifications=unread_notifications, recent_price_changes=recent_price_changes,
        woocommerce_stores=len(wc_configs),
        woocommerce_connected=sum(1 for c in wc_configs if c.get("is_connected")),
        woocommerce_auto_sync=sum(1 for c in wc_configs if c.get("auto_sync_enabled")),
        woocommerce_total_synced=sum(c.get("products_synced", 0) for c in wc_configs),
    )


@router.get("/dashboard/stock-alerts")
async def get_stock_alerts(user: dict = Depends(get_current_user)):
    low_stock = await db.products.find({"user_id": user["id"], "stock": {"$gt": 0, "$lte": 5}}, {"_id": 0, "user_id": 0}).limit(10).to_list(10)
    out_of_stock = await db.products.find({"user_id": user["id"], "stock": 0}, {"_id": 0, "user_id": 0}).limit(10).to_list(10)
    return {"low_stock": low_stock, "out_of_stock": out_of_stock}


@router.get("/dashboard/sync-status")
async def get_dashboard_sync_status(user: dict = Depends(get_current_user)):
    suppliers = await db.suppliers.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "name": 1, "last_sync": 1, "product_count": 1, "connection_type": 1}
    ).to_list(100)
    wc_configs = await db.woocommerce_configs.find(
        {"user_id": user["id"]}, {"_id": 0, "consumer_key": 0, "consumer_secret": 0}
    ).to_list(100)
    wc_syncs = []
    for c in wc_configs:
        catalog_name = None
        if c.get("catalog_id"):
            cat = await db.catalogs.find_one({"id": c["catalog_id"]}, {"_id": 0, "name": 1})
            catalog_name = cat["name"] if cat else None
        next_sync = None
        if c.get("auto_sync_enabled"):
            if c.get("last_sync"):
                last_dt = datetime.fromisoformat(c["last_sync"].replace('Z', '+00:00'))
                next_sync = (last_dt + timedelta(hours=12)).isoformat()
            else:
                next_sync = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        wc_syncs.append({
            "id": c["id"], "name": c.get("name", "Sin nombre"),
            "store_url": c.get("store_url", ""),
            "is_connected": c.get("is_connected", False),
            "auto_sync_enabled": c.get("auto_sync_enabled", False),
            "catalog_name": catalog_name, "last_sync": c.get("last_sync"),
            "next_sync": next_sync, "products_synced": c.get("products_synced", 0),
        })
    recent_notifications = await db.notifications.find(
        {"user_id": user["id"]}, {"_id": 0, "user_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    return {"suppliers": suppliers, "woocommerce_stores": wc_syncs, "recent_notifications": recent_notifications}


# ==================== NOTIFICATIONS ====================

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(unread_only: bool = False, skip: int = 0, limit: int = 50, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if unread_only:
        query["read"] = False
    notifications = await db.notifications.find(query, {"_id": 0, "user_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [NotificationResponse(**n) for n in notifications]


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    result = await db.notifications.update_one({"id": notification_id, "user_id": user["id"]}, {"$set": {"read": True}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"message": "Notificación marcada como leída"}


@router.put("/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(get_current_user)):
    await db.notifications.update_many({"user_id": user["id"]}, {"$set": {"read": True}})
    return {"message": "Todas las notificaciones marcadas como leídas"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, user: dict = Depends(get_current_user)):
    result = await db.notifications.delete_one({"id": notification_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return {"message": "Notificación eliminada"}


@router.delete("/notifications")
async def delete_all_notifications(read_only: bool = True, user: dict = Depends(get_current_user)):
    """Eliminar notificaciones. Si read_only=True, solo elimina las leídas."""
    query = {"user_id": user["id"]}
    if read_only:
        query["read"] = True
    result = await db.notifications.delete_many(query)
    return {"message": f"{result.deleted_count} notificaciones eliminadas"}


@router.get("/notifications/stats")
async def get_notification_stats(user: dict = Depends(get_current_user)):
    """Obtener estadísticas de notificaciones por tipo"""
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$group": {
            "_id": {"type": "$type", "read": "$read"},
            "count": {"$sum": 1}
        }}
    ]
    results = await db.notifications.aggregate(pipeline).to_list(100)
    stats = {
        "total": 0, "unread": 0,
        "by_type": {
            "sync_complete": {"total": 0, "unread": 0},
            "sync_error": {"total": 0, "unread": 0},
            "stock_out": {"total": 0, "unread": 0},
            "stock_low": {"total": 0, "unread": 0},
            "price_change": {"total": 0, "unread": 0},
            "woocommerce_export": {"total": 0, "unread": 0},
        }
    }
    for r in results:
        notif_type = r["_id"]["type"]
        is_read = r["_id"]["read"]
        count = r["count"]
        stats["total"] += count
        if not is_read:
            stats["unread"] += count
        if notif_type in stats["by_type"]:
            stats["by_type"][notif_type]["total"] += count
            if not is_read:
                stats["by_type"][notif_type]["unread"] += count
    return stats


# ==================== PRICE HISTORY ====================

@router.get("/price-history", response_model=List[PriceHistoryResponse])
async def get_price_history(product_id: Optional[str] = None, days: int = 30, skip: int = 0, limit: int = 100, user: dict = Depends(get_current_user)):
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query = {"user_id": user["id"], "created_at": {"$gte": start_date}}
    if product_id:
        query["product_id"] = product_id
    history = await db.price_history.find(query, {"_id": 0, "user_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [PriceHistoryResponse(**h) for h in history]


# ==================== CSV EXPORT ====================

@router.post("/export")
async def export_catalog(request: ExportRequest, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"], "active": True}
    if request.catalog_ids:
        query["id"] = {"$in": request.catalog_ids}
    catalog_items = await db.catalog.find(query, {"_id": 0}).to_list(10000)
    margin_rules = await db.margin_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("priority", -1).to_list(100)
    rows = []
    for item in catalog_items:
        product = await db.products.find_one({"id": item["product_id"]}, {"_id": 0, "user_id": 0})
        if not product:
            continue
        base_price = item.get("custom_price") or product.get("price", 0)
        final_price = calculate_final_price(base_price, product, margin_rules)
        name = item.get("custom_name") or product.get("name", "")
        if request.platform == "prestashop":
            rows.append({
                "ID": product.get("id"), "Active (0/1)": "1", "Name*": name,
                "Categories (x,y,z...)": product.get("category", ""),
                "Price tax excl.": round(final_price, 2), "Tax rules ID": "1",
                "Wholesale price": product.get("price", 0),
                "Reference #": product.get("sku", ""), "EAN13": product.get("ean", ""),
                "Weight": product.get("weight", ""), "Quantity": product.get("stock", 0),
                "Description": product.get("description", ""),
                "Image URLs (x,y,z...)": product.get("image_url", ""),
            })
        elif request.platform == "woocommerce":
            rows.append({
                "Type": "simple", "SKU": product.get("sku", ""), "Name": name,
                "Published": "1", "Regular price": round(final_price, 2),
                "Stock": product.get("stock", 0), "Categories": product.get("category", ""),
                "Images": product.get("image_url", ""), "Brands": product.get("brand", ""),
                "Weight (kg)": product.get("weight", ""),
            })
        elif request.platform == "shopify":
            rows.append({
                "Handle": product.get("sku", "").lower().replace(" ", "-"),
                "Title": name, "Vendor": product.get("brand", ""),
                "Type": product.get("category", ""), "Published": "TRUE",
                "Variant SKU": product.get("sku", ""),
                "Variant Inventory Qty": product.get("stock", 0),
                "Variant Price": round(final_price, 2),
                "Variant Barcode": product.get("ean", ""),
                "Image Src": product.get("image_url", ""),
            })
    if not rows:
        raise HTTPException(status_code=400, detail="No hay productos para exportar")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    filename = f"catalog_{request.platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
