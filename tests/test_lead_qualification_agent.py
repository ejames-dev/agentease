import json

from _fakes import FakeLlmClient

from agentease.guardrails import PiiScrubber
from agentease.telemetry import InMemoryMetrics
from agentease.templates import LeadQualificationAgent, LeadQualificationResult

VALID = json.dumps(
    {
        "intent": "hot",
        "fit": "enterprise",
        "budget_signal": "explicit",
        "next_action": "book_demo",
        "summary": "Enterprise lead asking for a demo.",
        "rationale": "Explicit demo request with enterprise scale.",
    }
)


def test_lead_agent_scrubs_pii_and_returns_typed_result() -> None:
    llm = FakeLlmClient(response=VALID)
    metrics = InMemoryMetrics()
    agent = LeadQualificationAgent(
        pii_scrubber=PiiScrubber(),
        metrics=metrics,
        llm_client=llm,
    )

    result = agent.run("Hi, I'm at cto@bigcorp.com — Acme Corp wants a demo for 1000 seats.")

    assert isinstance(result, LeadQualificationResult)
    assert result.intent == "hot"
    assert "cto@bigcorp.com" not in llm.prompt
    assert metrics.events[0].name == "lead_qualification.run"
    assert metrics.events[0].success is True
