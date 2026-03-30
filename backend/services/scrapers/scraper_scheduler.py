"""
Scraper Scheduler Service
Schedules and manages competitor price scraping jobs with retry logic and monitoring.
Similar to BullMQ but for Python: job queue, retries, concurrency limits, monitoring.

Features:
- Scheduled crawls with configurable intervals (1/6/12/24 hours)
- Exponential backoff retry logic (3, 5, 10 minutes)
- Concurrency control (max 3 simultaneous scrapes per user)
- Job status monitoring and detailed logging
- Automatic failure recovery and dead-letter queue
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from enum import Enum
from dataclasses import dataclass, asdict

from services.database import db

logger = logging.getLogger(__name__)

# Retry strategy: exponential backoff (in minutes)
RETRY_DELAYS = [3, 5, 10]  # First retry after 3 min, then 5 min, then 10 min
MAX_RETRIES = len(RETRY_DELAYS)

# Concurrency limits
MAX_CONCURRENT_CRAWLS_PER_USER = 3
MAX_CONCURRENT_CRAWLS_SYSTEM_WIDE = 10

# Job status enum
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class CrawlJob:
    """Representa un trabajo de scraping programado."""
    id: str
    user_id: str
    competitor_id: str
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_retries: int = MAX_RETRIES
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    products_found: int = 0
    products_matched: int = 0
    products_alerts: int = 0
    duration_seconds: Optional[float] = None
    next_retry_at: Optional[str] = None
    scheduled_for: Optional[str] = None  # Timestamp when scheduled to run

    def to_dict(self) -> dict:
        """Convert to dict for MongoDB storage."""
        d = asdict(self)
        # Serialize enum values
        if isinstance(d.get("status"), JobStatus):
            d["status"] = d["status"].value
        return d

    # Campos válidos del dataclass (para filtrar datos de MongoDB)
    _VALID_FIELDS = {
        "id", "user_id", "competitor_id", "status", "attempts", "max_retries",
        "started_at", "completed_at", "error_message", "products_found",
        "products_matched", "products_alerts", "duration_seconds",
        "next_retry_at", "scheduled_for",
    }

    @classmethod
    def from_dict(cls, data: dict) -> "CrawlJob":
        """Create from MongoDB document."""
        filtered = {k: v for k, v in data.items() if k in cls._VALID_FIELDS}
        # Ensure required fields have defaults
        filtered.setdefault("id", "")
        filtered.setdefault("user_id", "")
        filtered.setdefault("competitor_id", "")
        return cls(**filtered)


async def create_crawl_job(
    user_id: str,
    competitor_id: str,
    scheduled_for: Optional[datetime] = None
) -> CrawlJob:
    """
    Create a new crawl job.

    Args:
        user_id: User ID
        competitor_id: Competitor ID to crawl
        scheduled_for: When to schedule (None = immediate)

    Returns:
        Created CrawlJob
    """
    job = CrawlJob(
        id=str(uuid.uuid4()),
        user_id=user_id,
        competitor_id=competitor_id,
        scheduled_for=scheduled_for.isoformat() if scheduled_for else None
    )

    # Store in database
    await db.crawl_jobs.insert_one({
        **job.to_dict(),
        "_id": job.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": job.status.value
    })

    logger.info(f"Crawl job created: {job.id} for competitor {competitor_id}")
    return job


async def get_job(job_id: str) -> Optional[CrawlJob]:
    """Get a crawl job by ID."""
    doc = await db.crawl_jobs.find_one({"_id": job_id})
    if not doc:
        return None
    doc.pop("_id", None)
    doc.pop("created_at", None)
    return CrawlJob.from_dict(doc)


async def update_job_status(
    job_id: str,
    status: JobStatus,
    **kwargs
) -> bool:
    """Update job status with additional fields."""
    update_data = {
        "status": status.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **kwargs
    }

    result = await db.crawl_jobs.update_one(
        {"_id": job_id},
        {"$set": update_data}
    )

    return result.modified_count > 0


async def schedule_job_retry(job_id: str, attempt: int) -> bool:
    """
    Schedule a job retry with exponential backoff.

    Args:
        job_id: Job ID to retry
        attempt: Current attempt number (0-indexed)

    Returns:
        True if retry scheduled, False if max retries exceeded
    """
    if attempt >= MAX_RETRIES:
        logger.warning(f"Max retries exceeded for job {job_id}")
        return False

    delay_minutes = RETRY_DELAYS[attempt]
    next_retry = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)

    await update_job_status(
        job_id,
        JobStatus.RETRYING,
        attempts=attempt + 1,
        next_retry_at=next_retry.isoformat(),
        error_message=None
    )

    logger.info(f"Retry scheduled for job {job_id} in {delay_minutes} minutes")
    return True


async def get_pending_jobs(
    limit: int = 50,
    max_age_hours: int = 24
) -> List[CrawlJob]:
    """
    Get pending or retrying jobs ready to execute.

    Args:
        limit: Max number of jobs to return
        max_age_hours: Don't return jobs older than this (prevent stale jobs)

    Returns:
        List of CrawlJob objects ready to run
    """
    cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()

    docs = await db.crawl_jobs.find({
        "status": {"$in": [JobStatus.PENDING.value, JobStatus.RETRYING.value]},
        "created_at": {"$gte": cutoff_time},
        # For retrying jobs, only return if retry time has passed
        "$or": [
            {"status": JobStatus.PENDING.value},
            {
                "status": JobStatus.RETRYING.value,
                "next_retry_at": {"$lte": datetime.now(timezone.utc).isoformat()}
            }
        ]
    }).limit(limit).to_list(limit)

    jobs = []
    for doc in docs:
        doc.pop("_id", None)
        doc.pop("created_at", None)
        doc.pop("updated_at", None)
        jobs.append(CrawlJob.from_dict(doc))

    return jobs


async def get_active_crawl_count(user_id: str) -> int:
    """Get number of currently running crawls for a user."""
    count = await db.crawl_jobs.count_documents({
        "user_id": user_id,
        "status": JobStatus.RUNNING.value
    })
    return count


async def can_start_crawl(user_id: str) -> tuple[bool, Optional[str]]:
    """
    Check if user can start a new crawl (respects concurrency limits).

    Returns:
        (can_start, reason_if_not)
    """
    active_count = await get_active_crawl_count(user_id)

    if active_count >= MAX_CONCURRENT_CRAWLS_PER_USER:
        return False, f"Ya hay {active_count} scraping activos. Máximo: {MAX_CONCURRENT_CRAWLS_PER_USER}"

    return True, None


async def mark_job_running(job_id: str) -> bool:
    """Mark a job as running with start timestamp."""
    return await update_job_status(
        job_id,
        JobStatus.RUNNING,
        started_at=datetime.now(timezone.utc).isoformat()
    )


async def mark_job_completed(
    job_id: str,
    products_found: int,
    products_matched: int,
    products_alerts: int,
    duration_seconds: float
) -> bool:
    """Mark a job as completed with results."""
    now = datetime.now(timezone.utc)

    return await update_job_status(
        job_id,
        JobStatus.COMPLETED,
        completed_at=now.isoformat(),
        products_found=products_found,
        products_matched=products_matched,
        products_alerts=products_alerts,
        duration_seconds=duration_seconds
    )


async def mark_job_failed(job_id: str, error_message: str) -> bool:
    """Mark a job as failed with error message."""
    return await update_job_status(
        job_id,
        JobStatus.FAILED,
        error_message=error_message,
        completed_at=datetime.now(timezone.utc).isoformat()
    )


async def get_job_stats(user_id: str, days: int = 7) -> dict:
    """
    Get job execution statistics for a user.

    Returns:
        Stats including success rate, avg duration, recent errors, etc.
    """
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Aggregate pipeline for stats
    stats = await db.crawl_jobs.aggregate([
        {
            "$match": {
                "user_id": user_id,
                "created_at": {"$gte": cutoff_date}
            }
        },
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "avg_duration": {"$avg": "$duration_seconds"},
                "total_products_found": {"$sum": "$products_found"},
                "total_products_matched": {"$sum": "$products_matched"},
                "total_alerts": {"$sum": "$products_alerts"}
            }
        }
    ]).to_list(None)

    # Format results
    result = {
        "period_days": days,
        "total_jobs": 0,
        "completed": 0,
        "failed": 0,
        "retrying": 0,
        "avg_duration_seconds": 0,
        "total_products_found": 0,
        "total_products_matched": 0,
        "total_alerts": 0,
        "success_rate": 0.0
    }

    for stat in stats:
        status = stat["_id"]
        count = stat["count"]
        result["total_jobs"] += count

        if status == "completed":
            result["completed"] = count
            result["avg_duration_seconds"] = stat.get("avg_duration", 0)
            result["total_products_found"] = stat.get("total_products_found", 0)
            result["total_products_matched"] = stat.get("total_products_matched", 0)
            result["total_alerts"] = stat.get("total_alerts", 0)
        elif status == "failed":
            result["failed"] = count
        elif status == "retrying":
            result["retrying"] = count

    if result["total_jobs"] > 0:
        result["success_rate"] = round(result["completed"] / result["total_jobs"] * 100, 2)

    return result


async def schedule_user_crawls(user_id: str) -> int:
    """
    Schedule crawls for all active competitors of a user.
    Only schedules if user has enabled auto-sync.

    Returns:
        Number of jobs scheduled
    """
    # Get user sync settings
    user = await db.users.find_one({"id": user_id})
    if not user:
        return 0

    sync_config = user.get("sync_config", {})
    if not sync_config.get("sync_competitors"):
        return 0

    interval_hours = sync_config.get("competitor_sync_interval")
    if not interval_hours:
        return 0

    # Get active competitors
    competitors = await db.competitors.find({
        "user_id": user_id,
        "active": True
    }).to_list(None)

    if not competitors:
        return 0

    # Schedule a job for each competitor
    jobs_scheduled = 0
    scheduled_for = datetime.now(timezone.utc) + timedelta(hours=interval_hours)

    for competitor in competitors:
        try:
            await create_crawl_job(user_id, competitor["id"], scheduled_for)
            jobs_scheduled += 1
        except Exception as e:
            logger.error(f"Error scheduling crawl for competitor {competitor['id']}: {e}")

    logger.info(f"Scheduled {jobs_scheduled} crawls for user {user_id}")
    return jobs_scheduled


async def cleanup_old_jobs(days: int = 30) -> int:
    """
    Clean up old completed/failed jobs (archive to history).

    Args:
        days: Delete jobs older than this many days

    Returns:
        Number of jobs deleted
    """
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    result = await db.crawl_jobs.delete_many({
        "created_at": {"$lt": cutoff_date},
        "status": {"$in": [JobStatus.COMPLETED.value, JobStatus.FAILED.value]}
    })

    logger.info(f"Cleaned up {result.deleted_count} old crawl jobs")
    return result.deleted_count


async def get_failed_jobs(limit: int = 20) -> List[Dict]:
    """Get recent failed jobs for monitoring/alerting."""
    docs = await db.crawl_jobs.find({
        "status": JobStatus.FAILED.value
    }).sort("completed_at", -1).limit(limit).to_list(limit)

    for doc in docs:
        doc.pop("_id", None)

    return docs
