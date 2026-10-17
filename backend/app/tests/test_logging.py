"""App logging setup: app.* INFO reaches a handler without caplog help."""

import logging
from collections.abc import Iterator

import pytest

from app.app import create_app


@pytest.fixture
def app_logger(monkeypatch: pytest.MonkeyPatch) -> Iterator[logging.Logger]:
    logger = logging.getLogger("app")
    monkeypatch.setattr(logger, "level", logging.NOTSET)
    monkeypatch.setattr(logger, "handlers", [])
    yield logger


def _bare_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production under uvicorn has no root handlers; pytest adds its own per phase."""
    monkeypatch.setattr(logging.getLogger(), "handlers", [])


def test_create_app_enables_info_for_app_loggers(app_logger: logging.Logger) -> None:
    assert not logging.getLogger("app.auth").isEnabledFor(logging.INFO)
    create_app()
    assert logging.getLogger("app.auth").isEnabledFor(logging.INFO)
    assert logging.getLogger("app.core.email").isEnabledFor(logging.INFO)


def test_create_app_twice_adds_one_handler(
    app_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    _bare_root(monkeypatch)
    create_app()
    create_app()
    assert len(app_logger.handlers) == 1


def test_info_line_reaches_stderr(
    app_logger: logging.Logger,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _bare_root(monkeypatch)
    create_app()
    # The handler binds sys.stderr at creation, which capsys has already swapped.
    logging.getLogger("app.auth").info("login ok")
    assert "login ok" in capsys.readouterr().err


def test_no_handler_added_when_root_is_configured(
    app_logger: logging.Logger, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(logging.getLogger(), "handlers", [logging.NullHandler()])
    create_app()
    assert app_logger.handlers == []
    assert logging.getLogger("app.auth").isEnabledFor(logging.INFO)
