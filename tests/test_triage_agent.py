import pytest

from agentease.guardrails import PiiScrubber
from agentease.telemetry import InMemoryMetrics
from agentease.templates import TriageAgent


class FakeLlmClient:
    def __init__(self) -> None:
        self.prompt = ""

    def complete(self, prompt: str) -> str:
        self.prompt = prompt
        return """
        {
          "category": "billing",
          "priority": "high",
          "summary": "Customer reports a duplicate charge.",
          "suggested_reply": "Thanks for reaching out. We are reviewing the charge."
        }
        """


class SequentialLlmClient:
    def __init__(self, responses: list[str]) -> None:
        self.prompts: list[str] = []
        self._responses = responses

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._responses.pop(0)


def test_triage_agent_scrubs_before_llm_and_returns_typed_result() -> None:
    llm = FakeLlmClient()
    metrics = InMemoryMetrics()
    agent = TriageAgent(
        pii_scrubber=PiiScrubber(),
        metrics=metrics,
        llm_client=llm,
    )

    result = agent.run("Jane at jane@example.com says card 4242 4242 4242 4242 was charged twice.")

    assert result.category == "billing"
    assert "jane@example.com" not in llm.prompt
    assert "4242 4242 4242 4242" not in llm.prompt
    assert metrics.events[0].success is True
    assert metrics.events[0].metadata["detected_pii"] == ["credit_card", "email"]
    assert metrics.events[0].metadata["repair_attempts"] == 0


def test_triage_agent_repairs_invalid_json_response() -> None:
    llm = SequentialLlmClient(
        responses=[
            "Category: billing, Priority: high",
            """
            {
              "category": "billing",
              "priority": "high",
              "summary": "Customer reports a duplicate charge.",
              "suggested_reply": "Thanks for reaching out. We are reviewing the charge."
            }
            """,
        ]
    )
    metrics = InMemoryMetrics()
    agent = TriageAgent(
        pii_scrubber=PiiScrubber(),
        metrics=metrics,
        llm_client=llm,
        max_repair_attempts=1,
    )

    result = agent.run("Jane at jane@example.com was charged twice.")

    assert result.category == "billing"
    assert len(llm.prompts) == 2
    assert "previous response did not match" in llm.prompts[1]
    assert "jane@example.com" not in llm.prompts[1]
    assert metrics.events[0].success is True
    assert metrics.events[0].metadata["repair_attempts"] == 1


def test_triage_agent_records_failed_repair_attempts() -> None:
    llm = SequentialLlmClient(
        responses=[
            "Category: billing, Priority: high",
            "Still not JSON",
        ]
    )
    metrics = InMemoryMetrics()
    agent = TriageAgent(
        pii_scrubber=PiiScrubber(),
        metrics=metrics,
        llm_client=llm,
        max_repair_attempts=1,
    )

    with pytest.raises(Exception):
        agent.run("Jane at jane@example.com was charged twice.")

    assert len(llm.prompts) == 2
    assert metrics.events[0].success is False
    assert metrics.events[0].metadata["repair_attempts"] == 1
