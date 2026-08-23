"""GlitchTip / Sentry error tracking (conventions gap G11).

GlitchTip (glitchtip.com) is an open-source Sentry-compatible error tracker.
It accepts standard Sentry SDKs — just point the DSN at a GlitchTip instance.

Env: ``GLITCHTIP_DSN`` — if unset, error tracking is silently disabled.
"""

import logging

logger = logging.getLogger(__name__)


def init_glitchtip(dsn: str | None, *, environment: str = "production") -> None:
    """Configure Sentry SDK to report to a GlitchTip instance.

    Call once at startup. No-op when ``dsn`` is None/empty.
    """
    if not dsn:
        return

    try:
        import sentry_sdk  # noqa: F811
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                StarletteIntegration(),
                FastApiIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=environment,
            send_default_pii=False,
        )
        logger.info("GlitchTip error tracking enabled environment=%s", environment)
    except Exception:
        logger.warning("GlitchTip init failed — error tracking disabled", exc_info=True)
