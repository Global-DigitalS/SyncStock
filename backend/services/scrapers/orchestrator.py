"""
Orquestador de scraping de precios de competidores.
Coordina: selección de productos → scraping → matching → almacenamiento → alertas.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict

from services.database import db
from services.scrapers import get_scraper
from services.scrapers.base import ScrapedProduct
from services.scrapers.matcher import match_product, AUTO_ACCEPT_THRESHOLD, MatchResult

logger = logging.getLogger(__name__)

# Máximo de productos a scrapear por ejecución (para no sobrecargar)
MAX_PRODUCTS_PER_RUN = 200

# Máximo de competidores simultáneos
MAX_CONCURRENT_COMPETITORS = 3


async def _get_user_products(user_id: str, limit: int = MAX_PRODUCTS_PER_RUN) -> List[dict]:
    """Obtiene los productos del usuario para matching."""
    products = await db.products.find(
        {"user_id": user_id, "is_selected": True},
        {"_id": 0, "id": 1, "sku": 1, "ean": 1, "name": 1, "price": 1},
    ).to_list(limit)

    # Si no hay productos seleccionados, usar todos
    if not products:
        products = await db.products.find(
            {"user_id": user_id},
            {"_id": 0, "id": 1, "sku": 1, "ean": 1, "name": 1, "price": 1},
        ).to_list(limit)

    return products


async def _store_snapshot(
    user_id: str,
    competitor_id: str,
    scraped: ScrapedProduct,
    match: MatchResult,
) -> str:
    """Almacena un snapshot de precio en la BD."""
    now = datetime.now(timezone.utc).isoformat()
    snapshot_id = str(uuid.uuid4())

    snapshot = {
        "id": snapshot_id,
        "user_id": user_id,
        "competitor_id": competitor_id,
        "sku": match.product_sku or scraped.sku,
        "ean": match.product_ean or scraped.ean,
        "product_name": scraped.product_name,
        "price": scraped.price,
        "original_price": scraped.original_price,
        "currency": scraped.currency,
        "url": scraped.url,
        "seller": scraped.seller,
        "availability": scraped.availability,
        "match_confidence": match.confidence,
        "matched_by": match.matched_by,
        "scraped_at": now,
    }

    await db.price_snapshots.insert_one(snapshot)
    return snapshot_id


async def _store_pending_match(
    user_id: str,
    competitor_id: str,
    scraped: ScrapedProduct,
    match: MatchResult,
    snapshot_id: str,
) -> None:
    """Almacena un match de baja confianza para revisión manual."""
    now = datetime.now(timezone.utc).isoformat()
    pending = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "sku": match.product_sku,
        "ean": match.product_ean,
        "product_name": match.product_name,
        "competitor_id": competitor_id,
        "snapshot_id": snapshot_id,
        "candidate_name": scraped.product_name,
        "candidate_url": scraped.url,
        "match_score": match.confidence,
        "status": "pending",
        "reviewed_at": None,
        "created_at": now,
    }
    await db.pending_matches.insert_one(pending)


async def _evaluate_alerts(
    user_id: str,
    sku: Optional[str],
    ean: Optional[str],
    competitor_price: float,
    competitor_name: str,
) -> None:
    """Evalúa las alertas de precio del usuario para este producto."""
    query = {"user_id": user_id, "active": True}
    # Buscar alertas que coincidan por SKU o EAN
    or_conditions = []
    if sku:
        or_conditions.append({"sku": sku})
    if ean:
        or_conditions.append({"ean": ean})
    if not or_conditions:
        return

    query["$or"] = or_conditions

    alerts = await db.price_alerts.find(query, {"_id": 0}).to_list(50)

    for alert in alerts:
        triggered = False
        message = ""

        if alert["alert_type"] == "any_change":
            # Siempre se dispara con nuevo snapshot
            triggered = True
            message = f"Nuevo precio detectado en {competitor_name}: {competitor_price}€"

        elif alert["alert_type"] == "price_below":
            threshold = alert.get("threshold", 0)
            if competitor_price <= threshold:
                triggered = True
                message = f"Precio en {competitor_name} ({competitor_price}€) por debajo de {threshold}€"

        elif alert["alert_type"] == "competitor_cheaper":
            # Comparar con nuestro precio
            product_query = {"user_id": user_id}
            if sku:
                product_query["sku"] = sku
            elif ean:
                product_query["ean"] = ean

            my_product = await db.products.find_one(product_query, {"_id": 0, "price": 1})
            if my_product and competitor_price < my_product["price"]:
                diff = round(my_product["price"] - competitor_price, 2)
                triggered = True
                message = (
                    f"{competitor_name} tiene mejor precio ({competitor_price}€) "
                    f"que el tuyo ({my_product['price']}€). Diferencia: {diff}€"
                )

        elif alert["alert_type"] == "price_drop":
            threshold_pct = alert.get("threshold", 0)
            # Obtener el snapshot anterior más reciente
            prev_snapshot = await db.price_snapshots.find_one(
                {
                    "user_id": user_id,
                    "sku": sku,
                    "scraped_at": {"$lt": datetime.now(timezone.utc).isoformat()},
                },
                {"_id": 0, "price": 1},
                sort=[("scraped_at", -1)],
            )
            if prev_snapshot and prev_snapshot["price"] > 0:
                drop_pct = ((prev_snapshot["price"] - competitor_price) / prev_snapshot["price"]) * 100
                if drop_pct >= threshold_pct:
                    triggered = True
                    message = (
                        f"Bajada de precio en {competitor_name}: "
                        f"{prev_snapshot['price']}€ → {competitor_price}€ "
                        f"(-{drop_pct:.1f}%)"
                    )

        if triggered:
            now = datetime.now(timezone.utc).isoformat()
            # Actualizar alerta
            await db.price_alerts.update_one(
                {"id": alert["id"]},
                {
                    "$set": {"last_triggered_at": now},
                    "$inc": {"trigger_count": 1},
                },
            )

            # Crear notificación en la app
            if alert.get("channel") in ("app", "email"):
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "competitor_price",
                    "message": message,
                    "read": False,
                    "created_at": now,
                }
                await db.notifications.insert_one(notification)

            logger.info(f"Alerta disparada [{alert['alert_type']}]: {message}")


async def crawl_competitor(
    user_id: str,
    competitor: dict,
    user_products: List[dict],
) -> dict:
    """
    Ejecuta el scraping de un competidor para todos los productos del usuario.

    Returns:
        dict con estadísticas: {found, matched, stored, errors, pending_review}
    """
    competitor_id = competitor["id"]
    channel = competitor["channel"]
    base_url = competitor.get("base_url", "")

    scraper = get_scraper(channel, base_url)
    if not scraper:
        return {"error": f"No hay scraper para el canal {channel}"}

    stats = {"found": 0, "matched": 0, "stored": 0, "errors": 0, "pending_review": 0}

    for product in user_products:
        try:
            # Buscar el producto en el competidor
            result = await scraper.search_product(
                ean=product.get("ean"),
                sku=product.get("sku"),
                name=product.get("name"),
            )

            if result.error or not result.products:
                continue

            stats["found"] += len(result.products)

            # Intentar match con el mejor resultado
            for scraped in result.products[:3]:  # Top 3 resultados
                match = await match_product(scraped, [product])

                if match.matched:
                    stats["matched"] += 1

                    # Almacenar snapshot
                    snapshot_id = await _store_snapshot(
                        user_id, competitor_id, scraped, match,
                    )
                    stats["stored"] += 1

                    # Si la confianza es baja, guardar para revisión
                    if match.needs_review:
                        await _store_pending_match(
                            user_id, competitor_id, scraped, match, snapshot_id,
                        )
                        stats["pending_review"] += 1

                    # Evaluar alertas (solo si confianza suficiente)
                    if match.confidence >= AUTO_ACCEPT_THRESHOLD:
                        await _evaluate_alerts(
                            user_id,
                            match.product_sku,
                            match.product_ean,
                            scraped.price,
                            competitor.get("name", "Competidor"),
                        )

                    break  # Usar solo el mejor match

        except Exception as e:
            stats["errors"] += 1
            logger.error(f"Error scraping {product.get('sku')} en {channel}: {e}")

    return stats


async def run_crawl_for_user(user_id: str, competitor_id: Optional[str] = None) -> dict:
    """
    Ejecuta un ciclo completo de scraping para un usuario.

    Args:
        user_id: ID del usuario
        competitor_id: Si se especifica, solo scrapear este competidor

    Returns:
        dict con estadísticas globales del crawl
    """
    logger.info(f"Iniciando crawl para usuario {user_id}")
    start_time = datetime.now(timezone.utc)

    # Obtener competidores activos
    query = {"user_id": user_id, "active": True}
    if competitor_id:
        query["id"] = competitor_id

    competitors = await db.competitors.find(query, {"_id": 0}).to_list(50)
    if not competitors:
        return {"status": "no_competitors", "message": "No hay competidores activos"}

    # Obtener productos del usuario
    user_products = await _get_user_products(user_id)
    if not user_products:
        return {"status": "no_products", "message": "No hay productos para monitorizar"}

    global_stats = {
        "status": "success",
        "competitors_crawled": 0,
        "total_found": 0,
        "total_matched": 0,
        "total_stored": 0,
        "total_errors": 0,
        "total_pending_review": 0,
        "competitor_results": {},
    }

    # Ejecutar scraping con concurrencia limitada
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_COMPETITORS)

    async def _crawl_with_semaphore(comp):
        async with semaphore:
            return comp["id"], await crawl_competitor(user_id, comp, user_products)

    tasks = [_crawl_with_semaphore(comp) for comp in competitors]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    now = datetime.now(timezone.utc).isoformat()

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Error en crawl: {result}")
            global_stats["total_errors"] += 1
            continue

        comp_id, stats = result
        global_stats["competitors_crawled"] += 1
        global_stats["total_found"] += stats.get("found", 0)
        global_stats["total_matched"] += stats.get("matched", 0)
        global_stats["total_stored"] += stats.get("stored", 0)
        global_stats["total_errors"] += stats.get("errors", 0)
        global_stats["total_pending_review"] += stats.get("pending_review", 0)
        global_stats["competitor_results"][comp_id] = stats

        # Actualizar estado del competidor
        crawl_status = "success" if stats.get("errors", 0) == 0 else "partial"
        if stats.get("found", 0) == 0 and stats.get("errors", 0) > 0:
            crawl_status = "error"

        await db.competitors.update_one(
            {"id": comp_id, "user_id": user_id},
            {"$set": {"last_crawl_at": now, "last_crawl_status": crawl_status}},
        )

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    global_stats["duration_seconds"] = round(elapsed, 2)

    if global_stats["total_errors"] > 0 and global_stats["total_stored"] == 0:
        global_stats["status"] = "error"
    elif global_stats["total_errors"] > 0:
        global_stats["status"] = "partial"

    logger.info(
        f"Crawl completado para usuario {user_id}: "
        f"{global_stats['competitors_crawled']} competidores, "
        f"{global_stats['total_stored']} snapshots, "
        f"{elapsed:.1f}s"
    )

    return global_stats
