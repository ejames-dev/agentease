from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "claude.yml"
SHA_PINNED_ACTION_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")


def test_claude_workflow_enforces_trusted_actor_and_least_privilege() -> None:
    workflow = yaml.safe_load(CLAUDE_WORKFLOW.read_text(encoding="utf-8"))

    # YAML 1.1 parses bare `on:` as boolean True unless quoted; support both keys.
    triggers = workflow.get("on") or workflow[True]
    assert set(triggers) == {
        "issue_comment",
        "pull_request_review_comment",
        "issues",
        "pull_request_review",
    }
    assert workflow.get("permissions") == {}

    job = workflow["jobs"]["claude"]
    assert isinstance(job.get("timeout-minutes"), int)
    assert 0 < job["timeout-minutes"] <= 60

    condition = job["if"]
    assert "!endsWith(github.actor, '[bot]')" in condition
    assert 'fromJSON(\'["OWNER", "MEMBER", "COLLABORATOR"]\')' in condition
    assert "github.event.comment.author_association" in condition
    assert "github.event.review.author_association" in condition
    assert "github.event.issue.author_association" in condition

    steps = job["steps"]
    for step in steps:
        if "uses" in step:
            assert SHA_PINNED_ACTION_RE.match(step["uses"]), f"Unpinned action: {step['uses']}"

    checkout_step = next(s for s in steps if s["uses"].startswith("actions/checkout@"))
    assert checkout_step["with"]["persist-credentials"] is False

    claude_step = next(s for s in steps if s["uses"].startswith("anthropics/claude-code-action@"))
    assert claude_step["with"]["exclude_comments_by_actor"] == "*[bot]"
