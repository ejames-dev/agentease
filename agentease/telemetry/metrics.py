from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class MetricEvent:
    name: str
    duration_ms: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)


class MetricsRecorder(Protocol):
    def record(self, event: MetricEvent) -> None:
        ...


class InMemoryMetrics:
    def __init__(self) -> None:
        self.events: list[MetricEvent] = []

    def record(self, event: MetricEvent) -> None:
        self.events.append(event)


def now_ms() -> float:
    return time.perf_counter() * 1000
