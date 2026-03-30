"""
Competitor Monitoring Routes
CRUD de competidores, consulta de snapshots de precios y gestión de alertas.
Incluye: exportación CSV/Excel, informes de posicionamiento y automatización de precios.
"""
import csv
import io
import re
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from starlette.responses import StreamingResponse
from services.database import db
from services.auth import get_current_user
from models.schemas import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorResponse,
    PriceAlertCreate,
    PriceAlertUpdate,
    PriceAlertResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Canales válidos para competidores
VALID_CHANNELS = {
    "amazon_es", "pccomponentes", "mediamarkt", "fnac",
    "el_corte_ingles", "worten", "coolmod", "ldlc",
    "alternate", "web_directa", "otro",
}

# Tipos de alerta válidos
VALID_ALERT_TYPES = {"price_drop", "price_below", "competitor_cheaper", "any_change"}

# Canales de notificación válidos
VALID_ALERT_CHANNELS = {"app", "email", "webhook"}

# Regex básica para validar URLs (sin permitir inyección)
_URL_PATTERN = re.compile(
    r"^https?://"
    r"[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*"
    r"(:\d{1,5})?"
    r"(/[^\s]*)?$"
)


def _validate_url(url: str) -> bool:
    """Valida que la URL tenga un formato seguro."""
    return bool(_URL_PATTERN.match(url)) and len(url) <= 500


# ==================== PRICE QUERIES ====================
# IMPORTANTE: estas rutas estáticas van ANTES de /competitors/{competitor_id}
# para evitar que FastAPI interprete "prices" o "alerts" como un competitor_id.

@router.get("/competitors/prices")
async def get_competitor_prices(
    sku: Optional[str] = Query(None, description="SKU del producto"),
    ean: Optional[str] = Query(None, description="EAN del producto"),
    user: dict = Depends(get_current_user),
):
    """
    Obtiene precios actuales de competidores para un producto (por SKU o EAN).
    Devuelve el último snapshot de cada competidor + posicionamiento relativo.
    """
    if not sku and not ean:
        raise HTTPException(status_code=400, detail="Debes proporcionar un SKU o EAN")

    # Buscar el producto propio para obtener nuestro precio
    product_query = {"user_id": user["id"]}
    if sku:
        product_query["sku"] = sku
    elif ean:
        product_query["ean"] = ean

    my_product = await db.products.find_one(product_query, {"_id": 0})
    my_price = my_product["price"] if my_product else None

    # Buscar el último snapshot de cada competidor para este SKU/EAN
    snapshot_query = {"user_id": user["id"]}
    if sku:
        snapshot_query["sku"] = sku
    if ean:
        snapshot_query["ean"] = ean

    # Aggregation: último snapshot por competidor
    pipeline = [
        {"$match": snapshot_query},
        {"$sort": {"scraped_at": -1}},
        {
            "$group": {
                "_id": "$competitor_id",
                "latest": {"$first": "$$ROOT"},
            }
        },
        {"$replaceRoot": {"newRoot": "$latest"}},
        {"$project": {"_id": 0}},
    ]

    snapshots = await db.price_snapshots.aggregate(pipeline).to_list(100)

    # Enriquecer con nombre de competidor
    competitor_ids = [s["competitor_id"] for s in snapshots]
    competitors = {}
    if competitor_ids:
        comp_cursor = db.competitors.find(
            {"id": {"$in": competitor_ids}, "user_id": user["id"]},
            {"_id": 0, "id": 1, "name": 1, "channel": 1},
        )
        async for comp in comp_cursor:
            competitors[comp["id"]] = comp

    for snapshot in snapshots:
        comp = competitors.get(snapshot["competitor_id"], {})
        snapshot["competitor_name"] = comp.get("name", "Desconocido")

    # Calcular posicionamiento
    competitor_prices = [s["price"] for s in snapshots if s.get("price")]
    best_competitor_price = min(competitor_prices) if competitor_prices else None

    position = None
    price_diff = None
    price_diff_pct = None
    if my_price is not None and best_competitor_price is not None:
        price_diff = round(my_price - best_competitor_price, 2)
        if best_competitor_price > 0:
            price_diff_pct = round((price_diff / best_competitor_price) * 100, 2)
        if abs(price_diff) < 0.01:
            position = "equal"
        elif price_diff < 0:
            position = "cheaper"
        else:
            position = "expensive"

    return {
        "sku": sku,
        "ean": ean,
        "product_name": my_product.get("name") if my_product else None,
        "my_price": my_price,
        "competitors": snapshots,
        "best_competitor_price": best_competitor_price,
        "position": position,
        "price_difference": price_diff,
        "price_difference_percent": price_diff_pct,
    }


@router.get("/competitors/prices/history")
async def get_competitor_price_history(
    sku: Optional[str] = Query(None, description="SKU del producto"),
    ean: Optional[str] = Query(None, description="EAN del producto"),
    competitor_id: Optional[str] = Query(None, description="Filtrar por competidor"),
    days: int = Query(30, ge=1, le=365, description="Número de días de historial"),
    user: dict = Depends(get_current_user),
):
    """
    Obtiene el historial de precios de competidores para un producto.
    Útil para gráficos de evolución de precios.
    """
    if not sku and not ean:
        raise HTTPException(status_code=400, detail="Debes proporcionar un SKU o EAN")

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    query: dict = {"user_id": user["id"], "scraped_at": {"$gte": since}}
    if sku:
        query["sku"] = sku
    if ean:
        query["ean"] = ean
    if competitor_id:
        query["competitor_id"] = competitor_id

    snapshots = await db.price_snapshots.find(
        query, {"_id": 0}
    ).sort("scraped_at", 1).to_list(5000)

    # Enriquecer con nombre de competidor
    comp_ids = list({s["competitor_id"] for s in snapshots})
    competitors = {}
    if comp_ids:
        comp_cursor = db.competitors.find(
            {"id": {"$in": comp_ids}, "user_id": user["id"]},
            {"_id": 0, "id": 1, "name": 1},
        )
        async for comp in comp_cursor:
            competitors[comp["id"]] = comp["name"]

    for snapshot in snapshots:
        snapshot["competitor_name"] = competitors.get(snapshot["competitor_id"], "Desconocido")

    return {
        "sku": sku,
        "ean": ean,
        "days": days,
        "total_snapshots": len(snapshots),
        "snapshots": snapshots,
    }


