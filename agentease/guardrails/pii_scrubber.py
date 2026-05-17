from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field


Validator = Callable[[str], bool]


@dataclass(frozen=True, slots=True)
class ScrubResult:
    original_text: str
    sanitized_text: str
    replacements: dict[str, list[str]] = field(default_factory=dict)

    @property
    def detected_types(self) -> set[str]:
        return {kind for kind, values in self.replacements.items() if values}

    @property
    def counts(self) -> dict[str, int]:
        return {kind: len(values) for kind, values in self.replacements.items()}


@dataclass(frozen=True, slots=True)
class EntityPattern:
    kind: str
    pattern: re.Pattern[str]
    validator: Validator | None = None


class PiiScrubber:
    """Local regex-based PII scrubber for the MVP.

    This keeps the first version dependency-light while leaving room to swap in
    Microsoft Presidio behind the same interface later.
    """

    DEFAULT_PATTERNS: dict[str, str] = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "phone": r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)",
        "credit_card": r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    }

    def __init__(
        self,
        extra_patterns: dict[str, str] | None = None,
        custom_entities: dict[str, list[str]] | None = None,
        redaction_format: str = "[REDACTED_{kind}]",
        case_sensitive: bool = False,
    ) -> None:
        self.redaction_format = redaction_format
        flags = 0 if case_sensitive else re.IGNORECASE
        patterns: list[EntityPattern] = []

        default_patterns = dict(self.DEFAULT_PATTERNS)
        if extra_patterns:
            default_patterns.update(extra_patterns)

        for kind, pattern in default_patterns.items():
            patterns.append(
                EntityPattern(
                    kind=kind,
                    pattern=re.compile(pattern, flags),
                    validator=_is_luhn_valid if kind == "credit_card" else None,
                )
            )

        for kind, values in (custom_entities or {}).items():
            escaped_values = [re.escape(value) for value in values if value]
            if not escaped_values:
                continue
            patterns.append(
                EntityPattern(
                    kind=kind,
                    pattern=re.compile("|".join(escaped_values), flags),
                )
            )

        self._patterns = patterns

    def scrub(self, text: str) -> ScrubResult:
        sanitized = text
        replacements: dict[str, list[str]] = {}

        for entity_pattern in self._patterns:
            seen: list[str] = []

            def replace(match: re.Match[str]) -> str:
                value = match.group(0)
                if entity_pattern.validator and not entity_pattern.validator(value):
                    return value
                seen.append(value)
                return self.redaction_format.format(kind=entity_pattern.kind.upper())

            sanitized = entity_pattern.pattern.sub(replace, sanitized)
            if seen:
                replacements.setdefault(entity_pattern.kind, []).extend(seen)

        return ScrubResult(
            original_text=text,
            sanitized_text=sanitized,
            replacements=replacements,
        )


def _is_luhn_valid(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False

    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0
