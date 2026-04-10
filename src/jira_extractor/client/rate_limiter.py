"""Inter-request delay and exponential backoff on rate-limit responses."""
from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, delay_seconds: float = 0.5, max_backoff: float = 60.0) -> None:
        self._delay = delay_seconds
        self._max_backoff = max_backoff
        self._last_request: float = 0.0

    def wait(self) -> None:
        """Sleep for the remainder of the inter-request delay."""
        elapsed = time.monotonic() - self._last_request
        remaining = self._delay - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request = time.monotonic()

    def backoff(self, attempt: int) -> None:
        """Exponential backoff used on 429 / 503 responses."""
        wait = min(2**attempt, self._max_backoff)
        logger.warning("Rate limited — backing off for %.1f seconds (attempt %d)", wait, attempt)
        time.sleep(wait)
        self._last_request = time.monotonic()
