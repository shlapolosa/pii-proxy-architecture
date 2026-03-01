"""
Performance Optimizer for PII Detection Service
Implements caching, batching, and resource pooling for improved performance
"""

from functools import lru_cache
import threading
from typing import Dict, Any, List, Tuple
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """
    Performance optimizer implementing caching, batching, and resource pooling
    """

    def __init__(self, cache_size: int = 1000, batch_size: int = 10):
        self.cache_size = cache_size
        self.batch_size = batch_size
        self.request_queue = []
        self.queue_lock = threading.Lock()
        self.cache_lock = threading.Lock()
        self.batch_lock = threading.Lock()
        self.cache = {}
        self.batch_timer = None

    @lru_cache(maxsize=1000)
    def cached_pii_detection(self, text: str, sensitivity: float = 0.5) -> Tuple[bool, List[Dict], float]:
        """
        Cached PII detection with LRU cache

        Args:
            text (str): Text to analyze
            sensitivity (float): Sensitivity threshold

        Returns:
            Tuple[bool, List[Dict], float]: (has_pii, pii_entities, risk_score)
        """
        # This would normally call the actual PII detection service
        # For caching demonstration, we'll simulate the call
        return self._simulate_pii_detection(text, sensitivity)

    def _simulate_pii_detection(self, text: str, sensitivity: float) -> Tuple[bool, List[Dict], float]:
        """
        Simulate PII detection (in a real implementation, this would call the actual service)
        """
        # Simple simulation - in reality this would call the Presidio analyzer
        if "SSN" in text or "email" in text or "address" in text:
            return True, [{"entity_type": "PERSON", "start": 0, "end": 5, "score": 0.8}], 0.8
        return False, [], 0.0

    def batch_process_requests(self, texts: List[str]) -> List[Tuple[bool, List[Dict], float]]:
        """
        Process multiple texts in batch for efficiency

        Args:
            texts (List[str]): List of texts to analyze

        Returns:
            List[Tuple[bool, List[Dict], float]]: Results for each text
        """
        results = []
        for text in texts:
            # In a real implementation, this would batch process with Presidio
            result = self.cached_pii_detection(text)
            results.append(result)
        return results

    def queue_request(self, text: str, callback=None) -> None:
        """
        Queue a request for batch processing

        Args:
            text (str): Text to analyze
            callback: Callback function to call with results
        """
        with self.queue_lock:
            self.request_queue.append((text, callback))

            # If we've reached batch size, process immediately
            if len(self.request_queue) >= self.batch_size:
                self._process_batch()

    def _process_batch(self) -> None:
        """
        Process queued requests in batch
        """
        with self.queue_lock:
            if not self.request_queue:
                return

            # Take up to batch_size requests
            batch = self.request_queue[:self.batch_size]
            self.request_queue = self.request_queue[self.batch_size:]

        # Extract texts for batch processing
        texts = [item[0] for item in batch]

        # Process batch
        try:
            results = self.batch_process_requests(texts)

            # Call callbacks with results
            for i, (_, callback) in enumerate(batch):
                if callback:
                    callback(results[i])

        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")

            # Call callbacks with error
            for _, callback in batch:
                if callback:
                    callback((True, [{"error": str(e)}], 1.0))

    def circuit_breaker(self, func, max_failures: int = 5, timeout: int = 60):
        """
        Circuit breaker pattern for fault tolerance

        Args:
            func: Function to wrap
            max_failures (int): Maximum failures before opening circuit
            timeout (int): Timeout in seconds before allowing test requests

        Returns:
            Wrapped function with circuit breaker
        """
        class CircuitBreaker:
            def __init__(self):
                self.failures = 0
                self.last_failure = 0
                self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

            def call(self, *args, **kwargs):
                if self.state == "OPEN":
                    if time.time() - self.last_failure > timeout:
                        self.state = "HALF_OPEN"
                    else:
                        raise Exception("Circuit breaker is OPEN")

                try:
                    result = func(*args, **kwargs)
                    self.failures = 0
                    self.state = "CLOSED"
                    return result
                except Exception as e:
                    self.failures += 1
                    self.last_failure = time.time()
                    if self.failures >= max_failures:
                        self.state = "OPEN"
                    raise e

        return CircuitBreaker()

# Global instance
optimizer = PerformanceOptimizer()