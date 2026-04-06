"""
Scheduler para ejecutar crawls periódicos de precios de competidores.
Se ejecuta cada 8 horas vía APScheduler.
"""
import logging

from services.database import db
from services.scrapers.orchestrator import run_crawl_for_user

logger = logging.getLogger(__name__)


async def run_scheduled_crawls():
    """
    Job programado: ejecuta un crawl para cada usuario que tenga
    al menos un competidor activo.
    """
    logger.info("Iniciando crawl programado de competidores...")

    # Obtener usuarios con competidores activos
    pipeline = [
        {"$match": {"active": True}},
        {"$group": {"_id": "$user_id"}},
    ]
    user_ids = []
    async for doc in db.competitors.aggregate(pipeline):
        user_ids.append(doc["_id"])

    if not user_ids:
        logger.info("No hay usuarios con competidores activos. Crawl omitido.")
        return

    logger.info(f"Ejecutando crawl para {len(user_ids)} usuarios")

    total_stored = 0
    total_errors = 0

    for user_id in user_ids:
        try:
            result = await run_crawl_for_user(user_id)
            total_stored += result.get("total_stored", 0)
            total_errors += result.get("total_errors", 0)
        except Exception as e:
            logger.error(f"Error en crawl programado para usuario {user_id}: {e}")
            total_errors += 1

    logger.info(
        f"Crawl programado completado: {len(user_ids)} usuarios, "
        f"{total_stored} snapshots guardados, {total_errors} errores"
    )
