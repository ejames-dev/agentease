from __future__ import annotations

import time
from contextlib import suppress
from dataclasses import dataclass, field
from threading import Lock, Thread
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class MetricEvent:
    name: str
    duration_ms: float
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)


class MetricsRecorder(Protocol):
    def record(self, event: MetricEvent) -> None: ...


class InMemoryMetrics:
    def __init__(self) -> None:
        self.events: list[MetricEvent] = []
        self._lock = Lock()

    def record(self, event: MetricEvent) -> None:
        with self._lock:
            self.events.append(event)


def record_non_blocking(recorder: MetricsRecorder, event: MetricEvent) -> None:
    """Best-effort metric delivery that never delays or breaks a workflow.

    The bundled in-memory recorder is fast and deterministic, so it is updated
    inline. User-supplied recorders run on a daemon thread and their failures
    are deliberately isolated from SDK execution.
    """

    if isinstance(recorder, InMemoryMetrics):
        with suppress(Exception):
            recorder.record(event)
        return

    with suppress(Exception):
        Thread(target=_record_safely, args=(recorder, event), daemon=True).start()


def _record_safely(recorder: MetricsRecorder, event: MetricEvent) -> None:
    with suppress(Exception):
        recorder.record(event)


def now_ms() -> float:
    return time.perf_counter() * 1000