# ==================== PRICE ALERTS CRUD ====================

@router.get("/competitors/alerts", response_model=list[PriceAlertResponse])
async def list_price_alerts(
    active_only: bool = Query(False, description="Filtrar solo alertas activas"),
    user: dict = Depends(get_current_user),
):
    """Lista todas las alertas de precio del usuario"""
    query = {"user_id": user["id"]}
    if active_only:
        query["active"] = True

    alerts = await db.price_alerts.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return alerts


@router.post("/competitors/alerts", response_model=PriceAlertResponse, status_code=201)
async def create_price_alert(
    data: PriceAlertCreate,
    user: dict = Depends(get_current_user),
):
    """Crea una nueva alerta de precio"""
    if not data.sku and not data.ean:
        raise HTTPException(status_code=400, detail="Debes proporcionar un SKU o EAN")

    if data.alert_type not in VALID_ALERT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de alerta no válido. Tipos permitidos: {', '.join(sorted(VALID_ALERT_TYPES))}",
        )

    if data.channel not in VALID_ALERT_CHANNELS:
        raise HTTPException(
            status_code=400,
            detail=f"Canal no válido. Canales permitidos: {', '.join(sorted(VALID_ALERT_CHANNELS))}",
        )

    # Si el canal es webhook, validar que hay URL
    if data.channel == "webhook":
        if not data.webhook_url:
            raise HTTPException(status_code=400, detail="Se requiere webhook_url cuando el canal es webhook")
        if not _validate_url(data.webhook_url):
            raise HTTPException(status_code=400, detail="URL de webhook no válida")

    # Para alertas de tipo price_below y price_drop, el umbral es obligatorio
    if data.alert_type in ("price_below", "price_drop") and data.threshold is None:
        raise HTTPException(status_code=400, detail="El umbral es obligatorio para este tipo de alerta")

    now = datetime.now(timezone.utc).isoformat()
    alert = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "sku": data.sku,
        "ean": data.ean,
        "alert_type": data.alert_type,
        "threshold": data.threshold,
        "channel": data.channel,
        "webhook_url": data.webhook_url if data.channel == "webhook" else None,
        "active": data.active,
        "last_triggered_at": None,
        "trigger_count": 0,
        "created_at": now,
    }

    await db.price_alerts.insert_one(alert)
    alert.pop("_id", None)
    return alert


