from __future__ import annotations

import time
import threading
from collections import deque
from typing import Deque


class RateLimiter:
    """
    Simple thread-safe rate limiter based on a sliding window of timestamps.

    It ensures that at most `max_calls` happen in each `period` seconds.
    """

    def __init__(self, max_calls: int, period: float) -> None:
        if max_calls <= 0:
            raise ValueError("max_calls must be positive")
        if period <= 0:
            raise ValueError("period must be positive")

        self.max_calls = max_calls
        self.period = period
        self._lock = threading.Lock()
        self._calls: Deque[float] = deque()

    def acquire(self) -> None:
        """
        Block until a call is allowed according to the rate limit.
        """
        while True:
            with self._lock:
                now = time.monotonic()

                # Drop timestamps that are outside the current window
                while self._calls and self._calls[0] <= now - self.period:
                    self._calls.popleft()

                if len(self._calls) < self.max_calls:
                    self._calls.append(now)
                    return

                earliest = self._calls[0]
                delay = earliest + self.period - now

            if delay > 0:
                time.sleep(delay)
            else:
                # If delay is negative for some reason, loop again immediately.
                time.sleep(0)
