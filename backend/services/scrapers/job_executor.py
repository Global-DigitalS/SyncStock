"""
Job Executor: Ejecuta trabajos de scraping de la cola de scheduler
Integra scraper_scheduler con orchestrator para ejecución con retry y monitoreo.

Responsabilidades:
- Consume jobs pendientes de scraper_scheduler
- Ejecuta orchestrator.crawl_competitor para cada job
- Registra resultados y maneja reintentos automáticos
- Captura métricas de ejecución (duración, productos, alertas)
- Respeta límites de concurrencia por usuario
"""
import asyncio
import logging
from datetime import UTC, datetime

from services.database import db
from services.scrapers.orchestrator import run_crawl_for_user
from services.scrapers.scraper_scheduler import (
    can_start_crawl,
    get_pending_jobs,
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
    schedule_job_retry,
)

logger = logging.getLogger(__name__)

# Control de ejecución concurrente
_active_jobs = {}
_job_lock = asyncio.Lock()


async def execute_job(job_id: str, competitor_id: str, user_id: str) -> bool:
    """
    Ejecuta un trabajo de scraping de competidor.

    Args:
        job_id: ID del trabajo
        competitor_id: ID del competidor a scrapear
        user_id: ID del usuario propietario

    Returns:
        True si éxito, False si error (puede reintentar)
    """
    # Verificar límites de concurrencia
    can_start, reason = await can_start_crawl(user_id)
    if not can_start:
        logger.warning(f"Cannot start crawl for job {job_id}: {reason}")
        return False

    async with _job_lock:
        if job_id in _active_jobs:
            logger.warning(f"Job {job_id} already running")
            return False
        _active_jobs[job_id] = True

    try:
        # Marcar como ejecutándose
        await mark_job_running(job_id)

        # Verificar que el competidor existe y está activo
        competitor = await db.competitors.find_one({"id": competitor_id, "user_id": user_id})
        if not competitor:
            await mark_job_failed(job_id, "Competidor no encontrado")
            return False

        if not competitor.get("active"):
            await mark_job_failed(job_id, "Competidor inactivo")
            return False

        # Ejecutar scraping usando run_crawl_for_user (que acepta competitor_id)
        logger.info(f"Starting crawl job {job_id} for competitor {competitor_id}")
        start_time = datetime.now(UTC)

        result = await run_crawl_for_user(user_id, competitor_id=competitor_id)

        end_time = datetime.now(UTC)
        duration_seconds = (end_time - start_time).total_seconds()

        status = result.get("status", "error")
        if status in ("success", "partial"):
            products_found = result.get("total_found", 0)
            products_matched = result.get("total_matched", 0)
            products_alerts = result.get("total_stored", 0)

            await mark_job_completed(
                job_id,
                products_found=products_found,
                products_matched=products_matched,
                products_alerts=products_alerts,
                duration_seconds=duration_seconds
            )

            logger.info(
                f"Job {job_id} completed: {products_found} found, "
                f"{products_matched} matched in {duration_seconds}s"
            )
            return True

        else:
            error_msg = result.get("message", result.get("error", "Error desconocido en scraping"))
            logger.error(f"Job {job_id} failed: {error_msg}")
            await mark_job_failed(job_id, error_msg)
            return False

    except TimeoutError:
        error_msg = "Timeout durante scraping"
        logger.error(f"Job {job_id} timeout: {error_msg}")
        await mark_job_failed(job_id, error_msg)
        return False

    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        logger.exception(f"Job {job_id} exception: {error_msg}")
        await mark_job_failed(job_id, error_msg)
        return False

    finally:
        async with _job_lock:
            _active_jobs.pop(job_id, None)


async def process_pending_jobs(batch_size: int = 10, timeout_minutes: int = 30) -> dict:
    """
    Procesa una tanda de trabajos pendientes con timeout global.

    Args:
        batch_size: Número máximo de jobs a procesar
        timeout_minutes: Timeout total en minutos

    Returns:
        Dict con estadísticas de ejecución
    """
    logger.info(f"Processing pending jobs (batch_size={batch_size})")

    stats = {
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "retried": 0,
    }

    try:
        # Obtener jobs pendientes
        pending_jobs = await get_pending_jobs(limit=batch_size)

        if not pending_jobs:
            logger.debug("No pending jobs found")
            return stats

        logger.info(f"Found {len(pending_jobs)} pending jobs")

        # Ejecutar jobs con timeout total
        tasks = [
            asyncio.wait_for(
                execute_job(job.id, job.competitor_id, job.user_id),
                timeout=timeout_minutes * 60
            )
            for job in pending_jobs
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Procesar resultados
        for job, result in zip(pending_jobs, results):
            stats["processed"] += 1

            if isinstance(result, Exception):
                if isinstance(result, asyncio.TimeoutError):
                    logger.error(f"Job {job.id} timed out")
                    # Intentar reintentar
                    if await schedule_job_retry(job.id, job.attempts):
                        stats["retried"] += 1
                    else:
                        stats["failed"] += 1
                else:
                    logger.error(f"Job {job.id} error: {result}")
                    stats["failed"] += 1

            elif result is True:
                stats["succeeded"] += 1

            else:
                # Falló pero sin excepción - intentar reintentar
                if await schedule_job_retry(job.id, job.attempts):
                    stats["retried"] += 1
                else:
                    stats["failed"] += 1

    except Exception as e:
        logger.exception(f"Error processing batch: {e}")

    logger.info(f"Batch processing complete: {stats}")
    return stats


async def start_scheduler_worker(
    poll_interval_seconds: int = 60,
    batch_size: int = 10,
    max_runtime_hours: int = 1
):
    """
    Worker que ejecuta continuamente jobs pendientes.

    Args:
        poll_interval_seconds: Intervalo entre chequeos de jobs pendientes
        batch_size: Número de jobs a procesar por lote
        max_runtime_hours: Máximo tiempo para ejecutar el worker

    NOTA: Se ejecuta de forma continua en background. Típicamente se corre en un
    proceso separado (en producción usando supervisord o similar).
    """
    logger.info(f"Starting scheduler worker (poll_interval={poll_interval_seconds}s)")

    start_time = datetime.now(UTC)
    max_duration = max_runtime_hours * 3600

    try:
        while True:
            # Chequear si se ha excedido el runtime máximo
            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            if elapsed > max_duration:
                logger.info(f"Scheduler worker max_runtime ({max_runtime_hours}h) exceeded, exiting")
                break

            # Procesar lote de jobs
            try:
                await process_pending_jobs(batch_size=batch_size)
            except Exception as e:
                logger.error(f"Error in job processing loop: {e}")
                # Continuar intentando

            # Esperar antes del siguiente chequeo
            await asyncio.sleep(poll_interval_seconds)

    except asyncio.CancelledError:
        logger.info("Scheduler worker cancelled")
    except Exception as e:
        logger.exception(f"Scheduler worker fatal error: {e}")


def get_active_jobs_count() -> int:
    """Obtiene número de jobs en ejecución actualmente."""
    return len(_active_jobs)


async def cancel_job(job_id: str) -> bool:
    """
    Cancela un job en ejecución (si es posible).

    Returns:
        True si fue cancelado, False si no estaba ejecutándose
    """
    if job_id in _active_jobs:
        # Nota: aiohttp/asyncio no permite cancellation granular,
        # marcamos como cancelado y esperamos que termine naturalmente
        from services.scrapers.scraper_scheduler import JobStatus, update_job_status

        await update_job_status(job_id, JobStatus.CANCELLED)
        logger.info(f"Job {job_id} marked for cancellation")
        return True

    return False
