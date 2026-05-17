from agentease import AgentEase, OfflineTriageLlmClient
from agentease.guardrails import PiiScrubber


def test_offline_client_returns_valid_triage_json() -> None:
    scrubbed = PiiScrubber().scrub(
        "Customer jane@example.com says card 4242 4242 4242 4242 was charged twice."
    )

    response = OfflineTriageLlmClient().complete(scrubbed.sanitized_text)

    assert "billing" in response
    assert "high" in response
    assert "jane@example.com" not in response


def test_agentease_offline_runs_without_provider_key(monkeypatch) -> None:
    monkeypatch.delenv("AGENTEASE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = AgentEase.offline()
    result = client.triage.run(
        "Customer jane@example.com says card 4242 4242 4242 4242 was charged twice."
    )

    assert result.category == "billing"
    assert result.priority == "high"
    assert client.metrics.events[0].success is True
    assert client.metrics.events[0].metadata["detected_pii"] == ["credit_card", "email"]
