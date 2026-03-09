from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid
import io
import csv

from services.database import db
from services.auth import get_current_user, get_superadmin_user
from services.sync import calculate_final_price
from models.schemas import (
    DashboardStats, NotificationResponse, PriceHistoryResponse, ExportRequest, SyncHistoryResponse
)

router = APIRouter()


# ==================== DASHBOARD ====================

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    uid = user["id"]
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    # Unificar conteos de productos en una sola aggregation con $facet
    products_facet = await db.products.aggregate([
        {"$match": {"user_id": uid}},
        {"$facet": {
            "total":        [{"$count": "n"}],
            "low_stock":    [{"$match": {"stock": {"$gt": 0, "$lte": 5}}}, {"$count": "n"}],
            "out_of_stock": [{"$match": {"stock": 0}}, {"$count": "n"}],
        }}
    ]).to_list(1)
    pf = products_facet[0] if products_facet else {}
    total_products    = (pf.get("total")        or [{}])[0].get("n", 0)
    low_stock_count   = (pf.get("low_stock")    or [{}])[0].get("n", 0)
    out_of_stock_count = (pf.get("out_of_stock") or [{}])[0].get("n", 0)

    # Contar el resto en paralelo con gather (IO-bound, no bloquean entre sí)
    import asyncio
    (
        total_suppliers,
        total_catalogs,
        total_catalog_items,
        unread_notifications,
        recent_price_changes,
    ) = await asyncio.gather(
        db.suppliers.count_documents({"user_id": uid}),
        db.catalogs.count_documents({"user_id": uid}),
        db.catalog_items.count_documents({"user_id": uid}),
        db.notifications.count_documents({"user_id": uid, "read": False}),
        db.price_history.count_documents({"user_id": uid, "created_at": {"$gte": week_ago}}),
    )

    wc_configs = await db.woocommerce_configs.find(
        {"user_id": uid},
        {"_id": 0, "is_connected": 1, "auto_sync_enabled": 1, "products_synced": 1}
    ).to_list(100)

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


