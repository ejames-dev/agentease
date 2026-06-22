# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.1]: https://github.com/ejames-dev/agentease/releases/tag/v0.1.1
[0.1.0]: https://github.com/ejames-dev/agentease/releases/tag/v0.1.0
