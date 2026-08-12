# AgentEase

AgentEase is a Python SDK for structured LLM workflows that scrub a defined set
of sensitive values locally before calling a model, then validate the response
against a strict Pydantic schema.

Version 0.2.0 is the first three-template release:

- `client.triage`: support-ticket triage (the flagship workflow)
- `client.lead_qualification`: B2B lead qualification
- `client.document_classification`: internal document classification

Every template uses the same pipeline:

```text
raw text -> local regex scrubber -> provider -> schema validation/repair -> typed result
```

## What Works Today

- Three typed, schema-constrained workflow templates
- Local masking for the regex patterns documented below
- One JSON/schema repair attempt by default
- OpenAI live-provider path certified for this release
- Other providers available on a best-effort basis through LiteLLM
- Deterministic offline demos with no API key or network call
- In-memory, local-only run metrics and reports
- Python 3.11, 3.12, and 3.13 support

AgentEase outputs are advisory. They do not replace human review, access
controls, compliance checks, sales policy, or customer-support policy.

## Quick Start

Install the published package:

```bash
pip install agentease==0.2.0
# or: uv add agentease==0.2.0
```

For repository development, clone the project and install its development dependencies:

```bash
uv sync --dev
```

Run the flagship support-triage demo without an API key:

```bash
uv run python examples/support_triage.py
```

Run the other templates offline:

```bash
uv run python examples/lead_qualification.py
uv run python examples/document_classification.py
```

The offline responders are deterministic keyword-based fixtures for evaluation,
documentation, and integration development. They are not local language models
and should not be used to measure live-provider quality.

To use a live OpenAI model, copy the environment template and add your key:

```bash
cp .env.example .env
```

```dotenv
AGENTEASE_PROVIDER=openai
AGENTEASE_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_api_key_here
```

Then add `--live` to any example:

```bash
uv run python examples/support_triage.py --live
uv run python examples/lead_qualification.py --live
uv run python examples/document_classification.py --live
```

Live runs send the sanitized prompt to the configured provider and can incur
provider charges.

## SDK Usage

```python
from agentease import AgentEase

client = AgentEase.offline()

triage = client.triage.run(
    "Customer jane@example.com says card 4242 4242 4242 4242 was charged twice."
)
lead = client.lead_qualification.run(
    "A 1,000-person company wants a demo and pricing for 250 seats."
)
document = client.document_classification.run(
    "CONFIDENTIAL master services agreement. Contact: jane@example.com."
)

print(triage.model_dump_json(indent=2))
print(lead.model_dump_json(indent=2))
print(document.model_dump_json(indent=2))
```

Use `AgentEase.from_env()` instead of `AgentEase.offline()` for a configured
live provider.

### Run reports and local metrics

`run()` returns only the typed workflow result. Use `run_with_report()` when the
caller also needs the local execution report:

```python
run = client.triage.run_with_report("Customer says they were charged twice.")

print(run.output.model_dump_json(indent=2))
print(run.guardrails.detected_pii_types)
print(run.guardrails.repair_attempts)
```

`run_with_report()` returns a `WorkflowRun` with `output` and `guardrails`.
The guardrail report contains `detected_pii_types`, `input_chars`,
`sanitized_chars`, and `repair_attempts`; it does not include the original input
or captured PII values.
The default recorder keeps metric events only in the current process. AgentEase
0.2.0 has no hosted telemetry path and does not send metrics to AgentEase
servers.

## Template Contracts

### Support triage

The flagship `client.triage` workflow returns:

- `category`: `billing`, `technical`, `account`, `sales`, or `other`
- `priority`: `low`, `medium`, `high`, or `urgent`
- `summary`: a non-empty summary
- `suggested_reply`: a non-empty draft reply

The suggested reply is a draft. Review it before sending it to a customer.

### Lead qualification

`client.lead_qualification` uses a deliberately small, opinionated B2B sales
rubric:

- `intent`: `hot`, `warm`, `cold`, or `not_a_lead`
- `fit`: `enterprise`, `mid_market`, `smb`, or `unknown`
- `budget_signal`: `explicit`, `implied`, or `none`
- `next_action`: `book_demo`, `send_pricing`, `nurture`, or `disqualify`
- `summary` and `rationale`: non-empty explanatory text

This is a starting rubric, not an objective score or a substitute for your
qualification policy. The live model infers these labels from the sanitized
message. The offline responder uses simple keywords, so its labels are useful
for repeatable integration testing only.

### Document classification

`client.document_classification` returns:

- `doc_type`: `contract`, `invoice`, `policy`, `report`, `correspondence`, or `other`
- `sensitivity`: `public`, `internal`, `confidential`, or `restricted`
- `summary` and `recommended_handling`: non-empty advisory text

