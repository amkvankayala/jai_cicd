"""OpenAI web-search research adapter."""

from openai import OpenAI, OpenAIError
from pydantic import BaseModel

from src.app.core.config import settings
from src.app.core.logging import logger
from src.app.models import ResearchAnalysis
from src.app.services.market_data import normalize_ticker


class SWOT(BaseModel):
    """Structured strengths, weaknesses, opportunities, and threats."""

    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]


class StockResearchResponse(BaseModel):
    """Structured output requested from OpenAI's web-search response."""

    weekly_highlights: list[str]
    swot: SWOT
    short_term_outlook: str
    long_term_outlook: str
    references: list[str]


class ResearchService:
    """Create cited stock research using OpenAI's web-search tool."""

    def get_analysis(self, ticker: str) -> ResearchAnalysis:
        symbol = normalize_ticker(ticker)
        if not settings.openai_api_key:
            logger.error("Research requested for ticker=%s without an OpenAI API key", symbol)
            raise RuntimeError("OPENAI_API_KEY is required for AI research.")
        logger.info(
            "Starting OpenAI web-search research for ticker=%s model=%s",
            symbol,
            settings.openai_model,
        )
        client = OpenAI(api_key=settings.openai_api_key)
        prompt = (
            f"Research the company corresponding to {symbol} using web search. "
            "Cover only the past seven days."
            "State uncertainty "
            "Check for any news items from major news outlets that may indicate "
            "a change in the company's fundamentals or outlook"
            "and do not provide investment advice. Provide a source URL in references for every "
            "factual claim. Use the required response schema."
        )
        try:
            response = client.responses.parse(
                model=settings.openai_model,
                tools=[{"type": "web_search"}],
                input=prompt,
                text_format=StockResearchResponse,
            )
        except OpenAIError as error:
            logger.exception("OpenAI web-search request failed for ticker=%s: %s", symbol, error)
            raise RuntimeError(f"OpenAI web-search request failed: {error}") from error
        if response.output_parsed is None:
            output_types = [getattr(item, "type", type(item).__name__) for item in response.output]
            logger.error(
                "OpenAI returned no parsed research for ticker=%s output_types=%s",
                symbol,
                output_types,
            )
            raise RuntimeError("OpenAI returned an empty research response.")
        result = ResearchAnalysis(ticker=symbol, **response.output_parsed.model_dump())
        logger.info(
            "OpenAI research parsed for ticker=%s highlights=%s references=%s",
            symbol,
            len(result.weekly_highlights),
            len(result.references),
        )
        return result
