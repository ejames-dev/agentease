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


def test_agentease_offline_runs_lead_and_doc_workflows(monkeypatch) -> None:
    monkeypatch.delenv("AGENTEASE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = AgentEase.offline()

    lead = client.leads.run("Acme Corp wants a demo for 1000 seats, budget approved.")
    doc = client.docs.run("Master services agreement with jane@example.com, net-30 terms.")

    assert lead.next_action == "book_demo"
    assert doc.doc_type == "contract"
    assert doc.contains_pii is True
    names = {event.name for event in client.metrics.events}
    assert {"lead_qualification.run", "doc_classification.run"} <= names


def test_agentease_offline_accepts_custom_scrubber() -> None:
    client = AgentEase.offline(
        pii_scrubber=PiiScrubber(custom_entities={"project": ["Project Atlas"]})
    )

    result = client.triage.pii_scrubber.scrub("Project Atlas needs review.")

    assert result.sanitized_text == "[REDACTED_PROJECT] needs review."
