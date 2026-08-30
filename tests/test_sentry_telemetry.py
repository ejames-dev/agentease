from __future__ import annotations

import sys
import types

from agentease.telemetry.sentry import capture_exception


def test_capture_exception_is_a_noop_without_sentry_sdk(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "sentry_sdk", None)
    capture_exception(ValueError("boom"))


def test_capture_exception_forwards_to_sentry_sdk_when_available(monkeypatch) -> None:
    calls: list[BaseException] = []
    fake_sentry_sdk = types.SimpleNamespace(capture_exception=calls.append)
    monkeypatch.setitem(sys.modules, "sentry_sdk", fake_sentry_sdk)

    error = ValueError("boom")
    capture_exception(error)

    assert calls == [error]
