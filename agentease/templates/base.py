from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

from agentease.config import AgentEaseConfig
from agentease.guardrails.json_enforcer import enforce_json_schema
from agentease.guardrails.pii_scrubber import PiiScrubber, ScrubResult
from agentease.telemetry.metrics import MetricEvent, MetricsRecorder, now_ms

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LlmClient(Protocol):
    def complete(self, prompt: str) -> str: ...


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


@dataclass(frozen=True, slots=True)
class WorkflowSpec(Generic[SchemaT]):
    """Declarative description of a single workflow.

    The pipeline (scrub -> prompt -> complete -> validate+repair -> record) is
    identical across workflows; everything that differs is captured here so a new
    workflow is a schema plus a one-line instruction, not a new agent class.
    """

    name: str
    schema: type[SchemaT]
    instruction: str
    input_label: str = "Sanitized input"
    context_label: str | None = None

    @property
    def repair_context_label(self) -> str:
        return self.context_label or f"{self.input_label} for context"


class WorkflowAgent(Generic[SchemaT]):
    """Generic agent that runs one :class:`WorkflowSpec` through the guardrail pipeline."""

    def __init__(
        self,
        spec: WorkflowSpec[SchemaT],
        api_key: str | None = None,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        config: AgentEaseConfig | None = None,
        pii_scrubber: PiiScrubber | None = None,
        metrics: MetricsRecorder | None = None,
        llm_client: LlmClient | None = None,
        max_repair_attempts: int = 1,
    ) -> None:
        self.spec = spec
        self.config = config or AgentEaseConfig(
            api_key=api_key,
            provider=provider,
            model=model,
        )
        self.pii_scrubber = pii_scrubber or PiiScrubber()
        self.metrics = metrics
        self.llm_client = llm_client or LiteLlmClient(self.config)
        self.max_repair_attempts = max(0, max_repair_attempts)

    def run(self, text: str) -> SchemaT:
        started = now_ms()
        scrub_result = self.pii_scrubber.scrub(text)
        repair_attempts = 0

        try:
            prompt = self._build_prompt(scrub_result)
            raw_response = self.llm_client.complete(prompt)
            while True:
                try:
                    result = enforce_json_schema(raw_response, self.spec.schema)
                    break
                except Exception as error:
                    if repair_attempts >= self.max_repair_attempts:
                        raise
                    repair_attempts += 1
                    raw_response = self.llm_client.complete(
                        self._build_repair_prompt(
                            scrub_result=scrub_result,
                            invalid_response=raw_response,
                            validation_error=error,
                        )
                    )
            self._record(started, True, scrub_result, repair_attempts)
            return result
        except Exception:
            self._record(started, False, scrub_result, repair_attempts)
            raise

    def _build_prompt(self, scrub_result: ScrubResult) -> str:
        schema = json.dumps(self.spec.schema.model_json_schema(), indent=2)
        return (
            f"{self.spec.instruction}\n"
            "Return only valid JSON.\n"
            "Do not include markdown, commentary, or fields outside the schema.\n\n"
            f"JSON schema:\n{schema}\n\n"
            f"{self.spec.input_label}:\n{scrub_result.sanitized_text}"
        )

    def _build_repair_prompt(
        self,
        scrub_result: ScrubResult,
        invalid_response: str,
        validation_error: Exception,
    ) -> str:
        schema = json.dumps(self.spec.schema.model_json_schema(), indent=2)
        return (
            "Your previous response did not match the required JSON schema.\n"
            "Repair it and return only valid JSON. Do not include markdown, commentary, "
            "or fields outside the schema.\n\n"
            f"JSON schema:\n{schema}\n\n"
            f"Validation error:\n{validation_error}\n\n"
            f"Invalid response:\n{invalid_response}\n\n"
            f"{self.spec.repair_context_label}:\n{scrub_result.sanitized_text}"
        )

    def _record(
        self,
        started: float,
        success: bool,
        scrub_result: ScrubResult,
        repair_attempts: int,
    ) -> None:
        if not self.metrics:
            return
        self.metrics.record(
            MetricEvent(
                name=f"{self.spec.name}.run",
                duration_ms=now_ms() - started,
                success=success,
                metadata={
                    "detected_pii": sorted(scrub_result.detected_types),
                    "input_chars": len(scrub_result.original_text),
                    "repair_attempts": repair_attempts,
                    "sanitized_chars": len(scrub_result.sanitized_text),
                },
            )
        )
