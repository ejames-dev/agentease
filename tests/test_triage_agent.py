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
