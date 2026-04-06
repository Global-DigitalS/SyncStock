"""
Orquestador de scraping de precios de competidores.
Coordina: selección de productos → scraping → matching → almacenamiento → alertas.
OPTIMIZADO: Búsquedas paralelas, alertas diferidas, caché de precios.
"""
import asyncio
import logging
import uuid
from datetime import UTC, datetime

from cachetools import TTLCache

from services.database import db
from services.scrapers import get_scraper
from services.scrapers.base import ScrapedProduct
from services.scrapers.matcher import AUTO_ACCEPT_THRESHOLD, MatchResult, match_product

logger = logging.getLogger(__name__)

# Caché de precios recientes (user_id:sku/ean:competitor_id → price, maxsize=10k, TTL=3600s)
_price_cache: dict = TTLCache(maxsize=10000, ttl=3600)

# Máximo de productos a scrapear por ejecución (para no sobrecargar)
MAX_PRODUCTS_PER_RUN = 200

# Máximo de competidores simultáneos
MAX_CONCURRENT_COMPETITORS = 5

# Máximo de búsquedas paralelas por competidor
MAX_CONCURRENT_SEARCHES_PER_COMPETITOR = 4


async def _get_user_products(user_id: str, limit: int = MAX_PRODUCTS_PER_RUN) -> list[dict]:
    """
    Obtiene los productos del usuario desde el catálogo configurado para monitoreo.
    Incluye el precio final (con margen aplicado) para comparación con competidores.
    """
    from services.sync import calculate_final_price

    # Obtener catálogo configurado por el usuario para monitoreo
    user_config = await db.users.find_one(
        {"id": user_id},
        {"_id": 0, "competitor_monitoring_catalog_id": 1}
    )

    catalog_id = user_config.get("competitor_monitoring_catalog_id") if user_config else None

    # Si no hay configurado, intentar usar el catálogo predeterminado
    if not catalog_id:
        default_catalog = await db.catalogs.find_one(
            {"user_id": user_id, "is_default": True},
            {"_id": 0, "id": 1}
        )

        if not default_catalog:
            # Si no hay predeterminado, usar el primero disponible
            catalogs = await db.catalogs.find(
                {"user_id": user_id},
                {"_id": 0, "id": 1}
            ).limit(1).to_list(1)

            if not catalogs:
                logger.warning(f"Usuario {user_id} no tiene catálogos configurados")
                return []

            catalog_id = catalogs[0]["id"]
        else:
            catalog_id = default_catalog["id"]

    logger.debug(f"Usando catálogo {catalog_id} para usuario {user_id} (monitoreo de precios)")

    # Obtener items activos del catálogo con productos asociados
    pipeline = [
        {
            "$match": {
                "catalog_id": catalog_id,
                "active": True,
                "user_id": user_id,
            }
        },
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "id",
                "as": "product_data",
            }
        },
        {
            "$unwind": "$product_data"
        },
        {
            "$project": {
                "_id": 0,
                "id": "$product_data.id",
                "sku": "$product_data.sku",
                "ean": "$product_data.ean",
                "name": {"$ifNull": ["$custom_name", "$product_data.name"]},
                "base_price": {"$ifNull": ["$custom_price", "$product_data.price"]},
                "supplier_id": "$product_data.supplier_id",
                "category": "$product_data.category",
                "brand": "$product_data.brand",
            }
        },
        {
            "$limit": limit
        },
    ]

    items = await db.catalog_items.aggregate(pipeline).to_list(limit)

    if not items:
        logger.warning(f"Catálogo {catalog_id} no tiene productos activos")
        return []

    # Obtener reglas de margen para el catálogo
    margin_rules = await db.catalog_margin_rules.find(
        {"catalog_id": catalog_id, "user_id": user_id},
        {"_id": 0}
    ).sort("priority", -1).to_list(50)

    # Calcular precio final para cada producto
    products_with_final_price = []
    for item in items:
        # Calcular precio final aplicando reglas de margen
        final_price = calculate_final_price(item["base_price"], item, margin_rules)

        products_with_final_price.append({
            "id": item["id"],
            "sku": item["sku"],
            "ean": item["ean"],
            "name": item["name"],
            "price": final_price,  # Usar precio final para comparación
            "base_price": item["base_price"],
            "supplier_id": item.get("supplier_id"),
            "category": item.get("category"),
        })

    logger.info(f"Obtenidos {len(products_with_final_price)} productos con precio final del catálogo {catalog_id}")
    return products_with_final_price


