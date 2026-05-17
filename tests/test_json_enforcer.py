import pytest
from pydantic import ValidationError

from agentease.guardrails import enforce_json_schema
from agentease.templates import TriageResult


def test_enforces_valid_triage_schema() -> None:
    result = enforce_json_schema(
        {
            "category": "billing",
            "priority": "high",
            "summary": "Duplicate charge.",
            "suggested_reply": "We are reviewing the duplicate charge.",
        },
        TriageResult,
    )

    assert result.category == "billing"
    assert result.priority == "high"


def test_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        enforce_json_schema(
            {
                "category": "billing",
                "priority": "high",
                "summary": "Duplicate charge.",
                "suggested_reply": "We are reviewing it.",
                "unsafe": "extra",
            },
            TriageResult,
        )