@router.put("/competitors/alerts/{alert_id}", response_model=PriceAlertResponse)
async def update_price_alert(
    alert_id: str,
    data: PriceAlertUpdate,
    user: dict = Depends(get_current_user),
):
    """Actualiza una alerta de precio existente"""
    alert = await db.price_alerts.find_one(
        {"id": alert_id, "user_id": user["id"]},
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    updates = {}
    if data.sku is not None:
        updates["sku"] = data.sku
    if data.ean is not None:
        updates["ean"] = data.ean
    if data.alert_type is not None:
        if data.alert_type not in VALID_ALERT_TYPES:
            raise HTTPException(status_code=400, detail="Tipo de alerta no válido")
        updates["alert_type"] = data.alert_type
    if data.threshold is not None:
        updates["threshold"] = data.threshold
    if data.channel is not None:
        if data.channel not in VALID_ALERT_CHANNELS:
            raise HTTPException(status_code=400, detail="Canal de notificación no válido")
        updates["channel"] = data.channel
    if data.webhook_url is not None:
        if not _validate_url(data.webhook_url):
            raise HTTPException(status_code=400, detail="URL de webhook no válida")
        updates["webhook_url"] = data.webhook_url
    if data.active is not None:
        updates["active"] = data.active

    if not updates:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

    # Validar coherencia: si canal es webhook, necesita URL
    final_channel = updates.get("channel", alert.get("channel"))
    final_webhook = updates.get("webhook_url", alert.get("webhook_url"))
    if final_channel == "webhook" and not final_webhook:
        raise HTTPException(status_code=400, detail="Se requiere webhook_url cuando el canal es webhook")

    await db.price_alerts.update_one(
        {"id": alert_id, "user_id": user["id"]},
        {"$set": updates},
    )

    updated = await db.price_alerts.find_one(
        {"id": alert_id, "user_id": user["id"]},
        {"_id": 0},
    )
    return updated


@router.delete("/competitors/alerts/{alert_id}")
async def delete_price_alert(
    alert_id: str,
    user: dict = Depends(get_current_user),
):
    """Elimina una alerta de precio"""
    result = await db.price_alerts.delete_one(
        {"id": alert_id, "user_id": user["id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")

    return {"message": "Alerta eliminada correctamente"}


# ==================== CRAWL / SCRAPING ENDPOINTS ====================

# Registro de tareas en background para evitar garbage collection
_background_crawls: set = set()


@router.post("/competitors/crawl")
async def trigger_crawl(
    competitor_id: Optional[str] = Query(None, description="ID de competidor específico"),
    user: dict = Depends(get_current_user),
):
    """
    Lanza un crawl de precios de competidores en background.
    Si se especifica competitor_id, solo se scrapea ese competidor.
    """
    import asyncio
    from services.scrapers.orchestrator import run_crawl_for_user

    # Verificar que hay competidores activos
    query = {"user_id": user["id"], "active": True}
    if competitor_id:
        query["id"] = competitor_id
    count = await db.competitors.count_documents(query)
    if count == 0:
        raise HTTPException(status_code=404, detail="No hay competidores activos para scrapear")

    # Lanzar en background
    async def _run_crawl():
        try:
            result = await run_crawl_for_user(user["id"], competitor_id)
            logger.info(f"Crawl completado para {user['id']}: {result.get('status')}")
        except Exception as e:
            logger.error(f"Error en crawl background para {user['id']}: {e}")
        finally:
            _background_crawls.discard(asyncio.current_task())

    task = asyncio.create_task(_run_crawl())
    _background_crawls.add(task)

    return {
        "message": "Crawl iniciado en background",
        "competitors": count,
    }


@router.get("/competitors/crawl/status")
async def get_crawl_status(
    user: dict = Depends(get_current_user),
):
    """Obtiene el estado del último crawl de cada competidor."""
    competitors = await db.competitors.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "name": 1, "channel": 1, "last_crawl_at": 1, "last_crawl_status": 1, "active": 1},
    ).to_list(200)

    # Batch: obtener conteos de snapshots de las últimas 24h en 1 query
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    comp_ids = [c["id"] for c in competitors]
    if comp_ids:
        pipeline = [
            {"$match": {"competitor_id": {"$in": comp_ids}, "user_id": user["id"], "scraped_at": {"$gte": yesterday}}},
            {"$group": {"_id": "$competitor_id", "count": {"$sum": 1}}}
        ]
        counts_map = {}
        async for doc in db.price_snapshots.aggregate(pipeline):
            counts_map[doc["_id"]] = doc["count"]
        for comp in competitors:
            comp["snapshots_24h"] = counts_map.get(comp["id"], 0)
    else:
        for comp in competitors:
            comp["snapshots_24h"] = 0

    return {
        "competitors": competitors,
        "crawl_running": len(_background_crawls) > 0,
    }


# ==================== PENDING MATCHES ====================

@router.get("/competitors/matches/pending")
async def list_pending_matches(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """Lista los matches de baja confianza pendientes de revisión."""
    matches = await db.pending_matches.find(
        {"user_id": user["id"], "status": "pending"},
        {"_id": 0},
    ).sort("created_at", -1).skip(skip).to_list(limit)

    total = await db.pending_matches.count_documents(
        {"user_id": user["id"], "status": "pending"}
    )

    return {"matches": matches, "total": total}


@router.put("/competitors/matches/{match_id}")
async def review_pending_match(
    match_id: str,
    action: str = Query(..., description="Acción: confirm o reject"),
    user: dict = Depends(get_current_user),
):
    """Confirma o rechaza un match pendiente de revisión."""
    if action not in ("confirm", "reject"):
        raise HTTPException(status_code=400, detail="Acción debe ser 'confirm' o 'reject'")

    match = await db.pending_matches.find_one(
        {"id": match_id, "user_id": user["id"]},
    )
    if not match:
        raise HTTPException(status_code=404, detail="Match no encontrado")

    now = datetime.now(timezone.utc).isoformat()
    new_status = "confirmed" if action == "confirm" else "rejected"

    await db.pending_matches.update_one(
        {"id": match_id, "user_id": user["id"]},
        {"$set": {"status": new_status, "reviewed_at": now}},
    )

    # Si se confirma, actualizar el snapshot con confianza elevada
    if action == "confirm" and match.get("snapshot_id"):
        await db.price_snapshots.update_one(
            {"id": match["snapshot_id"], "user_id": user["id"]},
            {"$set": {"match_confidence": 1.0, "matched_by": "manual_confirm"}},
        )

    return {"message": f"Match {new_status}", "match_id": match_id}


# ==================== EXPORT & REPORTS (Fase 4B) ====================

def _csv_safe(value) -> str:
    """Previene inyección de fórmulas en CSV (OWASP A03)."""
    if not isinstance(value, str):
        return value
    if value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + value
    return value


@router.get("/competitors/export/prices")
async def export_competitor_prices_csv(
    days: int = Query(30, ge=1, le=365, description="Días de historial"),
    competitor_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """
    Exporta los snapshots de precios de competidores en CSV.
    Incluye: producto, competidor, precio, disponibilidad, fecha.
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query = {"user_id": user["id"], "scraped_at": {"$gte": since}}
    if competitor_id:
        query["competitor_id"] = competitor_id

    snapshots = await db.price_snapshots.find(
        query, {"_id": 0}
    ).sort("scraped_at", -1).to_list(10000)

    # Enriquecer con nombres de competidor
    comp_ids = list({s["competitor_id"] for s in snapshots})
    comp_names = {}
    if comp_ids:
        async for comp in db.competitors.find(
            {"id": {"$in": comp_ids}, "user_id": user["id"]},
            {"_id": 0, "id": 1, "name": 1},
        ):
            comp_names[comp["id"]] = comp["name"]

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "SKU", "EAN", "Producto (competidor)", "Competidor",
        "Precio", "Precio original", "Moneda", "Disponibilidad",
        "Confianza match", "Método match", "Fecha scraping", "URL",
    ])

    for s in snapshots:
        writer.writerow([
            _csv_safe(s.get("sku", "")),
            _csv_safe(s.get("ean", "")),
            _csv_safe(s.get("product_name", "")),
            _csv_safe(comp_names.get(s["competitor_id"], "Desconocido")),
            s.get("price", ""),
            s.get("original_price", ""),
            s.get("currency", "EUR"),
            s.get("availability", ""),
            s.get("match_confidence", ""),
            s.get("matched_by", ""),
            s.get("scraped_at", ""),
            _csv_safe(s.get("url", "")),
        ])

    filename = f"precios_competidores_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/competitors/report/positioning")
async def get_positioning_report(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    supplier_id: Optional[str] = Query(None, description="Filtrar por proveedor"),
    user: dict = Depends(get_current_user),
):
    """
    Informe de posicionamiento competitivo.
    Compara precios propios vs mejores precios de competidores para todos los productos
    que tienen snapshots. Devuelve resumen estadístico + detalle por producto.
    """
    # Obtener últimos snapshots por SKU/EAN (uno por competidor)
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$sort": {"scraped_at": -1}},
        {
            "$group": {
                "_id": {"sku": "$sku", "ean": "$ean", "competitor_id": "$competitor_id"},
                "latest": {"$first": "$$ROOT"},
            }
        },
        {"$replaceRoot": {"newRoot": "$latest"}},
        {"$project": {"_id": 0}},
    ]
    all_snapshots = await db.price_snapshots.aggregate(pipeline).to_list(10000)

    # Agrupar snapshots por producto (SKU o EAN)
    product_snapshots = {}
    for s in all_snapshots:
        key = s.get("sku") or s.get("ean")
        if not key:
            continue
        product_snapshots.setdefault(key, []).append(s)

    # Obtener nuestros productos
    product_query = {"user_id": user["id"]}
    if category:
        product_query["category"] = category
    if supplier_id:
        product_query["supplier_id"] = supplier_id

    my_products = await db.products.find(
        product_query,
        {"_id": 0, "id": 1, "sku": 1, "ean": 1, "name": 1, "price": 1, "category": 1, "supplier_name": 1},
    ).to_list(10000)

    # Nombres de competidores
    comp_ids = list({s["competitor_id"] for snaps in product_snapshots.values() for s in snaps})
    comp_names = {}
    if comp_ids:
        async for comp in db.competitors.find(
            {"id": {"$in": comp_ids}, "user_id": user["id"]},
            {"_id": 0, "id": 1, "name": 1},
        ):
            comp_names[comp["id"]] = comp["name"]

    # Construir informe
    report_items = []
    stats = {"total": 0, "cheaper": 0, "equal": 0, "expensive": 0, "no_data": 0}

    for product in my_products:
        key = product.get("sku") or product.get("ean")
        if not key:
            stats["no_data"] += 1
            continue

        snapshots = product_snapshots.get(key, [])
        if not snapshots:
            stats["no_data"] += 1
            continue

        stats["total"] += 1
        my_price = product.get("price", 0)
        best_snap = min(snapshots, key=lambda s: s.get("price", float("inf")))
        best_price = best_snap.get("price", 0)

        if my_price <= 0 or best_price <= 0:
            position = "sin_datos"
            stats["no_data"] += 1
        elif abs(my_price - best_price) < 0.01:
            position = "equal"
            stats["equal"] += 1
        elif my_price < best_price:
            position = "cheaper"
            stats["cheaper"] += 1
        else:
            position = "expensive"
            stats["expensive"] += 1

        diff = round(my_price - best_price, 2) if my_price > 0 and best_price > 0 else None
        diff_pct = round((diff / best_price) * 100, 2) if diff is not None and best_price > 0 else None

        report_items.append({
            "product_id": product["id"],
            "product_name": product.get("name", ""),
            "sku": product.get("sku"),
            "ean": product.get("ean"),
            "category": product.get("category"),
            "supplier_name": product.get("supplier_name"),
            "my_price": my_price,
            "best_competitor_price": best_price,
            "best_competitor_name": comp_names.get(best_snap["competitor_id"], "Desconocido"),
            "position": position,
            "price_difference": diff,
            "price_difference_percent": diff_pct,
            "competitors_count": len(snapshots),
        })

    # Ordenar: los más caros primero (mayor oportunidad de ajuste)
    report_items.sort(key=lambda x: x.get("price_difference_percent") or 0, reverse=True)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": stats,
        "total_products_analyzed": len(report_items),
        "items": report_items,
    }


@router.get("/competitors/report/positioning/export")
async def export_positioning_report_csv(
    category: Optional[str] = Query(None),
    supplier_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Exporta el informe de posicionamiento en CSV."""
    report = await get_positioning_report(category, supplier_id, user)

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow([
        "SKU", "EAN", "Producto", "Categoría", "Proveedor",
        "Mi precio (€)", "Mejor precio competidor (€)", "Competidor",
        "Posición", "Diferencia (€)", "Diferencia (%)", "Nº competidores",
    ])

    for item in report["items"]:
        pos_label = {"cheaper": "Más barato", "equal": "Igual", "expensive": "Más caro"}.get(
            item["position"], item["position"]
        )
        writer.writerow([
            _csv_safe(item.get("sku", "")),
            _csv_safe(item.get("ean", "")),
            _csv_safe(item.get("product_name", "")),
            _csv_safe(item.get("category", "")),
            _csv_safe(item.get("supplier_name", "")),
            item.get("my_price", ""),
            item.get("best_competitor_price", ""),
            _csv_safe(item.get("best_competitor_name", "")),
            pos_label,
            item.get("price_difference", ""),
            item.get("price_difference_percent", ""),
            item.get("competitors_count", 0),
        ])

    filename = f"informe_posicionamiento_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ==================== SMART PRICING AUTOMATION (Fase 4C) ====================

VALID_AUTOMATION_STRATEGIES = {
    "match_cheapest",      # Igualar al competidor más barato
    "undercut_by_amount",  # Precio = mejor competidor - amount
    "undercut_by_percent", # Precio = mejor competidor * (1 - pct/100)
    "margin_above_cost",   # Precio = coste proveedor * (1 + margin/100)
    "price_cap",           # No superar un techo de precio
}


@router.get("/competitors/automation/rules")
async def list_automation_rules(
    active_only: bool = Query(False),
    user: dict = Depends(get_current_user),
):
    """Lista las reglas de automatización de precios del usuario."""
    query = {"user_id": user["id"]}
    if active_only:
        query["active"] = True

    rules = await db.price_automation_rules.find(
        query, {"_id": 0}
    ).sort("priority", -1).to_list(500)
    return {"rules": rules, "total": len(rules)}


@router.post("/competitors/automation/rules", status_code=201)
async def create_automation_rule(
    data: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    """
    Crea una regla de automatización de precios.

    Body esperado:
    {
        "name": "Igualar Amazon",
        "strategy": "match_cheapest" | "undercut_by_amount" | "undercut_by_percent" |
                    "margin_above_cost" | "price_cap",
        "value": 5.0,
        "apply_to": "all" | "category" | "supplier" | "competitor" | "product",
        "apply_to_value": "string",
        "min_price": 0.0,
        "max_price": null,
        "catalog_id": null,
        "priority": 0,
        "active": true
    }
    """
    strategy = data.get("strategy", "")
    if strategy not in VALID_AUTOMATION_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Estrategia no válida. Permitidas: {', '.join(sorted(VALID_AUTOMATION_STRATEGIES))}",
        )

    name = (data.get("name") or "").strip()
    if not name or len(name) > 200:
        raise HTTPException(status_code=400, detail="Nombre requerido (máx 200 caracteres)")

    value = data.get("value")
    if value is None or not isinstance(value, (int, float)) or value < 0:
        raise HTTPException(status_code=400, detail="El campo 'value' debe ser un número >= 0")

    apply_to = data.get("apply_to", "all")
    if apply_to not in ("all", "category", "supplier", "competitor", "product"):
        raise HTTPException(status_code=400, detail="apply_to no válido")

    min_price = data.get("min_price", 0)
    max_price = data.get("max_price")
    if min_price is not None and not isinstance(min_price, (int, float)):
        raise HTTPException(status_code=400, detail="min_price debe ser numérico")
    if max_price is not None and not isinstance(max_price, (int, float)):
        raise HTTPException(status_code=400, detail="max_price debe ser numérico")
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=400, detail="min_price no puede ser mayor que max_price")

    now = datetime.now(timezone.utc).isoformat()
    rule = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": name,
        "strategy": strategy,
        "value": float(value),
        "apply_to": apply_to,
        "apply_to_value": data.get("apply_to_value"),
        "min_price": float(min_price) if min_price is not None else 0,
        "max_price": float(max_price) if max_price is not None else None,
        "catalog_id": data.get("catalog_id"),
        "priority": int(data.get("priority", 0)),
        "active": bool(data.get("active", True)),
        "last_applied_at": None,
        "products_affected": 0,
        "created_at": now,
    }

    await db.price_automation_rules.insert_one(rule)
    rule.pop("_id", None)
    return rule


@router.put("/competitors/automation/rules/{rule_id}")
async def update_automation_rule(
    rule_id: str,
    data: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    """Actualiza una regla de automatización de precios."""
    existing = await db.price_automation_rules.find_one(
        {"id": rule_id, "user_id": user["id"]},
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Regla no encontrada")

    allowed_fields = {
        "name", "strategy", "value", "apply_to", "apply_to_value",
        "min_price", "max_price", "catalog_id", "priority", "active",
    }
    updates = {k: v for k, v in data.items() if k in allowed_fields and v is not None}

    if "strategy" in updates and updates["strategy"] not in VALID_AUTOMATION_STRATEGIES:
        raise HTTPException(status_code=400, detail="Estrategia no válida")

    if not updates:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

    await db.price_automation_rules.update_one(
        {"id": rule_id, "user_id": user["id"]},
        {"$set": updates},
    )
    updated = await db.price_automation_rules.find_one(
        {"id": rule_id, "user_id": user["id"]}, {"_id": 0}
    )
    return updated


@router.delete("/competitors/automation/rules/{rule_id}")
async def delete_automation_rule(
    rule_id: str,
    user: dict = Depends(get_current_user),
):
    """Elimina una regla de automatización de precios."""
    result = await db.price_automation_rules.delete_one(
        {"id": rule_id, "user_id": user["id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"message": "Regla eliminada correctamente"}


@router.post("/competitors/automation/simulate")
async def simulate_automation(
    rule_id: Optional[str] = Query(None, description="Simular regla específica"),
    limit: int = Query(50, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """
    Simula la aplicación de reglas de automatización SIN modificar datos.
    Devuelve qué precios cambiarían y cómo.
    """
    rule_query = {"user_id": user["id"], "active": True}
    if rule_id:
        rule_query["id"] = rule_id
    rules = await db.price_automation_rules.find(
        rule_query, {"_id": 0}
    ).sort("priority", -1).to_list(100)

    if not rules:
        return {"message": "No hay reglas activas", "changes": [], "total": 0}

    # Obtener últimos snapshots agrupados por producto
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$sort": {"scraped_at": -1}},
        {
            "$group": {
                "_id": {"sku": "$sku", "ean": "$ean"},
                "best_price": {"$min": "$price"},
                "competitor_id": {"$first": "$competitor_id"},
                "latest_at": {"$first": "$scraped_at"},
            }
        },
    ]
    competitor_data = await db.price_snapshots.aggregate(pipeline).to_list(10000)

    comp_best = {}
    for cd in competitor_data:
        key = cd["_id"].get("sku") or cd["_id"].get("ean")
        if key:
            comp_best[key] = cd

    my_products = await db.products.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "sku": 1, "ean": 1, "name": 1, "price": 1,
         "category": 1, "supplier_id": 1, "supplier_name": 1},
    ).to_list(10000)

    changes = []
    for product in my_products:
        key = product.get("sku") or product.get("ean")
        if not key or key not in comp_best:
            continue

        best = comp_best[key]["best_price"]
        current_price = product.get("price", 0)
        if current_price <= 0 or best <= 0:
            continue

        for rule in rules:
            if not _rule_applies_to(rule, product):
                continue

            new_price = _calculate_automated_price(rule, current_price, best)
            if new_price is None:
                continue

            floor = rule.get("min_price", 0) or 0
            ceiling = rule.get("max_price")
            if new_price < floor:
                new_price = floor
            if ceiling is not None and new_price > ceiling:
                new_price = ceiling

            new_price = round(new_price, 2)

            if abs(new_price - current_price) >= 0.01:
                changes.append({
                    "product_id": product["id"],
                    "product_name": product.get("name", ""),
                    "sku": product.get("sku"),
                    "ean": product.get("ean"),
                    "current_price": current_price,
                    "new_price": new_price,
                    "best_competitor_price": best,
                    "rule_id": rule["id"],
                    "rule_name": rule["name"],
                    "strategy": rule["strategy"],
                    "change_amount": round(new_price - current_price, 2),
                    "change_percent": round(((new_price - current_price) / current_price) * 100, 2),
                })
            break  # Solo primera regla coincidente

        if len(changes) >= limit:
            break

    changes.sort(key=lambda c: abs(c["change_percent"]), reverse=True)

    return {
        "total_changes": len(changes),
        "rules_evaluated": len(rules),
        "changes": changes[:limit],
    }


@router.post("/competitors/automation/apply")
async def apply_automation(
    rule_id: Optional[str] = Query(None, description="Aplicar regla específica"),
    dry_run: bool = Query(False, description="Solo simular sin aplicar"),
    user: dict = Depends(get_current_user),
):
    """
    Aplica las reglas de automatización: actualiza custom_price en catalog_items.
    Si catalog_id está en la regla, solo afecta ese catálogo.
    Si no hay catalog_id, actualiza el precio base del producto.
    """
    if dry_run:
        return await simulate_automation(rule_id, 500, user)

    rule_query = {"user_id": user["id"], "active": True}
    if rule_id:
        rule_query["id"] = rule_id
    rules = await db.price_automation_rules.find(
        rule_query, {"_id": 0}
    ).sort("priority", -1).to_list(100)

    if not rules:
        return {"message": "No hay reglas activas", "applied": 0}

    # Obtener datos de competidores
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$sort": {"scraped_at": -1}},
        {
            "$group": {
                "_id": {"sku": "$sku", "ean": "$ean"},
                "best_price": {"$min": "$price"},
            }
        },
    ]
    competitor_data = await db.price_snapshots.aggregate(pipeline).to_list(10000)
    comp_best = {}
    for cd in competitor_data:
        key = cd["_id"].get("sku") or cd["_id"].get("ean")
        if key:
            comp_best[key] = cd["best_price"]

    my_products = await db.products.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "sku": 1, "ean": 1, "name": 1, "price": 1,
         "category": 1, "supplier_id": 1},
    ).to_list(10000)

    applied = 0
    now = datetime.now(timezone.utc).isoformat()
    rule_counts = {r["id"]: 0 for r in rules}

    for product in my_products:
        key = product.get("sku") or product.get("ean")
        if not key or key not in comp_best:
            continue

        best = comp_best[key]
        current_price = product.get("price", 0)
        if current_price <= 0 or best <= 0:
            continue

        for rule in rules:
            if not _rule_applies_to(rule, product):
                continue

            new_price = _calculate_automated_price(rule, current_price, best)
            if new_price is None:
                continue

            floor = rule.get("min_price", 0) or 0
            ceiling = rule.get("max_price")
            if new_price < floor:
                new_price = floor
            if ceiling is not None and new_price > ceiling:
                new_price = ceiling

            new_price = round(new_price, 2)
            if abs(new_price - current_price) < 0.01:
                break

            catalog_id = rule.get("catalog_id")
            if catalog_id:
                await db.catalog_items.update_many(
                    {"product_id": product["id"], "catalog_id": catalog_id, "user_id": user["id"]},
                    {"$set": {"custom_price": new_price}},
                )
            else:
                await db.products.update_one(
                    {"id": product["id"], "user_id": user["id"]},
                    {"$set": {"price": new_price, "updated_at": now}},
                )

            applied += 1
            rule_counts[rule["id"]] = rule_counts.get(rule["id"], 0) + 1
            break

    # Actualizar estadísticas de las reglas
    for rule in rules:
        if rule_counts.get(rule["id"], 0) > 0:
            await db.price_automation_rules.update_one(
                {"id": rule["id"], "user_id": user["id"]},
                {"$set": {"last_applied_at": now, "products_affected": rule_counts[rule["id"]]}},
            )

    # Notificación de resultado
    if applied > 0:
        try:
            from services.sync import send_realtime_notification
            notification = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "type": "competitor_price",
                "message": f"Automatización de precios aplicada: {applied} productos actualizados",
                "read": False,
                "created_at": now,
            }
            await db.notifications.insert_one(notification)
            await send_realtime_notification(user["id"], notification)
        except Exception:
            pass

    return {
        "message": f"Automatización aplicada: {applied} productos actualizados",
        "applied": applied,
        "rules_applied": {rid: cnt for rid, cnt in rule_counts.items() if cnt > 0},
    }


# ==================== HELPER FUNCTIONS ====================

def _rule_applies_to(rule: dict, product: dict) -> bool:
    """Evalúa si una regla de automatización aplica a un producto."""
    apply_to = rule.get("apply_to", "all")
    if apply_to == "all":
        return True
    target = rule.get("apply_to_value", "")
    if apply_to == "category":
        return product.get("category", "").lower() == (target or "").lower()
    if apply_to == "supplier":
        return product.get("supplier_id") == target
    if apply_to == "product":
        return product.get("id") == target
    if apply_to == "competitor":
        return True
    return False


def _calculate_automated_price(rule: dict, current_price: float, best_competitor: float) -> Optional[float]:
    """Calcula el nuevo precio según la estrategia de la regla."""
    strategy = rule["strategy"]
    value = rule.get("value", 0)

    if strategy == "match_cheapest":
        return best_competitor
    elif strategy == "undercut_by_amount":
        return best_competitor - value
    elif strategy == "undercut_by_percent":
        return best_competitor * (1 - value / 100)
    elif strategy == "margin_above_cost":
        return current_price * (1 + value / 100)
    elif strategy == "price_cap":
        return min(current_price, value)
    return None


# ==================== COMPETITORS CRUD ====================
# NOTA: las rutas con path parameter ({competitor_id}) van AL FINAL
# para que no capturen "prices", "alerts", "crawl", "matches" como IDs.

@router.get("/competitors", response_model=list[CompetitorResponse])
async def list_competitors(
    active_only: bool = Query(False, description="Filtrar solo competidores activos"),
    user: dict = Depends(get_current_user),
):
    """Lista todos los competidores del usuario"""
    query = {"user_id": user["id"]}
    if active_only:
        query["active"] = True

    competitors = await db.competitors.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(200)

    # Batch: obtener conteos de snapshots de todos los competidores en 1 query
    comp_ids = [c["id"] for c in competitors]
    if comp_ids:
        pipeline = [
            {"$match": {"competitor_id": {"$in": comp_ids}, "user_id": user["id"]}},
            {"$group": {"_id": "$competitor_id", "count": {"$sum": 1}}}
        ]
        counts_map = {}
        async for doc in db.price_snapshots.aggregate(pipeline):
            counts_map[doc["_id"]] = doc["count"]
        for comp in competitors:
            comp["total_snapshots"] = counts_map.get(comp["id"], 0)
    else:
        for comp in competitors:
            comp["total_snapshots"] = 0

    return competitors


@router.post("/competitors", response_model=CompetitorResponse, status_code=201)
async def create_competitor(
    data: CompetitorCreate,
    user: dict = Depends(get_current_user),
):
    """Crea un nuevo competidor para monitorizar"""
    # Validar URL
    if not _validate_url(data.base_url):
        raise HTTPException(status_code=400, detail="URL no válida. Debe empezar por http:// o https://")

    # Validar canal
    if data.channel not in VALID_CHANNELS:
        raise HTTPException(
            status_code=400,
            detail=f"Canal no válido. Canales permitidos: {', '.join(sorted(VALID_CHANNELS))}",
        )

    # Validar país (ISO 3166-1 alpha-2)
    if not re.match(r"^[A-Z]{2}$", data.country.upper()):
        raise HTTPException(status_code=400, detail="Código de país no válido (ISO 3166-1 alpha-2)")

    # Comprobar duplicados por URL + usuario
    existing = await db.competitors.find_one(
        {"user_id": user["id"], "base_url": data.base_url.strip().rstrip("/")},
    )
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un competidor con esta URL")

    now = datetime.now(timezone.utc).isoformat()
    competitor = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": data.name.strip(),
        "base_url": data.base_url.strip().rstrip("/"),
        "channel": data.channel,
        "country": data.country.upper(),
        "active": data.active,
        "last_crawl_at": None,
        "last_crawl_status": None,
        "created_at": now,
    }

    await db.competitors.insert_one(competitor)
    competitor.pop("_id", None)
    competitor["total_snapshots"] = 0
    return competitor


