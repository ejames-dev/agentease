from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ScrubResult:
    original_text: str
    sanitized_text: str
    replacements: dict[str, list[str]] = field(default_factory=dict)

    @property
    def detected_types(self) -> set[str]:
        return {kind for kind, values in self.replacements.items() if values}


class PiiScrubber:
    """Local regex-based PII scrubber for the MVP.

    This keeps the first version dependency-light while leaving room to swap in
    Microsoft Presidio behind the same interface later.
    """

    DEFAULT_PATTERNS: dict[str, str] = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "phone": r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)",
        "credit_card": r"(?<!\d)(?:\d[ -]*?){13,16}(?!\d)",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    }

    def __init__(self, extra_patterns: dict[str, str] | None = None) -> None:
        patterns = dict(self.DEFAULT_PATTERNS)
        if extra_patterns:
            patterns.update(extra_patterns)
        self._patterns = {
            kind: re.compile(pattern, re.IGNORECASE) for kind, pattern in patterns.items()
        }

    def scrub(self, text: str) -> ScrubResult:
        sanitized = text
        replacements: dict[str, list[str]] = {}

        for kind, pattern in self._patterns.items():
            seen: list[str] = []

            def replace(match: re.Match[str]) -> str:
                value = match.group(0)
                seen.append(value)
                return f"[REDACTED_{kind.upper()}]"

            sanitized = pattern.sub(replace, sanitized)
            if seen:
                replacements[kind] = seen

        return ScrubResult(
            original_text=text,
            sanitized_text=sanitized,
            replacements=replacements,
        )