@router.get("/dashboard/superadmin-stats")
async def get_superadmin_dashboard_stats(superadmin: dict = Depends(get_superadmin_user)):
    """Dashboard estadísticas globales para SuperAdmin"""
    import asyncio
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    # Todos los conteos en paralelo con asyncio.gather
    (
        total_users,
        total_suppliers,
        total_products,
        total_catalogs,
        total_wc_stores,
        syncs_this_week,
        sync_errors_this_week,
        wc_connected,
        wc_auto_sync,
    ) = await asyncio.gather(
        db.users.count_documents({}),
        db.suppliers.count_documents({}),
        db.products.count_documents({}),
        db.catalogs.count_documents({}),
        db.woocommerce_configs.count_documents({}),
        db.sync_history.count_documents({"created_at": {"$gte": week_ago}}),
        db.sync_history.count_documents({"created_at": {"$gte": week_ago}, "status": "error"}),
        db.woocommerce_configs.count_documents({"is_connected": True}),
        db.woocommerce_configs.count_documents({"auto_sync_enabled": True}),
    )

    # Conteo de usuarios por rol con $facet en una sola query
    roles_facet = await db.users.aggregate([
        {"$facet": {r: [{"$match": {"role": r}}, {"$count": "n"}] for r in ["superadmin", "admin", "user", "viewer"]}}
    ]).to_list(1)
    rf = roles_facet[0] if roles_facet else {}
    users_by_role = {r: (rf.get(r) or [{}])[0].get("n", 0) for r in ["superadmin", "admin", "user", "viewer"]}
    
    # Top users by resources
    pipeline = [
        {"$group": {
            "_id": "$user_id",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_users_suppliers = await db.suppliers.aggregate(pipeline).to_list(5)
    top_users_products = await db.products.aggregate(pipeline).to_list(5)
    
    # Get user names for top users
    all_user_ids = list(set([u["_id"] for u in top_users_suppliers] + [u["_id"] for u in top_users_products]))
    users_map = {}
    if all_user_ids:
        users_list = await db.users.find({"id": {"$in": all_user_ids}}, {"_id": 0, "id": 1, "name": 1, "email": 1}).to_list(100)
        users_map = {u["id"]: u for u in users_list}
    
    top_suppliers = [{"user_id": u["_id"], "name": users_map.get(u["_id"], {}).get("name", "Unknown"), "email": users_map.get(u["_id"], {}).get("email", ""), "count": u["count"]} for u in top_users_suppliers]
    top_products = [{"user_id": u["_id"], "name": users_map.get(u["_id"], {}).get("name", "Unknown"), "email": users_map.get(u["_id"], {}).get("email", ""), "count": u["count"]} for u in top_users_products]
    
    # Recent user registrations - solo campos necesarios
    recent_users = await db.users.find(
        {}, {"_id": 0, "password": 0, "max_suppliers": 0, "max_catalogs": 0, "max_woocommerce_stores": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "users": {
            "total": total_users,
            "by_role": users_by_role,
            "recent": recent_users
        },
        "resources": {
            "suppliers": total_suppliers,
            "products": total_products,
            "catalogs": total_catalogs,
            "woocommerce_stores": total_wc_stores
        },
        "sync": {
            "this_week": syncs_this_week,
            "errors_this_week": sync_errors_this_week
        },
        "woocommerce": {
            "total": total_wc_stores,
            "connected": wc_connected,
            "auto_sync": wc_auto_sync
        },
        "top_users": {
            "by_suppliers": top_suppliers,
            "by_products": top_products
        }
    }


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

    # Batch: cargar todos los catálogos referenciados en una sola query
    catalog_ids = [c["catalog_id"] for c in wc_configs if c.get("catalog_id")]
    catalogs_map = {}
    if catalog_ids:
        catalogs_list = await db.catalogs.find(
            {"id": {"$in": catalog_ids}}, {"_id": 0, "id": 1, "name": 1}
        ).to_list(len(catalog_ids))
        catalogs_map = {cat["id"]: cat["name"] for cat in catalogs_list}

    wc_syncs = []
    for c in wc_configs:
        catalog_name = catalogs_map.get(c.get("catalog_id"))
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


@router.get("/price-history/product/{product_name}")
async def get_price_history_by_product(product_name: str, days: int = 90, user: dict = Depends(get_current_user)):
    """Obtener historial de precios de un producto específico para gráficas"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query = {"user_id": user["id"], "product_name": product_name, "created_at": {"$gte": start_date}}
    history = await db.price_history.find(query, {"_id": 0, "user_id": 0}).sort("created_at", 1).to_list(500)
    
    # Build price evolution timeline
    if not history:
        return {"product_name": product_name, "timeline": [], "current_price": None, "min_price": None, "max_price": None}
    
    timeline = [{"date": h["created_at"][:10], "price": h["new_price"]} for h in history]
    prices = [h["new_price"] for h in history]
    
    return {
        "product_name": product_name,
        "timeline": timeline,
        "current_price": history[-1]["new_price"] if history else None,
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "total_changes": len(history)
    }


@router.get("/price-history/top-products")
async def get_top_price_change_products(days: int = 30, limit: int = 10, user: dict = Depends(get_current_user)):
    """Obtener productos con más cambios de precio"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    pipeline = [
        {"$match": {"user_id": user["id"], "created_at": {"$gte": start_date}}},
        {"$group": {
            "_id": "$product_name",
            "changes": {"$sum": 1},
            "last_old_price": {"$last": "$old_price"},
            "last_new_price": {"$last": "$new_price"},
            "avg_change": {"$avg": "$change_percentage"}
        }},
        {"$sort": {"changes": -1}},
        {"$limit": limit}
    ]
    results = await db.price_history.aggregate(pipeline).to_list(limit)
    return [{
        "product_name": r["_id"],
        "changes": r["changes"],
        "last_price": r["last_new_price"],
        "avg_change_percent": round(r["avg_change"], 1)
    } for r in results]


# ==================== SYNC HISTORY ====================

@router.get("/sync-history", response_model=List[SyncHistoryResponse])
async def get_sync_history(
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    days: int = 30,
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """Obtener historial de sincronizaciones"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query = {"user_id": user["id"], "created_at": {"$gte": start_date}}
    if supplier_id:
        query["supplier_id"] = supplier_id
    if status:
        query["status"] = status
    history = await db.sync_history.find(query, {"_id": 0, "user_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [SyncHistoryResponse(**h) for h in history]


@router.get("/sync-history/stats")
async def get_sync_history_stats(days: int = 30, user: dict = Depends(get_current_user)):
    """Obtener estadísticas de sincronizaciones"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query = {"user_id": user["id"], "created_at": {"$gte": start_date}}
    
    total = await db.sync_history.count_documents(query)
    success = await db.sync_history.count_documents({**query, "status": "success"})
    errors = await db.sync_history.count_documents({**query, "status": "error"})
    partial = await db.sync_history.count_documents({**query, "status": "partial"})
    
    # Get totals
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": None,
            "total_imported": {"$sum": "$imported"},
            "total_updated": {"$sum": "$updated"},
            "total_errors": {"$sum": "$errors"},
            "avg_duration": {"$avg": "$duration_seconds"}
        }}
    ]
    agg_result = await db.sync_history.aggregate(pipeline).to_list(1)
    totals = agg_result[0] if agg_result else {"total_imported": 0, "total_updated": 0, "total_errors": 0, "avg_duration": 0}
    
    # Group by day for chart
    daily_pipeline = [
        {"$match": query},
        {"$addFields": {
            "date_str": {"$substr": ["$created_at", 0, 10]}
        }},
        {"$group": {
            "_id": "$date_str",
            "count": {"$sum": 1},
            "success": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
            "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 30}
    ]
    daily_stats = await db.sync_history.aggregate(daily_pipeline).to_list(30)
    
    return {
        "total": total,
        "success": success,
        "errors": errors,
        "partial": partial,
        "total_imported": totals.get("total_imported", 0),
        "total_updated": totals.get("total_updated", 0),
        "total_errors": totals.get("total_errors", 0),
        "avg_duration": round(totals.get("avg_duration", 0) or 0, 2),
        "daily_stats": [{"date": d["_id"], "count": d["count"], "success": d["success"], "errors": d["errors"]} for d in daily_stats]
    }


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



# ==================== UNIFIED SYNC CONFIGURATION ====================

@router.get("/sync/settings")
async def get_sync_settings(user: dict = Depends(get_current_user)):
    """Get user's unified sync settings"""
    from services.unified_sync import get_user_sync_settings
    return await get_user_sync_settings(user["id"])


@router.put("/sync/settings")
async def update_sync_settings(request: dict, user: dict = Depends(get_current_user)):
    """Update user's unified sync settings"""
    from services.unified_sync import update_user_sync_settings
    return await update_user_sync_settings(user["id"], request)


@router.post("/sync/run-now")
async def run_sync_now(user: dict = Depends(get_current_user)):
    """
    Run immediate sync for the current user
    Syncs all enabled services: suppliers, stores, CRM
    """
    from services.unified_sync import run_user_sync
    
    result = await run_user_sync(user["id"])
    
    # Calculate totals
    total_synced = 0
    total_errors = 0
    for key in ["suppliers", "stores", "crm"]:
        if result.get(key):
            total_synced += result[key].get("synced", 0)
            total_errors += result[key].get("errors", 0)
    
    return {
        "status": "success" if total_errors == 0 else "partial",
        "message": f"Sincronización completada: {total_synced} elementos sincronizados, {total_errors} errores",
        "details": result
    }
