from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from agentease import AgentEase

DEFAULT_INPUT = Path(__file__).parent / "data" / "support_tickets.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Triage support tickets from a JSONL file.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="JSONL file with one support ticket per line.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use the configured live LLM provider instead of the offline demo client.",
    )
    args = parser.parse_args()

    if args.live:
        load_dotenv()
        client = AgentEase.from_env()
    else:
        client = AgentEase.offline()

    for output in triage_jsonl(args.input, client):
        print(json.dumps(output))


def triage_jsonl(path: Path, client: AgentEase) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue

        ticket = json.loads(line)
        ticket_id = ticket.get("id") or f"line-{line_number}"
        ticket_text = ticket["text"]
        run = client.triage.run_with_report(ticket_text)
        result = run.output

        outputs.append(
            {
                "id": ticket_id,
                "category": result.category,
                "priority": result.priority,
                "summary": result.summary,
                "suggested_reply": result.suggested_reply,
                "detected_pii": list(run.guardrails.detected_pii_types),
                "repair_attempts": run.guardrails.repair_attempts,
            }
        )

    return outputs


if __name__ == "__main__":
    main()
