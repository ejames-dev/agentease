# AgentEase

AgentEase is a secure agent SDK for B2B teams that want to automate LLM workflows without exposing sensitive customer or company data.

The first MVP is a Python SDK with one focused workflow: support-ticket triage. Raw ticket text is handled inside the customer's environment, sensitive values are masked locally, the sanitized prompt is sent to the configured LLM provider, and the response is validated into a strict typed result.

## What Works Today

- Support triage template for customer tickets
- Local PII masking for email, phone, credit card, and SSN-like values
- Strict Pydantic validation for LLM responses
- JSON repair retry when a model returns malformed output
- LiteLLM-backed provider calls
- Environment-based provider configuration
- Offline demo mode with no API key required
- Local metrics for duration, success state, and detected PII types
- Unit tests and GitHub Actions CI

## Quick Start

Install dependencies:

```bash
uv sync --dev
```

Run the test suite:

```bash
uv run pytest
```

Run the offline demo without an API key:

```bash
uv run python examples/support_triage.py
```

Configure a provider:

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
AGENTEASE_PROVIDER=openai
AGENTEASE_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_api_key_here
```

Run the same demo against a live provider:

```bash
uv run python examples/support_triage.py --live
```

## SDK Usage

```python
from dotenv import load_dotenv

from agentease import AgentEase

load_dotenv()

client = AgentEase.from_env()

result = client.triage.run(
    "Customer jane@example.com says card 4242 4242 4242 4242 was charged twice."
)

print(result.model_dump_json(indent=2))
```

For local demos or docs, use the deterministic offline client:

```python
from agentease import AgentEase

client = AgentEase.offline()
result = client.triage.run("Customer says they were charged twice.")
```

By default, AgentEase makes one repair attempt if the model response is not valid JSON or does not match the schema. You can tune this from the top-level client:

```python
client = AgentEase.from_env()
client.triage.max_repair_attempts = 2
```

Example result:

```json
{
  "category": "billing",
  "priority": "high",
  "summary": "Customer reports a duplicate charge.",
  "suggested_reply": "Thanks for reaching out. We are reviewing the charge."
}
```

## Provider Configuration

AgentEase reads configuration from `AgentEase.from_env()`:

```bash
AGENTEASE_PROVIDER=openai
AGENTEASE_MODEL=gpt-4o-mini
AGENTEASE_API_KEY=
```

If `AGENTEASE_API_KEY` is empty, AgentEase falls back to the provider-specific key name, such as `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

You can also configure the SDK directly:

```python
from agentease import AgentEase

client = AgentEase(
    api_key="your-provider-api-key",
    provider="openai",
    model="gpt-4o-mini",
)
```

## Security Model

AgentEase uses a sandwich model around each LLM call:

1. Pre-execution guardrail: raw input is scrubbed locally before model calls.
2. LLM execution: only sanitized text is sent to the configured provider.
3. Post-execution guardrail: output is repaired if needed, then rejected unless it matches the schema.

The hosted control plane described in the product roadmap is not part of this MVP. The current SDK does not send telemetry to AgentEase servers.

## Project Structure

```text
agentease/
  client.py
  config.py
  offline.py
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
.github/workflows/
  ci.yml
```

## Roadmap

- Harden PII detection and add Presidio-backed detection
- Add streaming and richer provider controls
- Add Node SDK after the Python API stabilizes
- Add safe dashboard telemetry and policy configuration
- Add templates for lead qualification and internal document analysis
- Add enterprise audit logs, policy versioning, and private deployments

## License

MIT
