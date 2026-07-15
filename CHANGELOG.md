# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - Unreleased

### Added

- First three-template release: flagship support triage, lead qualification,
  and plain-text document classification.
- Generic `WorkflowAgent` and declarative `WorkflowSpec` in
  `agentease.templates.base`; every template uses the shared scrub, prompt,
  validate/repair, and local-metrics pipeline.
- Canonical client entry points `client.triage`, `client.lead_qualification`,
  and `client.document_classification`.
- Legacy `client.leads` and `client.docs` aliases retained for compatibility.
- Canonical `DocumentClassificationResult` result model, with
  `DocClassificationResult` retained as a compatibility alias.
- `run_with_report()` for callers that need a typed result plus a local run
  report (`WorkflowRun.output` and `WorkflowRun.guardrails`) without reading the
  metrics recorder directly.
- Per-workflow deterministic offline responders, so `AgentEase.offline()` serves
  all three workflows without an API key or network call.
- Runnable offline/live examples for lead qualification and document
  classification.
- A security policy and explicit documentation of the regex scrubber's coverage
  and limitations.
- Stable, privacy-safe SDK exceptions for configuration, input, provider, and
  exhausted output-validation failures.
- Trusted Publishing workflows for TestPyPI and PyPI/GitHub releases, including
  artifact checksums and build provenance.

### Changed

- `TriageAgent` is now a thin specialization of `WorkflowAgent`; the
  `client.triage` API and offline triage behavior remain supported.
- `LlmClient` and `LiteLlmClient` now live in `agentease.templates.base` and are
  re-exported from `agentease.templates.triage_agent` for compatibility.
- OpenAI is the release-certified live-provider path. Other LiteLLM providers
  remain available on a best-effort basis.
- Release documentation now distinguishes local-only metrics, provider repair
  calls, advisory workflow outputs, and deferred dashboard, RAG, Node.js, and
  Presidio work.
- Provider requests now use validated timeout and output-token limits, while
  custom telemetry recorders are isolated from workflow outcomes.
- CI now validates Python 3.11-3.13, builds both distribution formats, checks
  package metadata, and smoke-installs the built wheel.

### Security

- Raised the minimum LiteLLM and Click versions and refreshed transitive locks
  to patched aiohttp and idna releases, resolving the dependency advisories
  found during the public-repository security audit.
- Removed the third-party PR Agent workflow because its pinned action revision
  still launched a mutable container image while receiving repository and
  provider credentials.

## [0.1.1] - 2026-06-22

### Fixed

- Constrained `requires-python` to `>=3.11,<3.14` to match the supported range of
  the `litellm` dependency. Previously an open-ended `>=3.11` advertised support
  for Python 3.14, where `pip install agentease` failed to resolve `litellm` with
  a confusing transitive error. Installs on Python 3.14+ now fail fast with a
  clear message that the package requires an older Python.

### Changed

- Added Python 3.13 to the CI test matrix.

## [0.1.0] - 2026-06-22

First MVP release: a Python SDK with one focused workflow, support-ticket triage,
that keeps raw ticket text and sensitive values inside the customer's environment.

### Added

- Support triage template for customer tickets.
- Local PII masking for email, phone, credit card (Luhn-validated), and SSN-like
  values, plus configurable extra patterns and custom entities.
- Strict Pydantic validation of LLM responses via `TriageResult`.
- JSON repair retry when a model returns malformed output.
- LiteLLM-backed provider calls.
- Environment-based provider configuration (`AgentEase.from_env`).
- Offline demo mode with no API key required (`AgentEase.offline`).
- In-memory metrics for duration, success state, and detected PII types.
- Support triage and JSONL batch triage examples.
- Unit tests and GitHub Actions CI (format, lint, tests on Python 3.11 and 3.12).

[0.2.0]: https://github.com/ejames-dev/agentease/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/ejames-dev/agentease/releases/tag/v0.1.1
[0.1.0]: https://github.com/ejames-dev/agentease/releases/tag/v0.1.0
