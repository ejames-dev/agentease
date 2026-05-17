from agentease.guardrails import PiiScrubber


def test_scrubber_redacts_common_pii() -> None:
    result = PiiScrubber().scrub(
        "Email jane@example.com or call 555-123-4567. Card 4242 4242 4242 4242."
    )

    assert "jane@example.com" not in result.sanitized_text
    assert "555-123-4567" not in result.sanitized_text
    assert "4242 4242 4242 4242" not in result.sanitized_text
    assert result.detected_types == {"email", "phone", "credit_card"}
