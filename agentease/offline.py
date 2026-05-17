from __future__ import annotations

import json


class OfflineTriageLlmClient:
    """Deterministic local LLM stand-in for demos and docs."""

    def complete(self, prompt: str) -> str:
        prompt_lower = self._ticket_context(prompt).lower()
        category = self._category(prompt_lower)
        priority = self._priority(prompt_lower)
        return json.dumps(
            {
                "category": category,
                "priority": priority,
                "summary": self._summary(category, priority),
                "suggested_reply": self._reply(category, priority),
            }
        )

    def _category(self, prompt_lower: str) -> str:
        if any(word in prompt_lower for word in ("charged", "refund", "invoice", "billing")):
            return "billing"
        if any(word in prompt_lower for word in ("bug", "error", "crash", "broken")):
            return "technical"
        if any(word in prompt_lower for word in ("login", "password", "account")):
            return "account"
        if any(word in prompt_lower for word in ("demo", "pricing", "trial", "sales")):
            return "sales"
        return "other"

    def _priority(self, prompt_lower: str) -> str:
        if any(word in prompt_lower for word in ("urgent", "immediately", "down", "blocked")):
            return "urgent"
        if any(word in prompt_lower for word in ("charged twice", "refund", "crash")):
            return "high"
        if any(word in prompt_lower for word in ("question", "help", "issue")):
            return "medium"
        return "low"

    def _ticket_context(self, prompt: str) -> str:
        markers = ("Sanitized ticket for context:", "Sanitized ticket:")
        for marker in markers:
            if marker in prompt:
                return prompt.split(marker, maxsplit=1)[1]
        return prompt

    def _summary(self, category: str, priority: str) -> str:
        if category == "billing":
            return "Customer reports a billing issue that needs review."
        if category == "technical":
            return "Customer reports a technical issue affecting product usage."
        if category == "account":
            return "Customer needs help with account access or settings."
        if category == "sales":
            return "Customer is asking about sales or evaluation next steps."
        return f"Customer request categorized as {category} with {priority} priority."

    def _reply(self, category: str, priority: str) -> str:
        if priority in {"high", "urgent"}:
            return "Thanks for reaching out. We are escalating this and will follow up shortly."
        if category == "sales":
            return "Thanks for your interest. We will follow up with the best next step."
        return "Thanks for reaching out. We will review this and get back to you soon."
