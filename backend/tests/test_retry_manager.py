"""
Tests for order retry manager with exponential backoff
"""
from datetime import UTC, datetime, timedelta

from services.orders.retry_manager import RetryManager


class TestRetryCalculations:
    """Test exponential backoff calculations"""

    def test_calculate_delay_retry_0(self):
        """First retry should be base delay"""
        delay = RetryManager.calculate_next_retry_delay(0)
        assert delay == 60  # BASE_DELAY_SECONDS

    def test_calculate_delay_retry_1(self):
        """Second retry should be 2x base delay"""
        delay = RetryManager.calculate_next_retry_delay(1)
        assert delay == 120  # 60 * 2

    def test_calculate_delay_retry_2(self):
        """Third retry should be 4x base delay"""
        delay = RetryManager.calculate_next_retry_delay(2)
        assert delay == 240  # 60 * 4

    def test_calculate_delay_retry_3(self):
        """Fourth retry should be 8x base delay"""
        delay = RetryManager.calculate_next_retry_delay(3)
        assert delay == 480  # 60 * 8

    def test_calculate_delay_retry_4(self):
        """Fifth retry should be 16x base delay"""
        delay = RetryManager.calculate_next_retry_delay(4)
        assert delay == 960  # 60 * 16

    def test_calculate_delay_capped_at_max(self):
        """Delay should be capped at 24 hours"""
        delay = RetryManager.calculate_next_retry_delay(20)
        assert delay == RetryManager.MAX_DELAY_SECONDS
        assert delay == 86400  # 24 hours

    def test_calculate_delay_negative_retry(self):
        """Negative retry count should return 0"""
        delay = RetryManager.calculate_next_retry_delay(-1)
        assert delay == 0

    def test_exponential_progression(self):
        """Test exponential progression: 2^n * base_delay"""
        for retry_count in range(5):
            delay = RetryManager.calculate_next_retry_delay(retry_count)
            expected = 60 * (2 ** retry_count)
            assert delay == expected


class TestRetryTiming:
    """Test retry timing calculations"""

    def test_next_retry_time_format(self):
        """Next retry time should be ISO 8601 formatted"""
        next_time = RetryManager.get_next_retry_time(0)
        assert next_time is not None
        assert "T" in next_time  # ISO format has T
        assert "+" in next_time or "Z" in next_time  # Timezone info

    def test_next_retry_time_future(self):
        """Next retry time should be in the future"""
        now = datetime.now(UTC)
        next_time_str = RetryManager.get_next_retry_time(0)
        next_time = datetime.fromisoformat(next_time_str.replace("Z", "+00:00"))

        assert next_time > now
        # Should be approximately 1 minute in future (with small tolerance)
        delta = (next_time - now).total_seconds()
        assert 59 <= delta <= 61  # Allow 1 second tolerance

    def test_next_retry_time_exceeds_max_retries(self):
        """Should return None when max retries exceeded"""
        next_time = RetryManager.get_next_retry_time(RetryManager.MAX_RETRIES)
        assert next_time is None


class TestShouldRetry:
    """Test retry eligibility checks"""

    def test_should_retry_non_error_order(self):
        """Should not retry non-error orders"""
        order = {"status": "completed", "retryCount": 0}
        should_retry, reason = RetryManager.should_retry(order)
        assert should_retry is False
        assert "not in error status" in reason

    def test_should_retry_max_retries_exceeded(self):
        """Should not retry when max retries exceeded"""
        order = {
            "status": "error",
            "retryCount": RetryManager.MAX_RETRIES,
            "id": "test-order"
        }
        should_retry, reason = RetryManager.should_retry(order)
        assert should_retry is False
        assert "exceeded" in reason

    def test_should_retry_too_soon(self):
        """Should not retry if next retry time hasn't passed"""
        future_time = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        order = {
            "status": "error",
            "retryCount": 0,
            "nextRetryAt": future_time,
            "id": "test-order"
        }
        should_retry, reason = RetryManager.should_retry(order)
        assert should_retry is False
        assert "in" in reason  # "in Xh" format

    def test_should_retry_ready(self):
        """Should retry when order is ready"""
        past_time = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        order = {
            "status": "error",
            "retryCount": 0,
            "nextRetryAt": past_time,
            "id": "test-order"
        }
        should_retry, reason = RetryManager.should_retry(order)
        assert should_retry is True
        assert reason is None

    def test_should_retry_no_next_retry_at(self):
        """Should retry if nextRetryAt is not set"""
        order = {
            "status": "error",
            "retryCount": 0,
            "id": "test-order"
        }
        should_retry, reason = RetryManager.should_retry(order)
        assert should_retry is True


