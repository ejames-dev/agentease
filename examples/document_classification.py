import argparse
import json
from dataclasses import asdict

from dotenv import load_dotenv

from agentease import AgentEase


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the AgentEase plain-text document classification demo."
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

    # Version 0.2.0 classifies caller-supplied plain text. It does not parse files or run OCR.
    run = client.document_classification.run_with_report(
        "CONFIDENTIAL master services agreement with net-30 payment terms. "
        "The customer contact is jane@example.com."
    )

    print(run.output.model_dump_json(indent=2))
    print(json.dumps({"guardrails": asdict(run.guardrails)}, indent=2))


if __name__ == "__main__":
    main()
