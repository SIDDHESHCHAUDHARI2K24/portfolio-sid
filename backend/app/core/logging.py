"""Application logging setup.

uvicorn only configures its own ``uvicorn.*`` loggers, so without this the
``app.*`` loggers inherit the root WARNING level and every INFO line (auth and
email outcomes) is dropped in production.
"""

import logging
import sys

_APP_LOGGER = "app"
_HANDLER_NAME = "app-stderr"
_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging() -> None:
    """Send ``app.*`` INFO and above to stderr. Safe to call repeatedly.

    ``propagate`` stays on so pytest's caplog (a root handler) still sees every
    record. The handler is skipped when the root logger already has handlers
    (an embedding host or pytest), which would otherwise print each line twice.
    """
    logger = logging.getLogger(_APP_LOGGER)
    logger.setLevel(logging.INFO)

    if any(h.get_name() == _HANDLER_NAME for h in logger.handlers):
        return
    if logging.getLogger().handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.set_name(_HANDLER_NAME)
    handler.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(handler)
