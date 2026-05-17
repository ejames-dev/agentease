from agentease import AgentEaseConfig


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