async def _store_snapshot(
    user_id: str,
    competitor_id: str,
    scraped: ScrapedProduct,
    match: MatchResult,
) -> str:
    """Almacena un snapshot de precio en la BD."""
    now = datetime.now(UTC).isoformat()
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
    now = datetime.now(UTC).isoformat()
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
    sku: str | None,
    ean: str | None,
    competitor_price: float,
    competitor_name: str,
    competitor_id: str = "",
) -> None:
    """
    Evalúa las alertas de precio del usuario para este producto.
    Usa AlertAnalyzer para generar contexto enriquecido (tendencia, posición, margen).
    """
    query = {"user_id": user_id, "active": True}
    or_conditions = []
    if sku:
        or_conditions.append({"sku": sku})
    if ean:
        or_conditions.append({"ean": ean})
    if not or_conditions:
        return

    query["$or"] = or_conditions
    alerts = await db.price_alerts.find(query, {"_id": 0}).to_list(50)
    if not alerts:
        return

    # Generar contexto enriquecido UNA sola vez para todas las alertas del producto
    enriched = None
    try:
        from services.scrapers.alert_analyzer import analyze_price_alert
        enriched = await analyze_price_alert(
            user_id=user_id,
            sku=sku,
            ean=ean,
            competitor_id=competitor_id,
            competitor_name=competitor_name,
            new_price=competitor_price,
            db=db,
        )
    except Exception as ae:
        logger.debug(f"AlertAnalyzer error (no crítico): {ae}")

    for alert in alerts:
        triggered = False
        message = ""

        # Usar mensaje enriquecido si disponible
        base_msg = enriched.message_short if enriched else f"Nuevo precio en {competitor_name}: {competitor_price}€"

        if alert["alert_type"] == "any_change":
            triggered = True
            message = base_msg

        elif alert["alert_type"] == "price_below":
            threshold = alert.get("threshold", 0)
            if competitor_price <= threshold:
                triggered = True
                message = base_msg if enriched else (
                    f"Precio en {competitor_name} ({competitor_price}€) por debajo de {threshold}€"
                )

        elif alert["alert_type"] == "competitor_cheaper":
            product_query = {"user_id": user_id}
            if sku:
                product_query["sku"] = sku
            elif ean:
                product_query["ean"] = ean

            my_product = await db.products.find_one(product_query, {"_id": 0, "price": 1})
            if my_product and competitor_price < my_product["price"]:
                triggered = True
                message = enriched.message_long if enriched else (
                    f"{competitor_name} tiene mejor precio ({competitor_price}€) "
                    f"que el tuyo ({my_product['price']}€)"
                )

        elif alert["alert_type"] == "price_drop":
            threshold_pct = alert.get("threshold", 0)
            prev_snapshot = await db.price_snapshots.find_one(
                {"user_id": user_id, "sku": sku, "scraped_at": {"$lt": datetime.now(UTC).isoformat()}},
                {"_id": 0, "price": 1},
                sort=[("scraped_at", -1)],
            )
            if prev_snapshot and prev_snapshot["price"] > 0:
                drop_pct = ((prev_snapshot["price"] - competitor_price) / prev_snapshot["price"]) * 100
                if drop_pct >= threshold_pct:
                    triggered = True
                    message = enriched.message_long if enriched else (
                        f"Bajada de precio en {competitor_name}: "
                        f"{prev_snapshot['price']}€ → {competitor_price}€ (-{drop_pct:.1f}%)"
                    )

        if triggered:
            now = datetime.now(UTC).isoformat()
            await db.price_alerts.update_one(
                {"id": alert["id"]},
                {"$set": {"last_triggered_at": now}, "$inc": {"trigger_count": 1}},
            )

            channel = alert.get("channel", "app")

            if channel in ("app", "email"):
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "competitor_price",
                    "message": message,
                    # Adjuntar contexto enriquecido si disponible
                    "context": {
                        "trend": enriched.context.trend.value if enriched else None,
                        "your_position": enriched.context.your_position if enriched else None,
                        "action": enriched.context.action.value if enriched else None,
                        "suggested_price": enriched.context.suggested_price if enriched else None,
                        "alert_level": enriched.context.alert_level.value if enriched else "INFO",
                    } if enriched else {},
                    "read": False,
                    "created_at": now,
                }
                await db.notifications.insert_one(notification)
                try:
                    from services.sync import send_realtime_notification
                    await send_realtime_notification(user_id, notification)
                except Exception as ws_err:
                    logger.debug(f"WebSocket push falló: {ws_err}")

            if channel == "email":
                try:
                    await _send_alert_email(user_id, alert, message, competitor_name, competitor_price, sku, ean)
                except Exception as email_err:
                    logger.warning(f"Error enviando email de alerta: {email_err}")

            if channel == "webhook" and alert.get("webhook_url"):
                try:
                    webhook_payload = {
                        "alert_id": alert["id"],
                        "alert_type": alert["alert_type"],
                        "message": message,
                        "competitor_name": competitor_name,
                        "price": competitor_price,
                        "sku": sku,
                        "ean": ean,
                        "triggered_at": now,
                    }
                    if enriched:
                        webhook_payload["context"] = {
                            "trend": enriched.context.trend.value,
                            "your_position": enriched.context.your_position,
                            "your_price": enriched.context.your_price,
                            "best_competitor_price": enriched.context.best_competitor_price,
                            "action": enriched.context.action.value,
                            "suggested_price": enriched.context.suggested_price,
                            "margin_current_percent": enriched.context.margin_current_percent,
                            "margin_if_copy_percent": enriched.context.margin_if_copy_percent,
                        }
                    await _send_alert_webhook(alert["webhook_url"], webhook_payload)
                except Exception as wh_err:
                    logger.warning(f"Error enviando webhook: {wh_err}")

            logger.info(f"Alerta disparada [{alert['alert_type']}]: {message}")


