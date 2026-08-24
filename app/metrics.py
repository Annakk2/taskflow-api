"""Minimal in-process metrics collection.

Not Prometheus/StatsD — this is a small, dependency-free counter store that
demonstrates observability awareness without building monitoring infrastructure.
Metrics reset when the process restarts, which is acceptable for this project's scope.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class EndpointStats:
    count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0

    @property
    def avg_duration_ms(self) -> float:
        return round(self.total_duration_ms / self.count, 2) if self.count else 0.0


class MetricsCollector:
    def __init__(self) -> None:
        self._lock = Lock()
        self._endpoints: dict[str, EndpointStats] = defaultdict(EndpointStats)
        self._request_count = 0
        self._error_count = 0
        self._tasks_created = 0

    def record_request(self, endpoint: str, duration_ms: float, is_error: bool) -> None:
        with self._lock:
            self._request_count += 1
            stats = self._endpoints[endpoint]
            stats.count += 1
            stats.total_duration_ms += duration_ms
            if is_error:
                self._error_count += 1
                stats.error_count += 1

    def record_task_created(self) -> None:
        with self._lock:
            self._tasks_created += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "request_count": self._request_count,
                "error_count": self._error_count,
                "tasks_created": self._tasks_created,
                "endpoints": {
                    name: {
                        "count": stats.count,
                        "error_count": stats.error_count,
                        "avg_duration_ms": stats.avg_duration_ms,
                    }
                    for name, stats in self._endpoints.items()
                },
            }


metrics = MetricsCollector()


class Timer:
    """Small context manager for measuring elapsed wall-clock time in ms."""

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc_info) -> None:
        self.duration_ms = (time.perf_counter() - self._start) * 1000
