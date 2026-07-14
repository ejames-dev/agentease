"""Stable, privacy-safe exceptions raised by the public SDK."""


class AgentEaseError(Exception):
    """Base class for all errors intentionally exposed by AgentEase."""


class ConfigurationError(AgentEaseError, ValueError):
    """Raised when SDK configuration is invalid."""


class InputValidationError(AgentEaseError, ValueError):
    """Raised when workflow input is missing or invalid."""


class ProviderError(AgentEaseError, RuntimeError):
    """Raised when an LLM provider request cannot produce a response."""


class OutputValidationError(AgentEaseError, ValueError):
    """Raised when model output cannot be validated after repair attempts."""
