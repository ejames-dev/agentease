# Contributing to AgentEase

Thanks for helping improve AgentEase. Bug reports, focused feature proposals,
documentation fixes, and pull requests are welcome.

## Before You Start

- Search the existing issues and pull requests before opening a new one.
- Keep changes focused. Discuss broad API changes in an issue before investing
  in an implementation.
- Do not open a public issue or pull request for a suspected vulnerability.
  Follow [SECURITY.md](SECURITY.md) instead.
- Never include real customer data, credentials, API keys, or other secrets in
  an issue, test, example, log, or pull request.

## Development Setup

AgentEase supports Python 3.11 through 3.13 and uses
[uv](https://docs.astral.sh/uv/) for dependency and environment management.

```bash
git clone https://github.com/ejames-dev/agentease.git
cd agentease
uv sync --locked --dev
```

Create a branch for your change. Branch names such as `fix/short-description`
or `feature/short-description` are easy to understand.

## Making Changes

- Add or update tests for behavior changes.
- Keep public API changes typed and documented.
- Use synthetic data in tests and examples.
- Update `README.md` when user-facing behavior changes.
- Update `CHANGELOG.md` for changes that affect a release.
- If dependencies change, commit the corresponding `uv.lock` update.

Run the same core checks used by continuous integration:

```bash
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen pytest
```

If formatting fails, apply it with `uv run ruff format .`, review the diff, and
run the checks again. Changes to workflow behavior should also exercise the
relevant offline examples:

```bash
uv run --frozen python examples/support_triage.py
uv run --frozen python examples/lead_qualification.py
uv run --frozen python examples/document_classification.py
uv run --frozen python examples/batch_triage_jsonl.py
```

Offline examples are deterministic fixtures and do not need an API key. Do not
use a live provider merely to validate a contribution unless the change
specifically requires it and you understand the possible cost and data flow.

## Pull Requests

Open your pull request against `main` and complete the template. A pull request
should explain the problem, the chosen approach, and how the change was tested.
Small, reviewable pull requests are preferred.

All required checks must pass and review conversations must be resolved before
the maintainer merges a pull request. The maintainer may ask for changes or
close proposals that do not fit the project scope. Contributions are provided
under the repository's [MIT License](LICENSE).