async def _send_alert_email(
    user_id: str,
    alert: dict,
    message: str,
    competitor_name: str,
    competitor_price: float,
    sku: str | None,
    ean: str | None,
) -> None:
    """Envía un email al usuario cuando se dispara una alerta de precio."""
    from services.email_service import get_competitor_alert_email_template, get_email_service_async

    user = await db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "name": 1})
    if not user or not user.get("email"):
        return

    email_service = await get_email_service_async("transactional")
    if not email_service.is_configured():
        logger.debug("Email no configurado, omitiendo envío de alerta")
        return

    product_ref = sku or ean or "N/A"
    template = get_competitor_alert_email_template(
        user_name=user.get("name", "Usuario"),
        alert_type=alert["alert_type"],
        message=message,
        competitor_name=competitor_name,
        competitor_price=competitor_price,
        product_ref=product_ref,
    )

    await email_service.send_email(
        to_email=user["email"],
        subject=template["subject"],
        html_content=template["html"],
        text_content=template["text"],
    )
    logger.info(f"Email de alerta enviado a {user['email']}")


def _is_safe_webhook_url(url: str) -> bool:
    """Valida que la URL del webhook no apunte a redes internas (prevención SSRF)."""
    import ipaddress
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""

        # Solo permitir HTTPS en producción (HTTP para desarrollo)
        if parsed.scheme not in ("https", "http"):
            return False

        # Bloquear hosts internos/reservados
        blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
        if host.lower() in blocked_hosts:
            return False

        # Bloquear rangos de IP privados
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            # Es un hostname, no una IP - verificar patrones internos comunes
            internal_patterns = (".local", ".internal", ".lan", ".corp", ".intranet")
            if any(host.lower().endswith(p) for p in internal_patterns):
                return False

        return True
    except Exception:
        return False


async def _send_alert_webhook(webhook_url: str, payload: dict) -> None:
    """Envía un POST al webhook configurado con los datos de la alerta."""
    import aiohttp

    # Validar URL para prevenir SSRF
    if not _is_safe_webhook_url(webhook_url):
        logger.warning(f"Webhook URL bloqueada por política SSRF: {webhook_url}")
        return

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json", "User-Agent": "SyncStockAlertBot/1.0"},
    ) as resp:
        if resp.status >= 400:
            logger.warning(f"Webhook devolvió status {resp.status}: {webhook_url}")