The 0.2.0 input is plain text only. AgentEase does not parse PDF, DOCX, images,
email containers, or scanned documents, and it does not perform OCR, retrieval,
or chunking. Extract trusted plain text before calling this workflow. The
classification and recommended handling are advisory, not a DLP control or a
legal/compliance determination. Use `run_with_report().guardrails` when the
caller needs to know which covered PII types the scrubber detected.

## PII Scrubber: Exact Built-in Coverage

The built-in scrubber is local and regex-based. Matching is case-insensitive by
default and covers only these forms:

| Type | Covered form | Important limitations |
| --- | --- | --- |
| Email | ASCII-style local part, `@`, domain, and alphabetic TLD of at least two characters | Not a full RFC email parser; internationalized addresses and unusual valid forms can be missed |
| Phone | 10-digit North American numbers with optional `+1`/`1`, parentheses, spaces, dots, or hyphens | Does not cover general international numbers, extensions, short codes, or words such as `555-FLOWERS` |
| Credit card | 13-19 digits separated by optional spaces or hyphens | Must pass a Luhn check; other payment/account identifiers are not covered |
| SSN-like value | Exactly `NNN-NN-NNNN` | Format match only; unhyphenated values are missed and issuance validity is not checked |

These are the built-in expressions:

```text
email       \b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b
phone       (?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)
credit_card (?<!\d)(?:\d[ -]*?){13,19}(?!\d)
ssn         \b\d{3}-\d{2}-\d{4}\b
```

Credit-card regex matches are redacted only when the digits also pass the Luhn
check.

It does not detect names, street addresses, dates of birth, account names,
organizations, IP addresses, secrets, medical identifiers, or every possible
variant of the four built-in types. Regex detection can produce both false
negatives and false positives. Do not claim comprehensive anonymization from
the built-in scrubber.

You can add application-specific regexes and literal terms:

```python
from agentease import AgentEase
from agentease.guardrails import PiiScrubber

scrubber = PiiScrubber(
    extra_patterns={"account_id": r"\bacct_[A-Za-z0-9]+\b"},
    custom_entities={"internal_project": ["Project Atlas"]},
)
client = AgentEase.offline(pii_scrubber=scrubber)
```

Custom regexes and literal lists are still pattern matching. Test them against
your own data and threat model. Literal matching is case-insensitive by default
and is not automatically limited to whole words.

## Validation and Repair Calls

The provider is instructed to return only JSON matching the workflow's schema.
AgentEase validates that response locally. If JSON parsing or schema validation
fails, the default behavior makes one additional provider call containing:

- the required JSON schema
- the invalid provider response
- the same sanitized input context

Raw input is not added back to the repair prompt. Each repair is a real provider
call with its own latency, cost, and provider-side data handling. If all repair
attempts fail, AgentEase records a failed local metric and raises the stable,
data-free `OutputValidationError` exception.

Configure the maximum at client construction:

```python
client = AgentEase(max_repair_attempts=0)  # disable repair calls
```

## Provider Support

OpenAI is the release-certified live-provider path for 0.2.0. LiteLLM provides
the adapter used by other providers, but those combinations are best effort and
are not in the release acceptance matrix. Model behavior and credentials differ
by provider; validate your exact provider/model combination before production
use.

AgentEase reads:

```dotenv
AGENTEASE_PROVIDER=openai
AGENTEASE_MODEL=gpt-4o-mini
AGENTEASE_API_KEY=
AGENTEASE_TIMEOUT=30
AGENTEASE_MAX_TOKENS=800
```

If `AGENTEASE_API_KEY` is empty, the SDK checks the provider-specific variable,
such as `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

## Batch Triage Integration

The repository includes a JSONL integration for support tickets exported from a
helpdesk, CRM, or internal queue:

```bash
uv run python examples/batch_triage_jsonl.py
uv run python examples/batch_triage_jsonl.py --live
```

Each input line must contain `text`; `id` is optional:

```json
{"id":"ticket-1001","text":"Customer jane@example.com says card 4242 4242 4242 4242 was charged twice."}
```

## Security Model

AgentEase wraps each provider call with:

1. Local preprocessing: covered values are replaced before prompt construction.
2. Provider execution: the sanitized prompt is sent to the configured provider.
3. Local postprocessing: output is parsed, optionally repaired, and schema-validated.

This narrows exposure; it does not make arbitrary text safe to share. Unmatched
sensitive data remains in the sanitized prompt, and provider policies still
apply. Review [SECURITY.md](SECURITY.md) before production use.

## Deferred Beyond 0.2.0

The following are roadmap items, not current features:

- hosted dashboard, remote telemetry, audit logs, and policy management
- RAG, document parsing, OCR, and chunking
- Node.js SDK
- Presidio-backed or ML-based entity detection
- streaming and richer provider controls
- enterprise private deployments

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete contribution and
security-reporting workflow.

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

Release notes are in [CHANGELOG.md](CHANGELOG.md). AgentEase is licensed under
the [MIT License](LICENSE).
