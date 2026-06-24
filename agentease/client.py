from __future__ import annotations

from dataclasses import dataclass, field

from agentease.config import AgentEaseConfig
from agentease.guardrails.pii_scrubber import PiiScrubber
from agentease.offline_registry import offline_client_for
from agentease.telemetry.metrics import InMemoryMetrics, MetricsRecorder
from agentease.templates.base import LlmClient, WorkflowAgent
from agentease.templates.doc_classification_agent import (
    DOC_SPEC,
    DocClassificationAgent,
    DocClassificationResult,
)
from agentease.templates.lead_qualification_agent import (
    LEAD_SPEC,
    LeadQualificationAgent,
    LeadQualificationResult,
)
from agentease.templates.triage_agent import TRIAGE_SPEC, TriageAgent


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
    offline_mode: bool = False
    triage: TriageAgent = field(init=False)
    leads: WorkflowAgent[LeadQualificationResult] = field(init=False)
    docs: WorkflowAgent[DocClassificationResult] = field(init=False)

    def __post_init__(self) -> None:
        self.config = self.config or AgentEaseConfig(
            api_key=self.api_key,
            provider=self.provider,
            model=self.model,
        )
        self.pii_scrubber = self.pii_scrubber or PiiScrubber()
        self.metrics = self.metrics or InMemoryMetrics()
        self.triage = self._build(TriageAgent, TRIAGE_SPEC.name, self.triage_llm_client)
        self.leads = self._build(LeadQualificationAgent, LEAD_SPEC.name)
        self.docs = self._build(DocClassificationAgent, DOC_SPEC.name)

    def _build(
        self,
        agent_cls: type[WorkflowAgent],
        spec_name: str,
        override: LlmClient | None = None,
    ) -> WorkflowAgent:
        llm = override or (offline_client_for(spec_name) if self.offline_mode else None)
        return agent_cls(
            config=self.config,
            pii_scrubber=self.pii_scrubber,
            metrics=self.metrics,
            llm_client=llm,
            max_repair_attempts=self.max_repair_attempts,
        )

    @classmethod
    def from_env(cls) -> AgentEase:
        return cls(config=AgentEaseConfig.from_env())

    @classmethod
    def offline(
        cls,
        pii_scrubber: PiiScrubber | None = None,
        metrics: MetricsRecorder | None = None,
    ) -> AgentEase:
        return cls(
            config=AgentEaseConfig(provider="offline", model="offline-triage"),
            pii_scrubber=pii_scrubber,
            metrics=metrics,
            offline_mode=True,
        )
