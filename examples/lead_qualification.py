import argparse
import json
from dataclasses import asdict

from dotenv import load_dotenv

from agentease import AgentEase


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AgentEase lead qualification demo.")
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

    run = client.lead_qualification.run_with_report(
        "A global company wants a demo and pricing for 1,000 seats. Reply to buyer@example.com."
    )

    print(run.output.model_dump_json(indent=2))
    print(json.dumps({"guardrails": asdict(run.guardrails)}, indent=2))


if __name__ == "__main__":
    main()
