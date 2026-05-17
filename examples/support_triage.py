from dotenv import load_dotenv

from agentease import AgentEase


def main() -> None:
    load_dotenv()

    client = AgentEase.from_env()
    result = client.triage.run(
        "Customer jane@example.com says card 4242 4242 4242 4242 was charged twice."
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
