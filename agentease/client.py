from __future__ import annotations

from dataclasses import dataclass

from agentease.config import AgentEaseConfig
from agentease.guardrails.pii_scrubber import PiiScrubber
from agentease.telemetry.metrics import InMemoryMetrics, MetricsRecorder
from agentease.templates.triage_agent import TriageAgent


@dataclass(slots=True)
class AgentEase:
    """Main SDK entrypoint for secure local agent workflows."""

    api_key: str | None = None
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    config: AgentEaseConfig | None = None
    pii_scrubber: PiiScrubber | None = None
    metrics: MetricsRecorder | None = None
    max_repair_attempts: int = 1

    def __post_init__(self) -> None:
        config = self.config or AgentEaseConfig(
            api_key=self.api_key,
            provider=self.provider,
            model=self.model,
        )
        self.pii_scrubber = self.pii_scrubber or PiiScrubber()
        self.metrics = self.metrics or InMemoryMetrics()
        self.triage = TriageAgent(
            config=config,
            pii_scrubber=self.pii_scrubber,
            metrics=self.metrics,
            max_repair_attempts=self.max_repair_attempts,
        )

    @classmethod
    def from_env(cls) -> "AgentEase":
        return cls(config=AgentEaseConfig.from_env())
