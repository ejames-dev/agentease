from __future__ import annotations

import json
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from agentease.config import AgentEaseConfig
from agentease.guardrails.json_enforcer import enforce_json_schema
from agentease.guardrails.pii_scrubber import PiiScrubber, ScrubResult
from agentease.telemetry.metrics import MetricEvent, MetricsRecorder, now_ms


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["billing", "technical", "account", "sales", "other"]
    priority: Literal["low", "medium", "high", "urgent"]
    summary: str = Field(min_length=1)
    suggested_reply: str = Field(min_length=1)


class LlmClient(Protocol):
    def complete(self, prompt: str) -> str:
        ...


class LiteLlmClient:
    def __init__(self, config: AgentEaseConfig) -> None:
        self.config = config

    def complete(self, prompt: str) -> str:
        import litellm

        response = litellm.completion(
            model=self.config.litellm_model,
            messages=[{"role": "user", "content": prompt}],
            api_key=self.config.api_key,
            temperature=0,
        )
        return str(response.choices[0].message.content)


class TriageAgent:
    def __init__(
        self,
        api_key: str | None = None,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        config: AgentEaseConfig | None = None,
        pii_scrubber: PiiScrubber | None = None,
        metrics: MetricsRecorder | None = None,
        llm_client: LlmClient | None = None,
    ) -> None:
        self.config = config or AgentEaseConfig(
            api_key=api_key,
            provider=provider,
            model=model,
        )
        self.pii_scrubber = pii_scrubber or PiiScrubber()
        self.metrics = metrics
        self.llm_client = llm_client or LiteLlmClient(self.config)

    def run(self, ticket_text: str) -> TriageResult:
        started = now_ms()
        scrub_result = self.pii_scrubber.scrub(ticket_text)

        try:
            raw_response = self.llm_client.complete(self._build_prompt(scrub_result))
            result = enforce_json_schema(raw_response, TriageResult)
            self._record(started, True, scrub_result)
            return result
        except Exception:
            self._record(started, False, scrub_result)
            raise

    def _build_prompt(self, scrub_result: ScrubResult) -> str:
        schema = json.dumps(TriageResult.model_json_schema(), indent=2)
        return (
            "You are a customer support triage agent.\n"
            "Classify the sanitized support ticket and return only valid JSON.\n"
            "Do not include markdown, commentary, or fields outside the schema.\n\n"
            f"JSON schema:\n{schema}\n\n"
            f"Sanitized ticket:\n{scrub_result.sanitized_text}"
        )

    def _record(self, started: float, success: bool, scrub_result: ScrubResult) -> None:
        if not self.metrics:
            return
        self.metrics.record(
            MetricEvent(
                name="triage.run",
                duration_ms=now_ms() - started,
                success=success,
                metadata={
                    "detected_pii": sorted(scrub_result.detected_types),
                    "input_chars": len(scrub_result.original_text),
                    "sanitized_chars": len(scrub_result.sanitized_text),
                },
            )
        )
