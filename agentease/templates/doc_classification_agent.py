from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agentease.templates.base import WorkflowAgent, WorkflowSpec

__all__ = [
    "DOC_SPEC",
    "DocClassificationAgent",
    "DocClassificationResult",
    "DocumentClassificationResult",
]


class DocumentClassificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_type: Literal["contract", "invoice", "policy", "report", "correspondence", "other"]
    sensitivity: Literal["public", "internal", "confidential", "restricted"]
    summary: str = Field(min_length=1)
    recommended_handling: str = Field(min_length=1)


# Compatibility alias retained through the 0.3 release line.
DocClassificationResult = DocumentClassificationResult


DOC_SPEC: WorkflowSpec[DocumentClassificationResult] = WorkflowSpec(
    name="doc_classification",
    schema=DocumentClassificationResult,
    instruction=(
        "You are an internal document governance agent.\n"
        "Classify the sanitized document and assess its data sensitivity."
    ),
    input_label="Sanitized document",
)


class DocClassificationAgent(WorkflowAgent[DocumentClassificationResult]):
    """Internal document classification workflow (a thin specialization of WorkflowAgent)."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(DOC_SPEC, **kwargs)  # type: ignore[arg-type]
