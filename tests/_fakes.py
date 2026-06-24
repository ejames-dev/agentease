"""Shared test doubles for the workflow agents."""

from __future__ import annotations

from agentease.guardrails import PiiScrubber
from agentease.telemetry import InMemoryMetrics
from agentease.templates.base import WorkflowAgent, WorkflowSpec

TRIAGE_JSON = """
{
  "category": "billing",
  "priority": "high",
  "summary": "Customer reports a duplicate charge.",
  "suggested_reply": "Thanks for reaching out. We are reviewing the charge."
}
"""


class FakeLlmClient:
    """Captures the last prompt and returns a canned response."""

    def __init__(self, response: str = TRIAGE_JSON) -> None:
        self.prompt = ""
        self._response = response

    def complete(self, prompt: str) -> str:
        self.prompt = prompt
        return self._response


class SequentialLlmClient:
    """Returns canned responses in order and records every prompt seen."""

    def __init__(self, responses: list[str]) -> None:
        self.prompts: list[str] = []
        self._responses = responses

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self._responses.pop(0)


def make_agent(spec: WorkflowSpec, llm: object) -> WorkflowAgent:
    """Build a WorkflowAgent wired with a real scrubber and in-memory metrics."""
    return WorkflowAgent(
        spec,
        pii_scrubber=PiiScrubber(),
        metrics=InMemoryMetrics(),
        llm_client=llm,
    )
