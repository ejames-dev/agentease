from __future__ import annotations

import os
from dataclasses import dataclass
from math import isfinite

from agentease.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class AgentEaseConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str | None = None
    timeout: float = 30
    max_tokens: int = 800

    def __post_init__(self) -> None:
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ConfigurationError("provider must be a non-blank string")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ConfigurationError("model must be a non-blank string")
        if self.api_key is not None and (
            not isinstance(self.api_key, str) or not self.api_key.strip()
        ):
            raise ConfigurationError("api_key must be None or a non-blank string")
        if isinstance(self.timeout, bool) or not isinstance(self.timeout, (int, float)):
            raise ConfigurationError("timeout must be a positive number")
        if not isfinite(self.timeout) or self.timeout <= 0:
            raise ConfigurationError("timeout must be a positive number")
        if isinstance(self.max_tokens, bool) or not isinstance(self.max_tokens, int):
            raise ConfigurationError("max_tokens must be a positive integer")
        if self.max_tokens <= 0:
            raise ConfigurationError("max_tokens must be a positive integer")

    @classmethod
    def from_env(cls) -> AgentEaseConfig:
        provider = os.getenv("AGENTEASE_PROVIDER", "openai")
        model = os.getenv("AGENTEASE_MODEL", "gpt-4o-mini")
        api_key = os.getenv("AGENTEASE_API_KEY") or os.getenv(_provider_api_key_name(provider), "")
        timeout = _float_from_env("AGENTEASE_TIMEOUT", 30)
        max_tokens = _int_from_env("AGENTEASE_MAX_TOKENS", 800)
        return cls(
            provider=provider,
            model=model,
            api_key=api_key or None,
            timeout=timeout,
            max_tokens=max_tokens,
        )

    @property
    def litellm_model(self) -> str:
        if "/" in self.model:
            return self.model
        return f"{self.provider}/{self.model}"


def _provider_api_key_name(provider: str) -> str:
    normalized = provider.upper().replace("-", "_")
    return f"{normalized}_API_KEY"


def _float_from_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ConfigurationError(f"{name} must be a positive number") from None


def _int_from_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ConfigurationError(f"{name} must be a positive integer") from None