class TestRecordRetryAttempt:
    """Test retry attempt recording"""

    def test_record_retry_increments_count(self):
        """Recording retry should increment count"""
        order = {
            "id": "test-order",
            "status": "error",
            "retryCount": 0,
            "retryHistory": []
        }

        updated = RetryManager.record_retry_attempt(order, "Connection timeout")

        assert updated["retryCount"] == 1
        assert len(updated["retryHistory"]) == 1

    def test_record_retry_history_entry(self):
        """Recording retry should add history entry"""
        order = {
            "id": "test-order",
            "status": "error",
            "retryCount": 0,
            "retryHistory": []
        }

        updated = RetryManager.record_retry_attempt(order, "API error")

        entry = updated["retryHistory"][0]
        assert entry["attemptNumber"] == 1
        assert entry["error"] == "API error"
        assert "timestamp" in entry
        assert "delayApplied" in entry

    def test_record_retry_max_retries_fails(self):
        """Recording final retry should mark as permanently failed"""
        order = {
            "id": "test-order",
            "status": "error",
            "retryCount": RetryManager.MAX_RETRIES - 1,
            "retryHistory": []
        }

        updated = RetryManager.record_retry_attempt(order, "Final attempt failed")

        assert updated["retryCount"] == RetryManager.MAX_RETRIES
        assert updated["nextRetryAt"] is None
        assert updated["status"] == "error"
        assert updated["error"]["code"] == "MAX_RETRIES_EXCEEDED"

    def test_record_retry_multiple_attempts(self):
        """Recording multiple retries should track all attempts"""
        order = {
            "id": "test-order",
            "status": "error",
            "retryCount": 0,
            "retryHistory": []
        }

        for i in range(3):
            order = RetryManager.record_retry_attempt(
                order,
                f"Error attempt {i + 1}"
            )

        assert order["retryCount"] == 3
        assert len(order["retryHistory"]) == 3
        assert [e["attemptNumber"] for e in order["retryHistory"]] == [1, 2, 3]


class TestRetryableOrders:
    """Test filtering retryable orders"""

    def test_get_retryable_orders_empty(self):
        """Should return empty list when no retryable orders"""
        orders = [
            {"id": "1", "status": "completed"},
            {"id": "2", "status": "pending"}
        ]

        retryable = RetryManager.get_retryable_orders(orders)
        assert len(retryable) == 0

    def test_get_retryable_orders_filters_correctly(self):
        """Should filter only retryable orders"""
        now = datetime.now(UTC)
        past = (now - timedelta(hours=1)).isoformat()
        future = (now + timedelta(hours=1)).isoformat()

        orders = [
            {"id": "1", "status": "error", "retryCount": 0, "nextRetryAt": past},  # Ready
            {"id": "2", "status": "error", "retryCount": 0, "nextRetryAt": future},  # Too soon
            {"id": "3", "status": "error", "retryCount": RetryManager.MAX_RETRIES},  # Max exceeded
            {"id": "4", "status": "completed"}  # Not error
        ]

        retryable = RetryManager.get_retryable_orders(orders)
        assert len(retryable) == 1
        assert retryable[0]["id"] == "1"


class TestRetryStats:
    """Test retry statistics calculation"""

    def test_calculate_retry_stats(self):
        """Should calculate accurate retry statistics"""
        from services.orders.retry_manager import calculate_retry_stats

        orders = [
            {"status": "completed", "retryCount": 0},
            {"status": "error", "retryCount": 0},
            {"status": "error", "retryCount": 1},
            {"status": "error", "retryCount": 1},
            {"status": "error", "retryCount": RetryManager.MAX_RETRIES}
        ]

        stats = calculate_retry_stats(orders)

        assert stats["total"] == 5
        assert stats["by_retry_count"][0] == 1
        assert stats["by_retry_count"][1] == 2
        assert stats["by_retry_count"][RetryManager.MAX_RETRIES] == 1
        assert stats["permanently_failed"] == 1
