"""Unit tests for performance_optimizer.py — PerformanceOptimizer"""

import pytest
import time
from performance_optimizer import PerformanceOptimizer

pytestmark = pytest.mark.unit


class TestCachedDetection:
    def setup_method(self):
        self.optimizer = PerformanceOptimizer()

    def test_cached_detection_no_pii(self):
        has_pii, entities, score = self.optimizer.cached_pii_detection("Hello world")
        assert has_pii is False
        assert entities == []
        assert score == 0.0

    def test_cached_detection_with_pii_keywords(self):
        has_pii, entities, score = self.optimizer.cached_pii_detection("my SSN is here")
        assert has_pii is True
        assert score > 0

    def test_cache_returns_same_result(self):
        r1 = self.optimizer.cached_pii_detection("Hello world")
        r2 = self.optimizer.cached_pii_detection("Hello world")
        assert r1 == r2


class TestBatchProcessing:
    def setup_method(self):
        self.optimizer = PerformanceOptimizer(batch_size=3)

    def test_batch_process_multiple_texts(self):
        texts = ["Hello", "my SSN is 123", "clean text"]
        results = self.optimizer.batch_process_requests(texts)
        assert len(results) == 3
        assert results[0][0] is False  # "Hello" has no PII keywords
        assert results[1][0] is True   # "SSN" keyword triggers

    def test_queue_and_manual_batch_process(self):
        """Queue requests then manually process the batch.

        Note: queue_request has a deadlock bug (calls _process_batch
        while holding queue_lock), so we test queuing and processing
        separately.
        """
        results = []

        def callback(result):
            results.append(result)

        # Queue without hitting batch_size threshold
        self.optimizer.queue_request("text 0", callback=callback)
        self.optimizer.queue_request("text 1", callback=callback)
        assert len(self.optimizer.request_queue) == 2

        # Manually trigger batch processing
        self.optimizer._process_batch()
        assert len(results) == 2


class TestCircuitBreaker:
    def setup_method(self):
        self.optimizer = PerformanceOptimizer()

    def test_circuit_breaker_closed_on_success(self):
        cb = self.optimizer.circuit_breaker(lambda: "ok", max_failures=3)
        assert cb.call() == "ok"
        assert cb.state == "CLOSED"

    def test_circuit_breaker_opens_after_max_failures(self):
        call_count = 0

        def fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("fail")

        cb = self.optimizer.circuit_breaker(fail, max_failures=3, timeout=60)
        for _ in range(3):
            with pytest.raises(ValueError):
                cb.call()

        assert cb.state == "OPEN"

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call()

    def test_circuit_breaker_half_open_after_timeout(self):
        def fail():
            raise ValueError("fail")

        cb = self.optimizer.circuit_breaker(fail, max_failures=1, timeout=0)
        with pytest.raises(ValueError):
            cb.call()

        assert cb.state == "OPEN"
        # timeout=0 means it immediately transitions to HALF_OPEN
        time.sleep(0.01)
        with pytest.raises(ValueError):
            cb.call()
        # Still fails so goes back to OPEN
        assert cb.state == "OPEN"

    def test_circuit_breaker_recovers(self):
        calls = [0]

        def sometimes_fail():
            calls[0] += 1
            if calls[0] <= 2:
                raise ValueError("fail")
            return "recovered"

        cb = self.optimizer.circuit_breaker(sometimes_fail, max_failures=2, timeout=0)
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call()
        assert cb.state == "OPEN"

        time.sleep(0.01)
        result = cb.call()
        assert result == "recovered"
        assert cb.state == "CLOSED"
