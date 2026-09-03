"""Host-app pattern for reporting AgentEase errors to Sentry.

AgentEase never calls sentry_sdk.init() itself (see agentease/telemetry/sentry.py) —
it only forwards exceptions to whatever client the host application has already
configured. This example shows the host side of that contract: install the
`sentry` extra (`pip install agentease[sentry]`), set SENTRY_DSN, and initialize
the SDK before touching AgentEase.
"""

import argparse
import os

from dotenv import load_dotenv

from agentease import AgentEase


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AgentEase Sentry integration demo.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use the configured live LLM provider instead of the offline demo client.",
    )
    args = parser.parse_args()

    load_dotenv()

    dsn = os.environ.get("SENTRY_DSN")
    if dsn:
        import sentry_sdk

        sentry_sdk.init(dsn=dsn, send_default_pii=True)

    client = AgentEase.from_env() if args.live else AgentEase.offline()

    run = client.lead_qualification.run_with_report(
        "A global company wants a demo and pricing for 1,000 seats. Reply to buyer@example.com."
    )
    print(run.output.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
