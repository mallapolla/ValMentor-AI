import time
from django.conf import settings
from .client import get_valkey_client

class RateLimiter:
    """
    Sliding window request rate-limiter using Valkey.
    Enforces customizable access frequency thresholds per user.
    """
    def __init__(self):
        self.client = get_valkey_client()

    def _get_key(self, identifier: str) -> str:
        return f"rate_limit:{identifier}"

    def is_rate_limited(self, identifier: str, limit: int = None, window_seconds: int = None) -> bool:
        """
        Calculates if the request limit in the sliding window has been exceeded.
        Uses Valkey transactional pipelines for speed and atomic security.
        """
        limit = limit or settings.RATE_LIMIT_REQUESTS
        window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        
        key = self._get_key(identifier)
        now = time.time()
        clear_before = now - window_seconds

        # Use transaction pipeline to prevent race conditions
        pipe = self.client.pipeline()
        
        # Remove elements older than window threshold
        pipe.zremrangebyscore(key, 0, clear_before)
        # Fetch current request counts in active window
        pipe.zcard(key)
        # Append new request timestamp
        pipe.zadd(key, {str(now): now})
        # Refresh key expiration
        pipe.expire(key, window_seconds)
        
        # Execute commands
        _, request_count, _, _ = pipe.execute()

        # If count exceeds limits, return rate limited (True)
        return request_count >= limit
