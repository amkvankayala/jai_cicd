"""Stock data and research endpoints."""

from fastapi import APIRouter, HTTPException

from src.app.core.logging import logger
from src.app.models import Fundamentals, Quote, ResearchAnalysis, TechnicalAnalysis
from src.app.services.market_data import FundamentalsService, MarketDataService
from src.app.services.research import ResearchService

router = APIRouter(prefix="/stocks", tags=["stocks"])
market_data = MarketDataService()
fundamentals = FundamentalsService()
research = ResearchService()


def _translate_error(error: Exception) -> HTTPException:
    status_code = 400 if isinstance(error, ValueError) else 502
    logger.exception("Stock endpoint failed with status %s: %s", status_code, error)
    return HTTPException(status_code=status_code, detail=str(error))


@router.get("/{ticker}/quote", response_model=Quote)
def quote(ticker: str) -> Quote:
    """Return the latest available quote."""
    logger.info("Quote endpoint requested for ticker=%s", ticker)
    try:
        result = market_data.get_quote(ticker)
        logger.info("Quote endpoint completed for ticker=%s", result.ticker)
        return result
    except (ValueError, KeyError) as error:
        raise _translate_error(error) from error


@router.get("/{ticker}/fundamentals", response_model=Fundamentals)
def get_fundamentals(ticker: str) -> Fundamentals:
    """Return core company fundamentals."""
    logger.info("Fundamentals endpoint requested for ticker=%s", ticker)
    try:
        result = fundamentals.get_fundamentals(ticker)
        logger.info(
            "Fundamentals endpoint completed for ticker=%s source=%s",
            result.ticker,
            result.source,
        )
        return result
    except (ValueError, KeyError) as error:
        raise _translate_error(error) from error


@router.get("/{ticker}/technical", response_model=TechnicalAnalysis)
def technical(ticker: str) -> TechnicalAnalysis:
    """Return simple moving-average and RSI technical analysis."""
    logger.info("Technical endpoint requested for ticker=%s", ticker)
    try:
        result = market_data.get_technical_analysis(ticker)
        logger.info(
            "Technical endpoint completed for ticker=%s trend=%s", result.ticker, result.trend
        )
        return result
    except ValueError as error:
        raise _translate_error(error) from error


@router.get("/{ticker}/research", response_model=ResearchAnalysis)
def get_research(ticker: str) -> ResearchAnalysis:
    """Return OpenAI web-search-based weekly research and outlook."""
    logger.info("Research endpoint requested for ticker=%s", ticker)
    try:
        result = research.get_analysis(ticker)
        logger.info("Research endpoint completed for ticker=%s", result.ticker)
        return result
    except (ValueError, RuntimeError) as error:
        raise _translate_error(error) from error
