# AgentEase

AgentEase is a secure agent SDK for B2B teams that want to automate workflows with LLMs without exposing sensitive customer or company data.

The MVP is a Python SDK with a production-oriented support triage workflow:

- Local PII detection and masking before any LLM call
- Controlled prompt construction
- Strict Pydantic validation for structured outputs
- Safe local metrics for latency, success state, and scrubbed entity types
- A testable provider interface so development does not require live model calls

## MVP Workflow

The first template is `Support Triage Agent`. It accepts raw support-ticket text inside the client's environment, scrubs sensitive data locally, sends sanitized content to the configured LLM provider, and returns a typed result.

```python
from agentease import AgentEase

client = AgentEase(api_key="your-provider-api-key", provider="openai", model="gpt-4o-mini")

result = client.triage.run(
    "Customer jane@example.com says they were charged twice and wants a refund."
)

print(result.category)
print(result.priority)
print(result.suggested_reply)
```

Example output:

```json
{
  "category": "billing",
  "priority": "high",
  "summary": "Customer reports a duplicate charge.",
  "suggested_reply": "Thanks for reaching out. We are reviewing the charge."
}
```

## Install

```bash
uv sync
```

## Run Tests

```bash
uv run pytest
```

## Project Structure

```text
agentease/
  client.py
  guardrails/
    pii_scrubber.py
    json_enforcer.py
  templates/
    triage_agent.py
  telemetry/
    metrics.py
examples/
  support_triage.py
tests/
```

## Roadmap

- Python SDK MVP
- Support Triage template
- Local PII scrubbing
- Schema-validated outputs
- Local metrics
- Hosted control plane for safe telemetry and configuration
- Additional templates for lead qualification and internal document analysis
- Enterprise policy controls and audit logging
