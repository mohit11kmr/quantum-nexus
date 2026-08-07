"""
Lightweight in-process metrics + request logging.

No external deps (no prometheus_client / structlog) so Render's free tier stays
lean. Exposes aggregate counters/histograms for /api/metrics and a small logging
middleware that records every HTTP request at INFO level.
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Dict

log = logging.getLogger("quantum_nexus.api")

_HTTP_BUCKETS_MS = [10, 50, 100, 250, 500, 1000, 2500, 5000]


class MetricsCollector:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._requests: Dict[str, int] = defaultdict(int)
        self._status_codes: Dict[int, int] = defaultdict(int)
        self._latency_buckets: Dict[str, int] = defaultdict(int)
        self._total_latency_ms = 0.0
        self._errors = 0

    def record(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        key = f"{method} {path}"
        bucket = next((b for b in _HTTP_BUCKETS_MS if duration_ms < b), None) or _HTTP_BUCKETS_MS[-1]
        with self._lock:
            self._requests[key] += 1
            self._status_codes[status_code] += 1
            self._latency_buckets[str(bucket)] += 1
            self._total_latency_ms += duration_ms
            if status_code >= 500:
                self._errors += 1

    def snapshot(self) -> Dict:
        with self._lock:
            total = sum(self._requests.values()) or 1
            return {
                "uptime_sec": round(time.time() - self._started_at, 2),
                "total_requests": total,
                "errors_5xx": self._errors,
                "avg_latency_ms": round(self._total_latency_ms / total, 2),
                "by_endpoint": dict(sorted(self._requests.items(), key=lambda kv: -kv[1])),
                "by_status": {str(k): v for k, v in sorted(self._status_codes.items())},
                "latency_histogram_ms": dict(sorted(self._latency_buckets.items(), key=lambda kv: int(kv[0]))),
            }


metrics = MetricsCollector()


class MetricsMiddleware:
    """ASGI middleware that times and logs each request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        start = time.perf_counter()
        status_holder = {"status": 0}

        async def _send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, _send_wrapper)
        except Exception:
            status_holder["status"] = 500
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            path = scope.get("path", "?")
            method = scope.get("method", "?")
            status = status_holder["status"]
            metrics.record(method, path, status, duration_ms)
            log.info("%s %s -> %s (%.1f ms)", method, path, status, duration_ms)


class _NoopMetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)
