"""Tests for application logging."""

from src.app.core.logging import configure_logging


def test_configure_logging_is_idempotent() -> None:
    logger = configure_logging()
    handlers_before = len(logger.handlers)

    assert configure_logging() is logger
    assert len(logger.handlers) == handlers_before
