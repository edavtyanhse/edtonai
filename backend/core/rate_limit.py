"""Small in-process rate limiter for abuse-prone API paths."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitRule:
    """Sliding-window rate limit rule."""

    max_requests: int
    window_seconds: int = 60


class InMemoryRateLimiter:
    """In-process sliding-window limiter.

    This is a safe baseline for a single app instance. A distributed deployment
    should replace it with Redis or provider-level rate limiting.
    """

    def __init__(self) -> None:
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str, rule: RateLimitRule) -> bool:
        """Return True if request is within the configured rule."""
        now = time.monotonic()
        cutoff = now - rule.window_seconds
        async with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= rule.max_requests:
                return False
            hits.append(now)
            return True
