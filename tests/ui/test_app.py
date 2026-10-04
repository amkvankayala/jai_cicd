"""Tests for UI helper functions."""

from unittest.mock import Mock

from src.ui.app import api_get, display_value, fundamentals_rows, market_ticker, technical_rows


def test_api_get_returns_json(monkeypatch) -> None:
    response = Mock(json=Mock(return_value={"status": "ok"}))
    monkeypatch.setattr("src.ui.app.httpx.get", Mock(return_value=response))

    assert api_get("/health") == {"status": "ok"}
    response.raise_for_status.assert_called_once()


def test_market_ticker_converts_indian_symbols() -> None:
    assert market_ticker("reliance", "NSE (India)") == "RELIANCE.NS"
    assert market_ticker("500325", "BSE (India)") == "500325.BO"
    assert market_ticker("AAPL", "US") == "AAPL"


def test_market_ticker_preserves_explicit_indian_suffix() -> None:
    assert market_ticker("TCS.NS", "BSE (India)") == "TCS.NS"


def test_dashboard_table_helpers_format_values() -> None:
    fundamentals = fundamentals_rows({"sector": "Technology", "dividend_yield": 0.02})
    technical = technical_rows({"trend": "bullish", "rsi_14": 56.789})

    assert display_value(None) == "—"
    assert display_value(0.02, percentage=True) == "2.00%"
    assert fundamentals[0] == {"Metric": "Sector", "Value": "Technology"}
    assert fundamentals[4]["Value"] == "2.00%"
    assert technical[0]["Value"] == "Bullish"
