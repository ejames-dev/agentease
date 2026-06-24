from json import JSONDecodeError

import pytest
from _fakes import FakeLlmClient, SequentialLlmClient, make_agent
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from agentease.templates.base import WorkflowSpec


class _DemoResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)


DEMO_SPEC: WorkflowSpec[_DemoResult] = WorkflowSpec(
    name="demo",
    schema=_DemoResult,
    instruction="Classify the sanitized input.",
    input_label="Sanitized input",
)

VALID = '{"label": "ok"}'


def test_base_agent_scrubs_before_llm_and_records_namespaced_metric() -> None:
    llm = FakeLlmClient(response=VALID)
    agent = make_agent(DEMO_SPEC, llm)

    result = agent.run("Reach me at jane@example.com please.")

    assert result.label == "ok"
    assert "jane@example.com" not in llm.prompt
    event = agent.metrics.events[0]
    assert event.name == "demo.run"
    assert event.success is True
    assert event.metadata["detected_pii"] == ["email"]
    assert set(event.metadata) == {
        "detected_pii",
        "input_chars",
        "repair_attempts",
        "sanitized_chars",
    }


def test_base_agent_repairs_invalid_response() -> None:
    llm = SequentialLlmClient(responses=["not json at all", VALID])
    agent = make_agent(DEMO_SPEC, llm)

    result = agent.run("Contact jane@example.com")

    assert result.label == "ok"
    assert len(llm.prompts) == 2
    assert "previous response did not match" in llm.prompts[1]
    assert "jane@example.com" not in llm.prompts[1]
    assert agent.metrics.events[0].metadata["repair_attempts"] == 1


def test_base_agent_raises_after_exhausting_repairs() -> None:
    llm = SequentialLlmClient(responses=["nope", "still nope"])
    agent = make_agent(DEMO_SPEC, llm)

    with pytest.raises((JSONDecodeError, ValidationError)):
        agent.run("Contact jane@example.com")

    assert len(llm.prompts) == 2
    assert agent.metrics.events[0].success is False
    assert agent.metrics.events[0].metadata["repair_attempts"] == 1
