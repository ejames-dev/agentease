from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentEaseConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str | None = None

    @classmethod
    def from_env(cls) -> AgentEaseConfig:
        provider = os.getenv("AGENTEASE_PROVIDER", "openai")
        model = os.getenv("AGENTEASE_MODEL", "gpt-4o-mini")
        api_key = os.getenv("AGENTEASE_API_KEY") or os.getenv(_provider_api_key_name(provider), "")
        return cls(provider=provider, model=model, api_key=api_key or None)

    @property
    def litellm_model(self) -> str:
        if "/" in self.model:
            return self.model
        return f"{self.provider}/{self.model}"


def _provider_api_key_name(provider: str) -> str:
    normalized = provider.upper().replace("-", "_")
    return f"{normalized}_API_KEY"
