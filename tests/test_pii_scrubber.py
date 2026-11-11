import pytest

from agentease.guardrails import PiiScrubber


def test_scrubber_redacts_common_pii() -> None:
    result = PiiScrubber().scrub(
        "Email jane@example.com or call 555-123-4567. Card 4242 4242 4242 4242. SSN 123-45-6789."
    )

    assert "jane@example.com" not in result.sanitized_text
    assert "555-123-4567" not in result.sanitized_text
    assert "4242 4242 4242 4242" not in result.sanitized_text
    assert "123-45-6789" not in result.sanitized_text
    assert result.detected_types == {"email", "phone", "credit_card", "ssn"}
    assert result.counts == {"email": 1, "phone": 1, "credit_card": 1, "ssn": 1}


def test_scrubber_avoids_invalid_credit_card_false_positive() -> None:
    result = PiiScrubber().scrub(
        "Order number 1234 5678 9012 3456 and tracking 12345678901234567890 shipped today."
    )

    assert "1234 5678 9012 3456" in result.sanitized_text
    assert "12345678901234567890" in result.sanitized_text
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


@pytest.mark.parametrize(
    ("raw_text", "expected_sanitized"),
    [
        ("Item 1 - 4242 4242 4242 4242", "Item 1 - [REDACTED_CREDIT_CARD]"),
        ("Step 1 4242 4242 4242 4242", "Step 1 [REDACTED_CREDIT_CARD]"),
        ("Step 8 4242 4242 4242 4242", "Step 8 [REDACTED_CREDIT_CARD]"),
        ("4242 4242 4242 4242 5", "[REDACTED_CREDIT_CARD] 5"),
        ("1 4242 4242 4242 4242 5", "1 [REDACTED_CREDIT_CARD] 5"),
        ("2026-07-09 4242 4242 4242 4242", "2026-07-09 [REDACTED_CREDIT_CARD]"),
        ("2026-07-16 4242 4242 4242 4242", "2026-07-16 [REDACTED_CREDIT_CARD]"),
    ],
)
def test_scrubber_redacts_credit_cards_adjacent_to_numbers_and_dates(
    raw_text: str,
    expected_sanitized: str,
) -> None:
    result = PiiScrubber().scrub(raw_text)

    assert result.sanitized_text == expected_sanitized
    assert result.detected_types == {"credit_card"}
    assert result.replacements["credit_card"] == ["4242 4242 4242 4242"]


def test_scrubber_redacts_adjacent_distinct_credit_cards() -> None:
    result = PiiScrubber().scrub("Cards: 4111111111119 4242 4242 4242 4242")

    assert result.sanitized_text == "Cards: [REDACTED_CREDIT_CARD] [REDACTED_CREDIT_CARD]"
    assert result.replacements["credit_card"] == ["4111111111119", "4242 4242 4242 4242"]


@pytest.mark.parametrize(
    "card_number",
    [
        "3600 555123 4567",
        "3782-1555-123-4568",
        "4242 4242 1555 123 4566",
    ],
)
def test_scrubber_prefers_full_credit_card_over_partial_phone_match(card_number: str) -> None:
    result = PiiScrubber().scrub(f"Card {card_number} was declined.")

    assert result.sanitized_text == "Card [REDACTED_CREDIT_CARD] was declined."
    assert result.detected_types == {"credit_card"}
    assert result.replacements == {"credit_card": [card_number]}


def test_scrubber_does_not_rematch_redaction_markers_with_custom_entities() -> None:
    scrubber = PiiScrubber(custom_entities={"code": ["RED", "CARD"]})

    result = scrubber.scrub("Card 4242 4242 4242 4242")

    assert result.sanitized_text == "[REDACTED_CODE] [REDACTED_CREDIT_CARD]"
    assert result.replacements == {
        "code": ["Card"],
        "credit_card": ["4242 4242 4242 4242"],
    }


def test_scrubber_prefers_longest_custom_entity_over_shorter_prefix() -> None:
    scrubber = PiiScrubber(custom_entities={"org": ["Acme", "Acme Secret Labs"]})

    result = scrubber.scrub("Contact Acme Secret Labs and Acme today.")

    assert result.sanitized_text == "Contact [REDACTED_ORG] and [REDACTED_ORG] today."
    assert result.replacements == {"org": ["Acme Secret Labs", "Acme"]}
