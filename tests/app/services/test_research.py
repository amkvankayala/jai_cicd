"""Tests for OpenAI research adapter."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.app.services.research import SWOT, ResearchService, StockResearchResponse


def test_research_requires_openai_key(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.services.research.settings",
        SimpleNamespace(openai_api_key=None, openai_model="test-model"),
    )

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        ResearchService().get_analysis("AAPL")


def test_research_uses_web_search_and_parses_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.services.research.settings",
        SimpleNamespace(openai_api_key="test-key", openai_model="test-model"),
    )
    response = SimpleNamespace(
        output_parsed=StockResearchResponse(
            weekly_highlights=["Event"],
            swot=SWOT(strengths=["Brand"], weaknesses=[], opportunities=[], threats=[]),
            short_term_outlook="Neutral",
            long_term_outlook="Positive",
            references=["https://example.com"],
        )
    )
    fake_client = SimpleNamespace(responses=SimpleNamespace(parse=Mock(return_value=response)))
    monkeypatch.setattr("src.app.services.research.OpenAI", lambda api_key: fake_client)

    result = ResearchService().get_analysis("aapl")

    assert result.ticker == "AAPL"
    assert fake_client.responses.parse.call_args.kwargs["tools"] == [{"type": "web_search"}]
    assert fake_client.responses.parse.call_args.kwargs["text_format"] is StockResearchResponse


def test_research_rejects_missing_parsed_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.services.research.settings",
        SimpleNamespace(openai_api_key="test-key", openai_model="test-model"),
    )
    response = SimpleNamespace(output_parsed=None, output=[SimpleNamespace(type="web_search_call")])
    fake_client = SimpleNamespace(responses=SimpleNamespace(parse=Mock(return_value=response)))
    monkeypatch.setattr("src.app.services.research.OpenAI", lambda api_key: fake_client)

    with pytest.raises(RuntimeError, match="empty"):
        ResearchService().get_analysis("AAPL")
