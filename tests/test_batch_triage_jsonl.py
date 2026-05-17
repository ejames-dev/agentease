import json

from agentease import AgentEase
from examples.batch_triage_jsonl import triage_jsonl


def test_batch_triage_jsonl_processes_ticket_file(tmp_path) -> None:
    input_path = tmp_path / "tickets.jsonl"
    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "ticket-1",
                        "text": (
                            "Customer jane@example.com says card "
                            "4242 4242 4242 4242 was charged twice."
                        ),
                    }
                ),
                json.dumps(
                    {
                        "id": "ticket-2",
                        "text": "A user cannot log in after resetting their password.",
                    }
                ),
            ]
        )
    )

    outputs = triage_jsonl(input_path, AgentEase.offline())

    assert len(outputs) == 2
    assert outputs[0]["id"] == "ticket-1"
    assert outputs[0]["category"] == "billing"
    assert outputs[0]["priority"] == "high"
    assert outputs[0]["detected_pii"] == ["credit_card", "email"]
    assert outputs[1]["category"] == "account"
