import sys
import time
from types import SimpleNamespace

import pytest
from _fakes import TRIAGE_JSON, FakeLlmClient

from agentease import AgentEase, ConfigurationError, ProviderError
from agentease.config import AgentEaseConfig
from agentease.templates.base import LiteLlmClient

LEAD_JSON = """
{
  "intent": "hot",
  "fit": "enterprise",
  "budget_signal": "explicit",
  "next_action": "book_demo",
  "summary": "Qualified lead.",
  "rationale": "Explicit enterprise request."
}
"""


def test_shared_llm_client_is_used_by_all_canonical_workflows() -> None:
    class RoutingLlm:
        def complete(self, prompt: str) -> str:
            if "lead qualification" in prompt:
                return LEAD_JSON
            if "document governance" in prompt:
                return (
                    '{"doc_type":"policy","sensitivity":"internal",'
                    '"summary":"Internal policy.",'
                    '"recommended_handling":"Use internal storage."}'
                )
            return TRIAGE_JSON

    client = AgentEase(llm_client=RoutingLlm())

    assert client.triage.run("Billing request").category == "billing"
    assert client.lead_qualification.run("Enterprise demo").intent == "hot"
    assert client.document_classification.run("Internal policy").doc_type == "policy"


def test_legacy_triage_override_takes_precedence_over_shared_client() -> None:
    shared = FakeLlmClient(response="not json")
    triage_override = FakeLlmClient(response=TRIAGE_JSON)
    client = AgentEase(llm_client=shared, triage_llm_client=triage_override)

    result = client.triage.run(ticket_text="Billing request")

    assert result.category == "billing"
    assert triage_override.prompt
    assert shared.prompt == ""


def test_litellm_receives_timeout_and_max_tokens(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def completion(**kwargs: object) -> object:
        captured.update(kwargs)
        message = SimpleNamespace(content=TRIAGE_JSON)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(completion=completion))
    client = LiteLlmClient(AgentEaseConfig(timeout=17, max_tokens=456))

    client.complete("prompt")

    assert captured["timeout"] == 17
    assert captured["max_tokens"] == 456


def test_provider_failure_uses_stable_data_free_exception_and_preserves_cause() -> None:
    secret = "private@example.com"

    class FailingLlm:
        def complete(self, prompt: str) -> str:
            raise TimeoutError(secret)

    client = AgentEase(llm_client=FailingLlm())

    with pytest.raises(ProviderError) as caught:
        client.triage.run("safe input")

    assert secret not in str(caught.value)
    assert isinstance(caught.value.__cause__, TimeoutError)


def test_null_provider_content_is_rejected() -> None:
    class NullLlm:
        def complete(self, prompt: str) -> str:
            return None  # type: ignore[return-value]

    with pytest.raises(ProviderError):
        AgentEase(llm_client=NullLlm()).triage.run("safe input")


@pytest.mark.parametrize("value", [-1, 1.5, True])
def test_invalid_repair_configuration_is_rejected(value: object) -> None:
    with pytest.raises(ConfigurationError):
        AgentEase(max_repair_attempts=value)  # type: ignore[arg-type]


def test_slow_failing_telemetry_does_not_block_or_break_workflow() -> None:
    class SlowFailingMetrics:
        def record(self, event: object) -> None:
            time.sleep(0.25)
            raise RuntimeError("telemetry unavailable")

    client = AgentEase(llm_client=FakeLlmClient(), metrics=SlowFailingMetrics())

    started = time.perf_counter()
    result = client.triage.run("Billing request")
    elapsed = time.perf_counter() - started

    assert result.category == "billing"
    assert elapsed < 0.2
