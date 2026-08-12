import pytest

from agentease import AgentEaseConfig, ConfigurationError


def test_config_reads_provider_key_from_env(monkeypatch) -> None:
    monkeypatch.setenv("AGENTEASE_PROVIDER", "openai")
    monkeypatch.setenv("AGENTEASE_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    config = AgentEaseConfig.from_env()

    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.api_key == "test-key"


def test_config_builds_litellm_model_from_provider() -> None:
    config = AgentEaseConfig(provider="openai", model="gpt-4o-mini")

    assert config.litellm_model == "openai/gpt-4o-mini"


def test_config_keeps_fully_qualified_model() -> None:
    config = AgentEaseConfig(provider="openai", model="anthropic/claude-3-5-haiku")

    assert config.litellm_model == "anthropic/claude-3-5-haiku"


def test_config_uses_safe_request_defaults() -> None:
    config = AgentEaseConfig()

    assert config.timeout == 30
    assert config.max_tokens == 800


@pytest.mark.parametrize(
    "kwargs",
    [
        {"provider": " "},
        {"model": ""},
        {"api_key": " "},
        {"timeout": 0},
        {"timeout": True},
        {"timeout": float("nan")},
        {"timeout": float("inf")},
        {"max_tokens": 0},
        {"max_tokens": 1.5},
    ],
)
def test_config_rejects_blank_or_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises(ConfigurationError):
        AgentEaseConfig(**kwargs)  # type: ignore[arg-type]


def test_config_reads_request_limits_from_env(monkeypatch) -> None:
    monkeypatch.setenv("AGENTEASE_TIMEOUT", "12.5")
    monkeypatch.setenv("AGENTEASE_MAX_TOKENS", "321")

    config = AgentEaseConfig.from_env()

    assert config.timeout == 12.5
    assert config.max_tokens == 321