@router.get("/competitors/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(
    competitor_id: str,
    user: dict = Depends(get_current_user),
):
    """Obtiene un competidor por ID"""
    competitor = await db.competitors.find_one(
        {"id": competitor_id, "user_id": user["id"]},
        {"_id": 0},
    )
    if not competitor:
        raise HTTPException(status_code=404, detail="Competidor no encontrado")

    competitor["total_snapshots"] = await db.price_snapshots.count_documents(
        {"competitor_id": competitor_id, "user_id": user["id"]}
    )
    return competitor


@router.put("/competitors/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: str,
    data: CompetitorUpdate,
    user: dict = Depends(get_current_user),
):
    """Actualiza un competidor existente"""
    competitor = await db.competitors.find_one(
        {"id": competitor_id, "user_id": user["id"]},
    )
    if not competitor:
        raise HTTPException(status_code=404, detail="Competidor no encontrado")

    updates = {}
    if data.name is not None:
        updates["name"] = data.name.strip()
    if data.base_url is not None:
        if not _validate_url(data.base_url):
            raise HTTPException(status_code=400, detail="URL no válida")
        updates["base_url"] = data.base_url.strip().rstrip("/")
    if data.channel is not None:
        if data.channel not in VALID_CHANNELS:
            raise HTTPException(
                status_code=400,
                detail=f"Canal no válido. Canales permitidos: {', '.join(sorted(VALID_CHANNELS))}",
            )
        updates["channel"] = data.channel
    if data.country is not None:
        if not re.match(r"^[A-Z]{2}$", data.country.upper()):
            raise HTTPException(status_code=400, detail="Código de país no válido")
        updates["country"] = data.country.upper()
    if data.active is not None:
        updates["active"] = data.active

    if not updates:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

    await db.competitors.update_one(
        {"id": competitor_id, "user_id": user["id"]},
        {"$set": updates},
    )

    updated = await db.competitors.find_one(
        {"id": competitor_id, "user_id": user["id"]},
        {"_id": 0},
    )
    updated["total_snapshots"] = await db.price_snapshots.count_documents(
        {"competitor_id": competitor_id, "user_id": user["id"]}
    )
    return updated


