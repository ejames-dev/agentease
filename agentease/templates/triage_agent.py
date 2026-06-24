from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Re-exported here so existing imports keep working
# (`from agentease.templates.triage_agent import LlmClient, LiteLlmClient`).
from agentease.templates.base import LiteLlmClient, LlmClient, WorkflowAgent, WorkflowSpec

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
