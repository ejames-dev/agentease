from __future__ import annotations

import json

from agentease.offline import OfflineTriageLlmClient
from agentease.templates.base import LlmClient


def _context(prompt: str, labels: tuple[str, ...]) -> str:
    """Return the sanitized text that follows the first matching prompt label."""
    for label in labels:
        marker = f"{label}:"
        if marker in prompt:
            return prompt.split(marker, maxsplit=1)[1]
    return prompt


class OfflineLeadQualificationLlmClient:
    """Deterministic local stand-in for the lead qualification workflow."""

    LABELS = ("Sanitized inbound message for context", "Sanitized inbound message")

    def complete(self, prompt: str) -> str:
        text = _context(prompt, self.LABELS).lower()
        intent = self._intent(text)
        return json.dumps(
            {
                "intent": intent,
                "fit": self._fit(text),
                "budget_signal": self._budget_signal(text),
                "next_action": self._next_action(intent, text),
                "summary": "Inbound message scored for buying intent and fit.",
                "rationale": f"Classified as a {intent} lead from the sanitized message.",
            }
        )

    def _intent(self, text: str) -> str:
        if any(w in text for w in ("buy", "purchase", "demo", "quote", "contract", "ready")):
            return "hot"
        if any(w in text for w in ("interested", "evaluate", "trial", "considering", "pricing")):
            return "warm"
        if any(w in text for w in ("maybe", "future", "just looking", "someday")):
            return "cold"
        return "not_a_lead"

    def _fit(self, text: str) -> str:
        if any(w in text for w in ("enterprise", "global", "thousand", "corp")):
            return "enterprise"
        if any(w in text for w in ("mid-market", "mid market", "growing", "hundred")):
            return "mid_market"
        if any(w in text for w in ("startup", "small", "solo", "few")):
            return "smb"
        return "unknown"

    def _budget_signal(self, text: str) -> str:
        if any(w in text for w in ("$", "budget", "pricing", "quote")):
            return "explicit"
        if any(w in text for w in ("seats", "team", "plan", "users")):
            return "implied"
        return "none"

    def _next_action(self, intent: str, text: str) -> str:
        if "demo" in text:
            return "book_demo"
        if any(w in text for w in ("pricing", "quote", "$")):
            return "send_pricing"
        if intent in {"warm", "cold"}:
            return "nurture"
        return "disqualify"


class OfflineDocClassificationLlmClient:
    """Deterministic local stand-in for the document classification workflow."""

    LABELS = ("Sanitized document for context", "Sanitized document")

    def complete(self, prompt: str) -> str:
        context = _context(prompt, self.LABELS)
        text = context.lower()
        return json.dumps(
            {
                "doc_type": self._doc_type(text),
                "sensitivity": self._sensitivity(text),
                "contains_pii": "[redacted_" in text,
                "summary": "Document classified and assessed for data sensitivity.",
                "recommended_handling": self._handling(text),
            }
        )

    def _doc_type(self, text: str) -> str:
        if any(w in text for w in ("agreement", "contract", "msa", "terms")):
            return "contract"
        if any(w in text for w in ("invoice", "net-30", "amount due", "payment")):
            return "invoice"
        if any(w in text for w in ("policy", "compliance", "gdpr")):
            return "policy"
        if any(w in text for w in ("report", "analysis", "findings")):
            return "report"
        if any(w in text for w in ("dear", "letter", "regards", "email")):
            return "correspondence"
        return "other"

    def _sensitivity(self, text: str) -> str:
        if any(w in text for w in ("restricted", "secret")):
            return "restricted"
        if any(w in text for w in ("confidential", "agreement", "contract", "[redacted_")):
            return "confidential"
        if "internal" in text:
            return "internal"
        return "public"

    def _handling(self, text: str) -> str:
        if "[redacted_" in text:
            return "Store in a restricted location; PII was detected and masked locally."
        return "Standard internal handling is sufficient."


OFFLINE_RESPONDERS: dict[str, LlmClient] = {
    "triage": OfflineTriageLlmClient(),
    "lead_qualification": OfflineLeadQualificationLlmClient(),
    "doc_classification": OfflineDocClassificationLlmClient(),
}


def offline_client_for(spec_name: str) -> LlmClient:
    """Return the deterministic offline responder registered for ``spec_name``."""
    try:
        return OFFLINE_RESPONDERS[spec_name]
    except KeyError:
        raise KeyError(
            f"No offline responder registered for workflow {spec_name!r}. "
            f"Known workflows: {sorted(OFFLINE_RESPONDERS)}."
        ) from None