@router.delete("/competitors/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    user: dict = Depends(get_current_user),
):
    """Elimina un competidor y sus snapshots de precios asociados"""
    competitor = await db.competitors.find_one(
        {"id": competitor_id, "user_id": user["id"]},
    )
    if not competitor:
        raise HTTPException(status_code=404, detail="Competidor no encontrado")

    deleted_snapshots = await db.price_snapshots.delete_many(
        {"competitor_id": competitor_id, "user_id": user["id"]}
    )
    await db.competitors.delete_one({"id": competitor_id, "user_id": user["id"]})

    return {
        "message": "Competidor eliminado correctamente",
        "deleted_snapshots": deleted_snapshots.deleted_count,
    }


# ==================== DASHBOARD ENDPOINTS ====================

@router.get("/competitors/dashboard/overview")
async def get_dashboard_overview(user: dict = Depends(get_current_user)):
    """
    Resumen general del dashboard de competidores.
    Devuelve KPIs principales: productos monitorizados, alertas activas, posición promedio.
    """
    user_id = user["id"]

    competitors_count = await db.competitors.count_documents({"user_id": user_id, "active": True})
    alerts_count = await db.price_alerts.count_documents({"user_id": user_id, "active": True})

    since_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    snapshots_7d = await db.price_snapshots.count_documents({"user_id": user_id, "scraped_at": {"$gte": since_7d}})

    # SKUs únicos monitorizados
    unique_skus = await db.price_snapshots.distinct("sku", {"user_id": user_id})
    monitored_skus = len([s for s in unique_skus if s])

    # Productos donde el competidor es más barato (últimos 24h)
    since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    pipeline_cheaper = [
        {"$match": {"user_id": user_id, "scraped_at": {"$gte": since_24h}}},
        {"$sort": {"scraped_at": -1}},
        {"$group": {"_id": "$sku", "comp_price": {"$first": "$price"}, "sku": {"$first": "$sku"}}},
    ]
    cheaper_snapshots = await db.price_snapshots.aggregate(pipeline_cheaper).to_list(500)

    cheaper_count = 0
    for s in cheaper_snapshots:
        if not s.get("sku"):
            continue
        my_prod = await db.products.find_one({"user_id": user_id, "sku": s["sku"]}, {"_id": 0, "price": 1})
        if my_prod and my_prod.get("price") and s.get("comp_price") and s["comp_price"] < my_prod["price"]:
            cheaper_count += 1

    return {
        "active_competitors": competitors_count,
        "active_alerts": alerts_count,
        "snapshots_last_7d": snapshots_7d,
        "monitored_skus": monitored_skus,
        "competitors_cheaper_24h": cheaper_count,
    }


