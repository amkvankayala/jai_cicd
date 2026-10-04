"""Interactive Streamlit dashboard for the Stock Insights API."""

import logging
import os

import httpx
import streamlit as st

API_URL = os.getenv("STOCK_API_URL", "http://127.0.0.1:8000/api/v1")
logger = logging.getLogger("stock_insights.ui")


def market_ticker(ticker: str, market: str) -> str:
    """Convert a plain UI ticker into the Yahoo Finance symbol for its selected market."""
    symbol = ticker.strip().upper()
    if not symbol or symbol.endswith((".NS", ".BO")):
        return symbol
    suffixes = {"NSE (India)": ".NS", "BSE (India)": ".BO"}
    return f"{symbol}{suffixes.get(market, '')}"


def display_value(value: object, *, currency: bool = False, percentage: bool = False) -> str:
    """Format optional financial values consistently for the dashboard."""
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        if percentage:
            return f"{value * 100:,.2f}%"
        if currency:
            return f"{value:,.2f}"
        return f"{value:,.2f}"
    return str(value)


def fundamentals_rows(fundamentals: dict) -> list[dict[str, str]]:
    """Prepare a concise table of fundamental indicators."""
    return [
        {"Metric": "Sector", "Value": display_value(fundamentals.get("sector"))},
        {"Metric": "Market cap", "Value": display_value(fundamentals.get("market_cap"))},
        {"Metric": "P/E ratio", "Value": display_value(fundamentals.get("pe_ratio"))},
        {"Metric": "EPS", "Value": display_value(fundamentals.get("eps"))},
        {
            "Metric": "Dividend yield",
            "Value": display_value(fundamentals.get("dividend_yield"), percentage=True),
        },
        {"Metric": "TTM revenue", "Value": display_value(fundamentals.get("revenue_ttm"))},
        {"Metric": "Data source", "Value": display_value(fundamentals.get("source"))},
    ]


def technical_rows(technical: dict) -> list[dict[str, str]]:
    """Prepare a concise table of technical indicators."""
    return [
        {"Metric": "Trend", "Value": display_value(technical.get("trend")).title()},
        {"Metric": "20-day SMA", "Value": display_value(technical.get("sma_20"))},
        {"Metric": "50-day SMA", "Value": display_value(technical.get("sma_50"))},
        {"Metric": "14-day RSI", "Value": display_value(technical.get("rsi_14"))},
    ]


def api_get(path: str) -> dict:
    """Fetch a JSON response from the backend or display an actionable error."""
    logger.info("UI requesting API path=%s", path)
    response = httpx.get(f"{API_URL}{path}", timeout=30)
    response.raise_for_status()
    logger.info("UI received API response path=%s status=%s", path, response.status_code)
    return response.json()


def render() -> None:
    """Render the dashboard."""
    st.set_page_config(page_title="Stock Insights", page_icon="📈")
    st.title("Stock Insights")
    market = st.selectbox("Market", ["NSE (India)", "BSE (India)", "US"])
    ticker = st.text_input(
        "Ticker", value="RELIANCE", help="For example: RELIANCE, TCS, INFY, AAPL"
    ).strip()
    if not st.button("Analyze"):
        logger.debug("UI loaded without an analysis request")
        return
    symbol = market_ticker(ticker, market)
    if not symbol:
        logger.warning("UI analysis requested without a ticker")
        st.warning("Enter a ticker symbol.")
        return
    logger.info("UI analysis requested for ticker=%s market=%s symbol=%s", ticker, market, symbol)
    try:
        quote, fundamentals, technical = (
            api_get(f"/stocks/{symbol}/quote"),
            api_get(f"/stocks/{symbol}/fundamentals"),
            api_get(f"/stocks/{symbol}/technical"),
        )
    except httpx.HTTPError as error:
        logger.exception("UI core market-data request failed for ticker=%s: %s", ticker, error)
        st.error(f"Could not load analysis: {error}")
        return
    st.header(f"{quote['ticker']} · {fundamentals.get('company_name') or 'Stock'}")
    st.metric(
        "Latest price",
        display_value(quote.get("price"), currency=True),
        f"{quote.get('change_percent') or 0:.2f}%",
    )
    st.subheader("Fundamentals")
    st.caption(f"Source: {fundamentals.get('source', 'Unknown')}")
    st.table(fundamentals_rows(fundamentals))
    st.subheader("Technical analysis")
    first, second, third = st.columns(3)
    first.metric("Trend", technical["trend"].title())
    second.metric("RSI (14)", display_value(technical.get("rsi_14")))
    moving_averages = (
        f"{display_value(technical.get('sma_20'))} / {display_value(technical.get('sma_50'))}"
    )
    third.metric("20 / 50-day SMA", moving_averages)
    st.table(technical_rows(technical))
    st.subheader("Past-week research")
    try:
        research = api_get(f"/stocks/{symbol}/research")
    except httpx.HTTPError as error:
        logger.exception("UI research request failed for ticker=%s: %s", ticker, error)
        st.warning(f"AI research is temporarily unavailable: {error}")
        return
    for highlight in research["weekly_highlights"]:
        st.write(f"- {highlight}")
    st.subheader("SWOT")
    for category, items in research["swot"].items():
        st.markdown(f"**{category}**")
        for item in items:
            st.write(f"- {item}")
    st.subheader("Outlook")
    st.write(f"**Short term:** {research['short_term_outlook']}")
    st.write(f"**Long term:** {research['long_term_outlook']}")
    st.subheader("References")
    for url in research["references"]:
        st.markdown(f"- {url}")


if __name__ == "__main__":
    render()
