"""
Order retry manager with exponential backoff
Handles automatic retries for failed order synchronization
"""
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class RetryManager:
    """Manages retry logic with exponential backoff for failed orders"""

    # Retry configuration
    MAX_RETRIES = 5
    BASE_DELAY_SECONDS = 60  # 1 minute initial delay
    MAX_DELAY_SECONDS = 86400  # 24 hours max delay
    EXPONENTIAL_BASE = 2  # 2x exponential backoff

    @staticmethod
    def calculate_next_retry_delay(retry_count: int) -> int:
        """
        Calculate delay in seconds using exponential backoff formula:
        delay = base_delay * (2 ^ retry_count)

        With max cap of 24 hours.

        Args:
            retry_count: Number of retries already attempted (0-indexed)

        Returns:
            Delay in seconds
        """
        if retry_count < 0:
            return 0

        # Calculate exponential delay: 2^retry_count * base_delay
        delay = RetryManager.BASE_DELAY_SECONDS * (
            RetryManager.EXPONENTIAL_BASE ** retry_count
        )

        # Cap at maximum delay
        delay = min(int(delay), RetryManager.MAX_DELAY_SECONDS)

        logger.debug(f"Retry {retry_count}: calculated delay = {delay}s ({delay/3600:.1f}h)")
        return delay

    @staticmethod
    def get_next_retry_time(retry_count: int) -> str:
        """
        Get the ISO timestamp when the next retry should occur

        Args:
            retry_count: Current retry count

        Returns:
            ISO 8601 formatted datetime string
        """
        if retry_count >= RetryManager.MAX_RETRIES:
            return None

        delay_seconds = RetryManager.calculate_next_retry_delay(retry_count)
        next_retry = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        return next_retry.isoformat()

    @staticmethod
    def should_retry(order: dict) -> Tuple[bool, Optional[str]]:
        """
        Determine if an order should be retried

        Args:
            order: Order document from MongoDB

        Returns:
            Tuple of (should_retry, reason)
        """
        # Only retry orders with error status
        if order.get("status") != "error":
            return False, "Order is not in error status"

        # Check if max retries exceeded
        retry_count = order.get("retryCount", 0)
        if retry_count >= RetryManager.MAX_RETRIES:
            return False, f"Max retries ({RetryManager.MAX_RETRIES}) exceeded"

        # Check if it's time for retry
        next_retry_str = order.get("nextRetryAt")
        if next_retry_str:
            try:
                next_retry = datetime.fromisoformat(next_retry_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                if now < next_retry:
                    wait_time = (next_retry - now).total_seconds()
                    return False, f"Next retry in {wait_time:.0f}s"
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid nextRetryAt format: {next_retry_str}, error: {e}")

        return True, None

    @staticmethod
    def record_retry_attempt(order: dict, error_message: str) -> dict:
        """
        Record a failed retry attempt in the order history

        Args:
            order: Order document
            error_message: Error message from the failed attempt

        Returns:
            Updated order document
        """
        retry_count = order.get("retryCount", 0)
        retry_history = order.get("retryHistory", [])

        # Record this attempt
        retry_history.append({
            "attemptNumber": retry_count + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error_message,
            "delayApplied": RetryManager.calculate_next_retry_delay(retry_count)
        })

        # Update order document
        order["retryCount"] = retry_count + 1
        order["retryHistory"] = retry_history

        # Set next retry time if max retries not exceeded
        if retry_count + 1 < RetryManager.MAX_RETRIES:
            order["nextRetryAt"] = RetryManager.get_next_retry_time(retry_count + 1)
        else:
            # Mark as permanently failed
            order["status"] = "error"
            order["error"] = {
                "code": "MAX_RETRIES_EXCEEDED",
                "message": f"Order failed after {RetryManager.MAX_RETRIES} retry attempts"
            }
            order["nextRetryAt"] = None

        logger.info(
            f"Order {order.get('id')}: retry {retry_count + 1}/{RetryManager.MAX_RETRIES}, "
            f"next retry at {order.get('nextRetryAt', 'Never')}"
        )

        return order

    @staticmethod
    def get_retryable_orders(orders: list) -> list:
        """
        Filter orders that are eligible for retry

        Args:
            orders: List of order documents

        Returns:
            List of orders that should be retried
        """
        retryable = []
        for order in orders:
            should_retry, reason = RetryManager.should_retry(order)
            if should_retry:
                retryable.append(order)
                logger.debug(f"Order {order.get('id')} eligible for retry")
            else:
                logger.debug(f"Order {order.get('id')} not eligible: {reason}")

        return retryable


def calculate_retry_stats(orders: list) -> dict:
    """
    Calculate retry statistics for a batch of orders

    Args:
        orders: List of order documents

    Returns:
        Dictionary with retry statistics
    """
    stats = {
        "total": len(orders),
        "retryable": 0,
        "permanently_failed": 0,
        "by_retry_count": {},
        "total_wait_time": 0
    }

    for order in orders:
        if order.get("status") == "error":
            retry_count = order.get("retryCount", 0)
            stats["by_retry_count"][retry_count] = stats["by_retry_count"].get(retry_count, 0) + 1

            should_retry, _ = RetryManager.should_retry(order)
            if should_retry:
                stats["retryable"] += 1
            elif retry_count >= RetryManager.MAX_RETRIES:
                stats["permanently_failed"] += 1

    return stats
