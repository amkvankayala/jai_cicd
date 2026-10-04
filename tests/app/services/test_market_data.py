"""Tests for market data calculations and provider fallback."""

import warnings
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
import yfinance as yf

from src.app.services.market_data import FundamentalsService, MarketDataService, normalize_ticker


def test_normalize_ticker_accepts_market_symbols() -> None:
    assert normalize_ticker(" brk.b ") == "BRK.B"


def test_normalize_ticker_accepts_indian_exchange_aliases() -> None:
    assert normalize_ticker("NSE:reliance") == "RELIANCE.NS"
    assert normalize_ticker("BSE:500325") == "500325.BO"


def test_normalize_ticker_rejects_invalid_input() -> None:
    with pytest.raises(ValueError, match="Ticker"):
        normalize_ticker("AAPL/")


def test_yfinance_timedelta_deprecation_is_suppressed_at_provider_boundary() -> None:
    warning_code = (
        "import warnings\n"
        "warnings.warn(\"The 'generic' unit for NumPy timedelta is deprecated, "
        'and will raise an error in the future.", DeprecationWarning)'
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with MarketDataService._suppress_yfinance_timedelta_warning():
            exec(warning_code, yf.utils.__dict__)  # noqa: S102

    assert caught == []


def test_get_quote_calculates_change(monkeypatch) -> None:
    ticker = Mock(fast_info={"lastPrice": 110, "previousClose": 100, "currency": "USD"})
    monkeypatch.setattr("src.app.services.market_data.yf.Ticker", lambda symbol: ticker)

    result = MarketDataService().get_quote("aapl")

    assert result.ticker == "AAPL"
    assert result.change_percent == 10


def test_technical_analysis_calculates_indicators(monkeypatch) -> None:
    closes = pd.Series(range(1, 101), dtype=float)
    ticker = Mock(history=Mock(return_value=pd.DataFrame({"Close": closes})))
    monkeypatch.setattr("src.app.services.market_data.yf.Ticker", lambda symbol: ticker)

    result = MarketDataService().get_technical_analysis("MSFT")

    assert result.sma_20 == 90.5
    assert result.sma_50 == 75.5
    assert result.trend == "bullish"


def test_technical_analysis_rejects_empty_history(monkeypatch) -> None:
    ticker = Mock(history=Mock(return_value=pd.DataFrame()))
    monkeypatch.setattr("src.app.services.market_data.yf.Ticker", lambda symbol: ticker)

    with pytest.raises(ValueError, match="No price history"):
        MarketDataService().get_technical_analysis("MSFT")


def test_alpha_vantage_payload_is_mapped() -> None:
    result = FundamentalsService._from_alpha_vantage(
        "AAPL",
        {
            "Name": "Apple",
            "Sector": "Technology",
            "MarketCapitalization": "10",
            "PERatio": "2",
            "EPS": "3",
            "DividendYield": "0.01",
            "RevenueTTM": "20",
        },
    )

    assert result.source == "Alpha Vantage"
    assert result.market_cap == 10


def test_fundamentals_falls_back_to_yfinance_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.services.market_data.settings",
        SimpleNamespace(alphavantage_api_key=None),
    )
    ticker = Mock(info={"longName": "Apple", "marketCap": 1})
    monkeypatch.setattr("src.app.services.market_data.yf.Ticker", lambda symbol: ticker)

    result = FundamentalsService().get_fundamentals("AAPL")

    assert result.company_name == "Apple"
    assert result.source == "Yahoo Finance"
