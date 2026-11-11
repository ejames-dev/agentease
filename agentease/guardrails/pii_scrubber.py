from __future__ import annotations

import re
from bisect import bisect_right
from collections.abc import Callable, Iterator
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


@dataclass(frozen=True, slots=True)
class _CandidateSpan:
    start: int
    end: int
    priority: int
    kind: str
    value: str


class PiiScrubber:
    """Local regex-based PII scrubber for the MVP.

    This keeps the first version dependency-light while leaving room to swap in
    Microsoft Presidio behind the same interface later.
    """

    DEFAULT_PATTERNS: dict[str, str] = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "phone": r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)",
        "credit_card": r"(?<!\d)(?:\d(?: ?\d){12,18}|\d(?:-?\d){12,18})(?!\d)",
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
            unique_values = list(dict.fromkeys(value for value in values if value))
            if not unique_values:
                continue
            sorted_values = sorted(unique_values, key=len, reverse=True)
            escaped_values = [re.escape(value) for value in sorted_values]
            patterns.append(
                EntityPattern(
                    kind=kind,
                    pattern=re.compile("|".join(escaped_values), flags),
                )
            )

        self._patterns = patterns

    def scrub(self, text: str) -> ScrubResult:
        candidates: list[_CandidateSpan] = []
        for priority, entity_pattern in enumerate(self._patterns):
            candidates.extend(_iter_candidates(entity_pattern, priority, text))

        selected = _resolve_non_overlapping(candidates)
        if not selected:
            return ScrubResult(
                original_text=text,
                sanitized_text=text,
                replacements={},
            )

        chunks: list[str] = []
        replacements: dict[str, list[str]] = {}
        cursor = 0
        for span in selected:
            chunks.append(text[cursor : span.start])
            chunks.append(self.redaction_format.format(kind=span.kind.upper()))
            replacements.setdefault(span.kind, []).append(span.value)
            cursor = span.end
        chunks.append(text[cursor:])

        return ScrubResult(
            original_text=text,
            sanitized_text="".join(chunks),
            replacements=replacements,
        )


def _iter_candidates(
    entity_pattern: EntityPattern,
    priority: int,
    text: str,
) -> Iterator[_CandidateSpan]:
    validator = entity_pattern.validator
    if validator is None:
        for match in entity_pattern.pattern.finditer(text):
            start, end = match.start(), match.end()
            if start < end:
                yield _CandidateSpan(start, end, priority, entity_pattern.kind, match.group(0))
        return

    length = len(text)
    pos = 0
    while pos < length:
        match = entity_pattern.pattern.search(text, pos)
        if match is None:
            break
        start, end = match.start(), match.end()
        if start == end:
            pos = start + 1
            continue

        # Validator-backed patterns (such as Luhn credit-card checks) can greedily
        # absorb adjacent digit groups and fail validation as a whole while still
        # containing a valid sub-span on separator boundaries.
        probe_end = end
        while probe_end > start:
            sub = (
                match if probe_end == end else entity_pattern.pattern.match(text, start, probe_end)
            )
            if (
                sub is not None
                and sub.end() == probe_end
                and (probe_end == end or not text[probe_end].isalnum())
            ):
                candidate = sub.group(0)
                if validator(candidate):
                    yield _CandidateSpan(
                        start,
                        probe_end,
                        priority,
                        entity_pattern.kind,
                        candidate,
                    )

            cursor = probe_end - 1
            while cursor > start and text[cursor].isalnum():
                cursor -= 1
            while cursor > start and not text[cursor - 1].isalnum():
                cursor -= 1
            probe_end = cursor

        next_pos = start + 1
        while next_pos < end and text[next_pos].isalnum():
            next_pos += 1
        while next_pos < end and not text[next_pos].isalnum():
            next_pos += 1
        pos = next_pos


def _resolve_non_overlapping(candidates: list[_CandidateSpan]) -> list[_CandidateSpan]:
    if not candidates:
        return []

    ordered = sorted(candidates, key=lambda c: (c.end, c.start, c.priority))
    ends = [c.end for c in ordered]
    count = len(ordered)

    # Maximize total redacted characters; break ties toward fewer split spans,
    # earlier pattern registration order, and leftmost start index.
    dp_score: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)] * (count + 1)
    take: list[bool] = [False] * count
    prev_idx: list[int] = [0] * count

    for index, cand in enumerate(ordered):
        compatible = bisect_right(ends, cand.start, 0, index)
        base = dp_score[compatible]
        with_cand = (
            base[0] + (cand.end - cand.start),
            base[1] - 1,
            base[2] - cand.priority,
            base[3] - cand.start,
        )
        if with_cand > dp_score[index]:
            dp_score[index + 1] = with_cand
            take[index] = True
            prev_idx[index] = compatible
        else:
            dp_score[index + 1] = dp_score[index]

    selected: list[_CandidateSpan] = []
    cursor = count
    while cursor > 0:
        if take[cursor - 1]:
            selected.append(ordered[cursor - 1])
            cursor = prev_idx[cursor - 1]
        else:
            cursor -= 1

    selected.reverse()
    return selected


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
