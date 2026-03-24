"""
Competitor Monitoring Routes
CRUD de competidores, consulta de snapshots de precios y gestión de alertas.
Fase 0 del sistema de monitorización de precios de la competencia.
"""
import re
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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


# ==================== COMPETITORS CRUD ====================
# NOTA: las rutas con path parameter ({competitor_id}) van AL FINAL
# para que no capturen "prices", "alerts" como IDs.

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

    # Enriquecer con conteo de snapshots
    for comp in competitors:
        comp["total_snapshots"] = await db.price_snapshots.count_documents(
            {"competitor_id": comp["id"], "user_id": user["id"]}
        )

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

    # Eliminar snapshots asociados
    deleted_snapshots = await db.price_snapshots.delete_many(
        {"competitor_id": competitor_id, "user_id": user["id"]}
    )

    # Eliminar el competidor
    await db.competitors.delete_one({"id": competitor_id, "user_id": user["id"]})

    return {
        "message": "Competidor eliminado correctamente",
        "deleted_snapshots": deleted_snapshots.deleted_count,
    }
