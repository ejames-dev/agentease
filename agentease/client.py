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
    DocumentClassificationResult,
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
    timeout: float = 30
    max_tokens: int = 800
    config: AgentEaseConfig | None = None
    pii_scrubber: PiiScrubber | None = None
    metrics: MetricsRecorder | None = None
    llm_client: LlmClient | None = None
    triage_llm_client: LlmClient | None = None
    max_repair_attempts: int = 1
    offline_mode: bool = False
    triage: TriageAgent = field(init=False)
    lead_qualification: LeadQualificationAgent = field(init=False)
    document_classification: DocClassificationAgent = field(init=False)
    leads: WorkflowAgent[LeadQualificationResult] = field(init=False)
    docs: WorkflowAgent[DocumentClassificationResult] = field(init=False)

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = AgentEaseConfig(
                api_key=self.api_key,
                provider=self.provider,
                model=self.model,
                timeout=self.timeout,
                max_tokens=self.max_tokens,
            )
        self.pii_scrubber = self.pii_scrubber if self.pii_scrubber is not None else PiiScrubber()
        self.metrics = self.metrics if self.metrics is not None else InMemoryMetrics()
        self.triage = self._build(TriageAgent, TRIAGE_SPEC.name, self.triage_llm_client)
        self.lead_qualification = self._build(LeadQualificationAgent, LEAD_SPEC.name)
        self.document_classification = self._build(DocClassificationAgent, DOC_SPEC.name)
        # Compatibility aliases retained through the 0.3 release line.
        self.leads = self.lead_qualification
        self.docs = self.document_classification

    def _build(
        self,
        agent_cls: type[WorkflowAgent],
        spec_name: str,
        override: LlmClient | None = None,
    ) -> WorkflowAgent:
        if override is not None:
            llm = override
        elif self.llm_client is not None:
            llm = self.llm_client
        elif self.offline_mode:
            llm = offline_client_for(spec_name)
        else:
            llm = None
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
