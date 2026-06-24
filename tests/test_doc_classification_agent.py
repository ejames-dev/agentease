import json

from _fakes import FakeLlmClient

from agentease.guardrails import PiiScrubber
from agentease.telemetry import InMemoryMetrics
from agentease.templates import DocClassificationAgent, DocClassificationResult

VALID = json.dumps(
    {
        "doc_type": "contract",
        "sensitivity": "confidential",
        "contains_pii": True,
        "summary": "Master services agreement between two parties.",
        "recommended_handling": "Store in a restricted location.",
    }
)


def test_doc_agent_scrubs_pii_and_returns_typed_result() -> None:
    llm = FakeLlmClient(response=VALID)
    metrics = InMemoryMetrics()
    agent = DocClassificationAgent(
        pii_scrubber=PiiScrubber(),
        metrics=metrics,
        llm_client=llm,
    )

    result = agent.run("MSA signed by jane@example.com on behalf of Acme, net-30 terms.")

    assert isinstance(result, DocClassificationResult)
    assert result.doc_type == "contract"
    assert "jane@example.com" not in llm.prompt
    assert metrics.events[0].name == "doc_classification.run"
    assert metrics.events[0].success is True
