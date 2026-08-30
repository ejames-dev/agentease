"""Optional, passive Sentry error reporting.

AgentEase never initializes a Sentry client and never ships a DSN. This
module only forwards exceptions to whatever client the *host application*
has already configured via its own ``sentry_sdk.init(...)`` call. Install
the ``sentry`` extra (``pip install agentease[sentry]``) to enable it; with
the extra absent, or no host-side ``sentry_sdk.init(...)``, this is a no-op.
"""

from __future__ import annotations

from contextlib import suppress


def capture_exception(error: BaseException) -> None:
    with suppress(Exception):
        import sentry_sdk

        sentry_sdk.capture_exception(error)
