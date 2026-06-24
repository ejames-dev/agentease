import pytest

from agentease.guardrails import PiiScrubber, enforce_json_schema
from agentease.offline_registry import offline_client_for
from agentease.templates import (
    DocClassificationResult,
    LeadQualificationResult,
    TriageResult,
)

CASES = [
    ("triage", TriageResult, "Customer was charged twice and wants a refund."),
    ("lead_qualification", LeadQualificationResult, "Acme Corp wants a demo for 1000 seats."),
    ("doc_classification", DocClassificationResult, "Master services agreement, net-30 terms."),
]


@pytest.mark.parametrize(("name", "schema", "text"), CASES)
def test_offline_responder_returns_schema_valid_json(name, schema, text) -> None:
    scrubbed = PiiScrubber().scrub(f"{text} Contact jane@example.com.")

    response = offline_client_for(name).complete(scrubbed.sanitized_text)

    enforce_json_schema(response, schema)  # raises if invalid
    assert "jane@example.com" not in response


def test_offline_client_for_unknown_workflow_raises() -> None:
    with pytest.raises(KeyError):
        offline_client_for("does_not_exist")