async def crawl_competitor(
    user_id: str,
    competitor: dict,
    user_products: list[dict],
) -> dict:
    """
    Ejecuta el scraping de un competidor para todos los productos del usuario.
    OPTIMIZADO: Búsquedas paralelas por producto.

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

    # Paralelizar búsquedas de productos
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES_PER_COMPETITOR)

    async def _search_product_in_competitor(product: dict) -> tuple:
        """Busca un producto en el competidor. Retorna (found_count, matched_count, stored_count, errors_count, pending_count)."""
        async with semaphore:
            try:
                # Verificar caché: si tenemos un precio reciente, saltar búsqueda
                cache_key = f"{user_id}:{product.get('sku') or product.get('ean')}:{competitor_id}"
                if cache_key in _price_cache:
                    logger.debug(f"Precio cachéado encontrado para {cache_key}")
                    return (0, 0, 0, 0, 0)

                result = await scraper.search_product(
                    ean=product.get("ean"),
                    sku=product.get("sku"),
                    name=product.get("name"),
                )

                if result.error or not result.products:
                    return (0, 0, 0, 0, 0)

                found_count = len(result.products)
                matched_count = 0
                stored_count = 0
                pending_count = 0

                # Intentar match con el mejor resultado
                for scraped in result.products[:3]:  # Top 3 resultados
                    match = await match_product(scraped, [product])

                    if match.matched:
                        matched_count += 1

                        # Almacenar snapshot
                        snapshot_id = await _store_snapshot(
                            user_id, competitor_id, scraped, match,
                        )
                        stored_count += 1

                        # Cachear el precio encontrado
                        cache_key = f"{user_id}:{match.product_sku or match.product_ean}:{competitor_id}"
                        _price_cache[cache_key] = scraped.price

                        # Si la confianza es baja, guardar para revisión
                        if match.needs_review:
                            await _store_pending_match(
                                user_id, competitor_id, scraped, match, snapshot_id,
                            )
                            pending_count += 1

                        # Evaluar alertas (solo si confianza suficiente)
                        # OPTIMIZADO: Diferir alertas a background
                        if match.confidence >= AUTO_ACCEPT_THRESHOLD:
                            asyncio.create_task(_evaluate_alerts(
                                user_id,
                                match.product_sku,
                                match.product_ean,
                                scraped.price,
                                competitor.get("name", "Competidor"),
                                competitor_id=competitor_id,
                            ))

                        break  # Usar solo el mejor match

                return (found_count, matched_count, stored_count, 0, pending_count)

            except Exception as e:
                logger.error(f"Error scraping {product.get('sku')} en {channel}: {e}")
                return (0, 0, 0, 1, 0)

    # Ejecutar todas las búsquedas en paralelo
    tasks = [_search_product_in_competitor(product) for product in user_products]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    # Agregar resultados
    for found, matched, stored, errors, pending in results:
        stats["found"] += found
        stats["matched"] += matched
        stats["stored"] += stored
        stats["errors"] += errors
        stats["pending_review"] += pending

    return stats


async def run_crawl_for_user(user_id: str, competitor_id: str | None = None) -> dict:
    """
    Ejecuta un ciclo completo de scraping para un usuario.

    Args:
        user_id: ID del usuario
        competitor_id: Si se especifica, solo scrapear este competidor

    Returns:
        dict con estadísticas globales del crawl
    """
    logger.info(f"Iniciando crawl para usuario {user_id}")
    start_time = datetime.now(UTC)

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

    now = datetime.now(UTC).isoformat()

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

    elapsed = (datetime.now(UTC) - start_time).total_seconds()
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

    # Notificación resumen del crawl
    try:
        from services.sync import send_realtime_notification
        summary_msg = (
            f"Crawl de competidores completado: "
            f"{global_stats['competitors_crawled']} competidores, "
            f"{global_stats['total_stored']} precios capturados"
        )
        if global_stats["total_pending_review"] > 0:
            summary_msg += f", {global_stats['total_pending_review']} pendientes de revisión"
        notification = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "competitor_price",
            "message": summary_msg,
            "read": False,
            "created_at": datetime.now(UTC).isoformat(),
        }
        await db.notifications.insert_one(notification)
        await send_realtime_notification(user_id, notification)
    except Exception as e:
        logger.debug(f"Error enviando notificación de resumen de crawl: {e}")

    return global_stats
