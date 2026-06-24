from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timezone


class RateLimiter:
    """
    Rate limiter in-memory simplu: max 60 request-uri/minut per IP.
    Protecție împotriva brute-force și spam fără dependențe externe.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._store: dict[str, list[float]] = defaultdict(list)

    async def check(self, request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - self._window

        timestamps = [t for t in self._store[ip] if t > window_start]
        if len(timestamps) >= self._max:
            raise HTTPException(status_code=429, detail="Prea multe cereri. Încearcă mai târziu.")

        timestamps.append(now)
        self._store[ip] = timestamps


rate_limiter = RateLimiter()