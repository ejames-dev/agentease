from __future__ import annotations

from dataclasses import dataclass, field

from agentease.config import AgentEaseConfig
from agentease.guardrails.pii_scrubber import PiiScrubber
from agentease.offline import OfflineTriageLlmClient
from agentease.telemetry.metrics import InMemoryMetrics, MetricsRecorder
from agentease.templates.triage_agent import LlmClient, TriageAgent


@dataclass(slots=True)
class AgentEase:
    """Main SDK entrypoint for secure local agent workflows."""

    api_key: str | None = None
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    config: AgentEaseConfig | None = None
    pii_scrubber: PiiScrubber | None = None
    metrics: MetricsRecorder | None = None
    triage_llm_client: LlmClient | None = None
    max_repair_attempts: int = 1
    triage: TriageAgent = field(init=False)

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
            llm_client=self.triage_llm_client,
            max_repair_attempts=self.max_repair_attempts,
        )

    @classmethod
    def from_env(cls) -> "AgentEase":
        return cls(config=AgentEaseConfig.from_env())

    @classmethod
    def offline(
        cls,
        pii_scrubber: PiiScrubber | None = None,
        metrics: MetricsRecorder | None = None,
    ) -> "AgentEase":
        return cls(
            config=AgentEaseConfig(provider="offline", model="offline-triage"),
            pii_scrubber=pii_scrubber,
            metrics=metrics,
            triage_llm_client=OfflineTriageLlmClient(),
        )
