"""Market-data providers and derived calculations."""

import warnings
from contextlib import contextmanager
from typing import Any

import httpx
import pandas as pd
import yfinance as yf

from src.app.core.config import settings
from src.app.core.logging import logger
from src.app.models import Fundamentals, Quote, TechnicalAnalysis

YFINANCE_TIMEDELTA_WARNING = (
    r"The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future.*"
)


def normalize_ticker(ticker: str) -> str:
    """Validate and normalize a Yahoo Finance ticker, including Indian exchange aliases."""
    normalized = ticker.strip().upper()
    exchange_prefixes = {"NSE:": ".NS", "BSE:": ".BO"}
    for prefix, suffix in exchange_prefixes.items():
        if normalized.startswith(prefix):
            normalized = f"{normalized.removeprefix(prefix)}{suffix}"
            logger.info(
                "Converted Indian exchange ticker input=%r normalized=%r", ticker, normalized
            )
            break
    logger.debug("Normalizing ticker input=%r normalized=%r", ticker, normalized)
    if not normalized or not all(char.isalnum() or char in {"-", "."} for char in normalized):
        logger.warning("Rejected invalid ticker input=%r", ticker)
        raise ValueError("Ticker must contain only letters, numbers, hyphens, or periods.")
    return normalized


class MarketDataService:
    """Fetch quote and historical data from Yahoo Finance through yfinance."""

    def get_quote(self, ticker: str) -> Quote:
        symbol = normalize_ticker(ticker)
        logger.info("Fetching latest Yahoo Finance quote for ticker=%s", symbol)
        with self._suppress_yfinance_timedelta_warning():
            data: dict[str, Any] = yf.Ticker(symbol).fast_info
        last_price = data.get("lastPrice")
        previous_close = data.get("previousClose")
        change_percent = None
        if last_price is not None and previous_close not in (None, 0):
            change_percent = (last_price - previous_close) / previous_close * 100
        logger.info(
            "Quote retrieved for ticker=%s price=%s previous_close=%s",
            symbol,
            last_price,
            previous_close,
        )
        return Quote(
            ticker=symbol,
            price=last_price,
            currency=data.get("currency"),
            change_percent=change_percent,
            market_time=None,
        )

    def get_technical_analysis(self, ticker: str) -> TechnicalAnalysis:
        symbol = normalize_ticker(ticker)
        logger.info("Fetching six-month price history for ticker=%s", symbol)
        with self._suppress_yfinance_timedelta_warning():
            history = yf.Ticker(symbol).history(period="6mo", auto_adjust=True)
        if history.empty or "Close" not in history:
            logger.warning("No technical-analysis history returned for ticker=%s", symbol)
            raise ValueError(f"No price history found for {symbol}.")
        closes = history["Close"]
        sma_20 = closes.rolling(20).mean().iloc[-1]
        sma_50 = closes.rolling(50).mean().iloc[-1]
        rsi = self._rsi(closes).iloc[-1]
        trend = "bullish" if sma_20 > sma_50 else "bearish" if sma_20 < sma_50 else "neutral"
        logger.info(
            "Technical analysis computed for ticker=%s rows=%s trend=%s",
            symbol,
            len(history),
            trend,
        )
        return TechnicalAnalysis(
            ticker=symbol,
            sma_20=self._number(sma_20),
            sma_50=self._number(sma_50),
            rsi_14=self._number(rsi),
            trend=trend,
        )

    @staticmethod
    def _rsi(closes: pd.Series, period: int = 14) -> pd.Series:
        change = closes.diff()
        gain = change.clip(lower=0).rolling(period).mean()
        loss = -change.clip(upper=0).rolling(period).mean()
        return 100 - (100 / (1 + gain / loss.replace(0, float("nan"))))

    @staticmethod
    def _number(value: Any) -> float | None:
        return None if pd.isna(value) else round(float(value), 2)

    @staticmethod
    @contextmanager
    def _suppress_yfinance_timedelta_warning():
        """Limit a known yfinance/NumPy compatibility warning to yfinance calls only."""
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=YFINANCE_TIMEDELTA_WARNING,
                category=DeprecationWarning,
                module=r"yfinance\.utils",
            )
            yield


class FundamentalsService:
    """Use Alpha Vantage's free overview endpoint with a yfinance fallback."""

    alpha_vantage_url = "https://www.alphavantage.co/query"

    def get_fundamentals(self, ticker: str) -> Fundamentals:
        symbol = normalize_ticker(ticker)
        if settings.alphavantage_api_key:
            logger.info("Fetching Alpha Vantage fundamentals for ticker=%s", symbol)
            try:
                response = httpx.get(
                    self.alpha_vantage_url,
                    params={
                        "function": "OVERVIEW",
                        "symbol": symbol,
                        "apikey": settings.alphavantage_api_key,
                    },
                    timeout=10,
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("Symbol"):
                    logger.info("Alpha Vantage fundamentals retrieved for ticker=%s", symbol)
                    return self._from_alpha_vantage(symbol, payload)
                logger.warning("Alpha Vantage returned no overview for ticker=%s", symbol)
            except httpx.HTTPError as error:
                logger.warning("Alpha Vantage unavailable for ticker=%s: %s", symbol, error)
        else:
            logger.info(
                "No Alpha Vantage key configured; using Yahoo Finance for ticker=%s", symbol
            )
        logger.info("Fetching Yahoo Finance fundamentals for ticker=%s", symbol)
        return self._from_yfinance(symbol)

    @staticmethod
    def _from_alpha_vantage(symbol: str, data: dict[str, Any]) -> Fundamentals:
        def number(key: str) -> float | None:
            try:
                return float(data[key]) if data.get(key) not in (None, "None", "-") else None
            except ValueError:
                return None

        return Fundamentals(
            ticker=symbol,
            company_name=data.get("Name"),
            sector=data.get("Sector"),
            market_cap=number("MarketCapitalization"),
            pe_ratio=number("PERatio"),
            eps=number("EPS"),
            dividend_yield=number("DividendYield"),
            revenue_ttm=number("RevenueTTM"),
            source="Alpha Vantage",
        )

    @staticmethod
    def _from_yfinance(symbol: str) -> Fundamentals:
        with MarketDataService._suppress_yfinance_timedelta_warning():
            info = yf.Ticker(symbol).info
        logger.info(
            "Yahoo Finance fundamentals retrieved for ticker=%s fields=%s", symbol, len(info)
        )
        return Fundamentals(
            ticker=symbol,
            company_name=info.get("longName"),
            sector=info.get("sector"),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            eps=info.get("trailingEps"),
            dividend_yield=info.get("dividendYield"),
            revenue_ttm=info.get("totalRevenue"),
            source="Yahoo Finance",
        )