@router.get("/competitors/dashboard/table")
async def get_dashboard_price_table(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    sort_by: str = Query("gap", description="Campo de ordenación: gap, price, sku"),
    user: dict = Depends(get_current_user),
):
    """
    Tabla completa de precios por SKU con posicionamiento.
    Devuelve: SKU | Nuestro precio | Mejor competidor | Gap | Cambio 24h
    """
    user_id = user["id"]
    skip = (page - 1) * page_size

    # Obtener productos propios
    product_query: dict = {"user_id": user_id}
    if search:
        product_query["$or"] = [
            {"sku": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
        ]

    products = await db.products.find(
        product_query, {"_id": 0, "id": 1, "sku": 1, "ean": 1, "name": 1, "price": 1, "cost": 1}
    ).skip(skip).limit(page_size).to_list(page_size)

    total = await db.products.count_documents(product_query)

    if not products:
        return {"items": [], "total": total, "page": page, "page_size": page_size}

    # Para cada producto, obtener último precio de cada competidor
    since_48h = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    since_96h = (datetime.now(timezone.utc) - timedelta(hours=96)).isoformat()

    result_items = []
    for prod in products:
        sku = prod.get("sku")
        ean = prod.get("ean")
        my_price = prod.get("price")

        # Último precio por competidor
        match_q: dict = {"user_id": user_id, "scraped_at": {"$gte": since_96h}}
        if sku:
            match_q["sku"] = sku
        elif ean:
            match_q["ean"] = ean
        else:
            continue

        pipeline = [
            {"$match": match_q},
            {"$sort": {"scraped_at": -1}},
            {"$group": {
                "_id": "$competitor_id",
                "price": {"$first": "$price"},
                "scraped_at": {"$first": "$scraped_at"},
                "availability": {"$first": "$availability"},
            }},
        ]
        comp_prices = await db.price_snapshots.aggregate(pipeline).to_list(20)

        if not comp_prices:
            continue

        # Nombre de competidores
        comp_ids = [c["_id"] for c in comp_prices]
        comp_names = {}
        async for comp in db.competitors.find(
            {"id": {"$in": comp_ids}, "user_id": user_id},
            {"_id": 0, "id": 1, "name": 1, "channel": 1},
        ):
            comp_names[comp["id"]] = {"name": comp["name"], "channel": comp.get("channel")}

        competitors_data = []
        prices_list = []
        for cp in comp_prices:
            cp_info = comp_names.get(cp["_id"], {})
            price = cp.get("price")
            if price and price > 0:
                prices_list.append(price)
            competitors_data.append({
                "competitor_id": cp["_id"],
                "competitor_name": cp_info.get("name", "N/A"),
                "channel": cp_info.get("channel"),
                "price": price,
                "scraped_at": cp.get("scraped_at"),
                "availability": cp.get("availability"),
            })

        best_price = min(prices_list) if prices_list else None
        gap = round(my_price - best_price, 2) if my_price and best_price else None
        gap_pct = round((gap / best_price) * 100, 2) if gap is not None and best_price else None

        # Cambio de precio 24h
        price_change_24h = None
        old_snapshot = await db.price_snapshots.find_one(
            {**match_q, "scraped_at": {"$lt": since_48h, "$gte": since_96h}},
            {"_id": 0, "price": 1},
            sort=[("scraped_at", -1)],
        )
        if old_snapshot and best_price and old_snapshot.get("price"):
            price_change_24h = round(
                ((best_price - old_snapshot["price"]) / old_snapshot["price"]) * 100, 2
            )

        # Calcular margen actual
        margin = None
        if my_price and prod.get("cost") and prod["cost"] > 0:
            margin = round(((my_price - prod["cost"]) / my_price) * 100, 1)

        result_items.append({
            "sku": sku,
            "ean": ean,
            "name": prod.get("name"),
            "my_price": my_price,
            "best_competitor_price": best_price,
            "gap_eur": gap,
            "gap_percent": gap_pct,
            "margin_percent": margin,
            "price_change_24h_percent": price_change_24h,
            "competitors": competitors_data,
            "position": (
                "cheaper" if gap is not None and gap < -0.01 else
                "equal" if gap is not None and abs(gap) <= 0.01 else
                "expensive" if gap is not None and gap > 0.01 else
                "no_data"
            ),
        })

    # Ordenación
    if sort_by == "gap":
        result_items.sort(key=lambda x: x.get("gap_eur") or 999, reverse=True)
    elif sort_by == "price":
        result_items.sort(key=lambda x: x.get("my_price") or 0, reverse=True)

    return {
        "items": result_items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/competitors/dashboard/alerts/enriched")
async def get_enriched_alerts(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="PENDING, ACTED, IGNORED"),
    user: dict = Depends(get_current_user),
):
    """
    Obtiene alertas de precio con contexto enriquecido (tendencia, posición, recomendación).
    Devuelve las alertas más recientes con análisis contextual completo.
    """
    user_id = user["id"]

    # Buscar notificaciones de competidores recientes con contexto
    query: dict = {"user_id": user_id, "type": "competitor_price"}
    if status:
        query["status"] = status.upper()

    notifications = await db.notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return {
        "alerts": notifications,
        "total": len(notifications),
    }


@router.get("/competitors/proxy/stats")
async def get_proxy_stats(user: dict = Depends(get_current_user)):
    """Devuelve estadísticas del ProxyManager (solo para admin/superadmin)."""
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Sin permisos")

    try:
        from services.scrapers.proxy_manager import proxy_manager
        return {"proxies": proxy_manager.get_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/competitors/proxy/reset/{host}")
async def reset_proxy(host: str, user: dict = Depends(get_current_user)):
    """Resetea manualmente el estado de un proxy (solo admin)."""
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Sin permisos")

    from services.scrapers.proxy_manager import proxy_manager
    ok = proxy_manager.reset_proxy(host)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Proxy '{host}' no encontrado")
    return {"message": f"Proxy '{host}' reseteado correctamente"}
