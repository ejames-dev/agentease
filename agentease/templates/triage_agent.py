from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Re-exported here so existing imports keep working
# (`from agentease.templates.triage_agent import LlmClient, LiteLlmClient`).
from agentease.exceptions import InputValidationError
from agentease.templates.base import (
    LiteLlmClient,
    LlmClient,
    WorkflowAgent,
    WorkflowRun,
    WorkflowSpec,
)

__all__ = ["LiteLlmClient", "LlmClient", "TRIAGE_SPEC", "TriageAgent", "TriageResult"]


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Literal["billing", "technical", "account", "sales", "other"]
    priority: Literal["low", "medium", "high", "urgent"]
    summary: str = Field(min_length=1)
    suggested_reply: str = Field(min_length=1)


TRIAGE_SPEC: WorkflowSpec[TriageResult] = WorkflowSpec(
    name="triage",
    schema=TriageResult,
    instruction=(
        "You are a customer support triage agent.\nClassify the sanitized support ticket."
    ),
    input_label="Sanitized ticket",
    context_label="Sanitized ticket for context",
)


class TriageAgent(WorkflowAgent[TriageResult]):
    """Customer support triage workflow (a thin specialization of WorkflowAgent)."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(TRIAGE_SPEC, **kwargs)  # type: ignore[arg-type]

    def run(
        self,
        text: str | None = None,
        *,
        ticket_text: str | None = None,
    ) -> TriageResult:
        return super().run(self._resolve_ticket_text(text, ticket_text))

    def run_with_report(
        self,
        text: str | None = None,
        *,
        ticket_text: str | None = None,
    ) -> WorkflowRun[TriageResult]:
        return super().run_with_report(self._resolve_ticket_text(text, ticket_text))

    def _resolve_ticket_text(self, text: str | None, ticket_text: str | None) -> str:
        if text is not None and ticket_text is not None:
            raise InputValidationError("Pass either text or ticket_text, not both.")
        if ticket_text is not None:
            return ticket_text
        if text is not None:
            return text
        raise InputValidationError("Workflow input must be a non-blank string.")
