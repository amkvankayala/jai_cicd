"""Tests for settings."""

from src.app.core.config import Settings


def test_settings_has_default_model() -> None:
    assert Settings().openai_model
