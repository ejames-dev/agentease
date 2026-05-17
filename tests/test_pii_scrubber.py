from agentease.guardrails import PiiScrubber


def test_scrubber_redacts_common_pii() -> None:
    result = PiiScrubber().scrub(
        "Email jane@example.com or call 555-123-4567. "
        "Card 4242 4242 4242 4242. SSN 123-45-6789."
    )

    assert "jane@example.com" not in result.sanitized_text
    assert "555-123-4567" not in result.sanitized_text
    assert "4242 4242 4242 4242" not in result.sanitized_text
    assert "123-45-6789" not in result.sanitized_text
    assert result.detected_types == {"email", "phone", "credit_card", "ssn"}
    assert result.counts == {"email": 1, "phone": 1, "credit_card": 1, "ssn": 1}


def test_scrubber_avoids_invalid_credit_card_false_positive() -> None:
    result = PiiScrubber().scrub("Order number 1234 5678 9012 3456 shipped today.")

    assert "1234 5678 9012 3456" in result.sanitized_text
    assert "credit_card" not in result.detected_types


def test_scrubber_supports_custom_regex_patterns() -> None:
    result = PiiScrubber(extra_patterns={"account_id": r"\bacct_[A-Za-z0-9]+\b"}).scrub(
        "Customer account acct_ABC123 needs review."
    )

    assert "acct_ABC123" not in result.sanitized_text
    assert "[REDACTED_ACCOUNT_ID]" in result.sanitized_text
    assert result.replacements["account_id"] == ["acct_ABC123"]


def test_scrubber_supports_custom_literal_entities() -> None:
    result = PiiScrubber(
        custom_entities={"project": ["Project Atlas"]},
        redaction_format="<{kind}>",
    ).scrub("Escalate Project Atlas before launch.")

    assert result.sanitized_text == "Escalate <PROJECT> before launch."
    assert result.replacements["project"] == ["Project Atlas"]
