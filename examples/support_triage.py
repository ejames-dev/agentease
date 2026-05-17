import argparse

from dotenv import load_dotenv

from agentease import AgentEase


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AgentEase support triage demo.")
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

    result = client.triage.run(
        "Customer jane@example.com says card 4242 4242 4242 4242 was charged twice."
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
