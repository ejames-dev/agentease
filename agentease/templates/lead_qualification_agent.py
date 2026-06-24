from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agentease.templates.base import WorkflowAgent, WorkflowSpec

__all__ = ["LEAD_SPEC", "LeadQualificationAgent", "LeadQualificationResult"]


class LeadQualificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Literal["hot", "warm", "cold", "not_a_lead"]
    fit: Literal["enterprise", "mid_market", "smb", "unknown"]
    budget_signal: Literal["explicit", "implied", "none"]
    next_action: Literal["book_demo", "send_pricing", "nurture", "disqualify"]
    summary: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


LEAD_SPEC: WorkflowSpec[LeadQualificationResult] = WorkflowSpec(
    name="lead_qualification",
    schema=LeadQualificationResult,
    instruction=(
        "You are a B2B sales lead qualification agent.\n"
        "Score the sanitized inbound message for buying intent and fit."
    ),
    input_label="Sanitized inbound message",
)


class LeadQualificationAgent(WorkflowAgent[LeadQualificationResult]):
    """Sales lead qualification workflow (a thin specialization of WorkflowAgent)."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(LEAD_SPEC, **kwargs)  # type: ignore[arg-type]
