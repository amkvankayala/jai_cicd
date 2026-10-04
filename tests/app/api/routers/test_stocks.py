"""Tests for stock routers."""

from fastapi.testclient import TestClient

from src.app.main import app
from src.app.models import Fundamentals, Quote, ResearchAnalysis

client = TestClient(app)


def test_quote_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.api.routers.stocks.market_data.get_quote",
        lambda ticker: Quote(
            ticker=ticker, price=100, currency="USD", change_percent=1, market_time=None
        ),
    )
    response = client.get("/api/v1/stocks/aapl/quote")

    assert response.status_code == 200
    assert response.json()["price"] == 100


def test_quote_returns_bad_request_for_invalid_ticker(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.api.routers.stocks.market_data.get_quote",
        lambda ticker: (_ for _ in ()).throw(ValueError("bad ticker")),
    )

    response = client.get("/api/v1/stocks/bad/quote")

    assert response.status_code == 400
    assert response.json()["detail"] == "bad ticker"


def test_fundamentals_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.api.routers.stocks.fundamentals.get_fundamentals",
        lambda ticker: Fundamentals(
            ticker=ticker,
            company_name="Apple",
            sector="Tech",
            market_cap=1,
            pe_ratio=2,
            eps=3,
            dividend_yield=4,
            revenue_ttm=5,
            source="test",
        ),
    )

    response = client.get("/api/v1/stocks/AAPL/fundamentals")

    assert response.status_code == 200
    assert response.json()["company_name"] == "Apple"


def test_technical_returns_provider_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.api.routers.stocks.market_data.get_technical_analysis",
        lambda ticker: (_ for _ in ()).throw(ValueError("no data")),
    )

    response = client.get("/api/v1/stocks/AAPL/technical")

    assert response.status_code == 400


def test_research_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.api.routers.stocks.research.get_analysis",
        lambda ticker: ResearchAnalysis(
            ticker=ticker,
            weekly_highlights=["Update"],
            swot={"Strengths": ["Brand"]},
            short_term_outlook="Neutral",
            long_term_outlook="Positive",
            references=["https://example.com"],
        ),
    )

    response = client.get("/api/v1/stocks/AAPL/research")

    assert response.status_code == 200
    assert response.json()["references"] == ["https://example.com"]


def test_research_returns_gateway_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.app.api.routers.stocks.research.get_analysis",
        lambda ticker: (_ for _ in ()).throw(RuntimeError("missing key")),
    )

    response = client.get("/api/v1/stocks/AAPL/research")

    assert response.status_code == 502
