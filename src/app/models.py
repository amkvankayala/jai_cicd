"""Response models exposed by the API."""

from pydantic import BaseModel, Field


class Quote(BaseModel):
    ticker: str
    price: float | None
    currency: str | None
    change_percent: float | None
    market_time: str | None


class Fundamentals(BaseModel):
    ticker: str
    company_name: str | None
    sector: str | None
    market_cap: float | None
    pe_ratio: float | None
    eps: float | None
    dividend_yield: float | None
    revenue_ttm: float | None
    source: str


class TechnicalAnalysis(BaseModel):
    ticker: str
    sma_20: float | None
    sma_50: float | None
    rsi_14: float | None
    trend: str


class ResearchAnalysis(BaseModel):
    ticker: str
    weekly_highlights: list[str] = Field(default_factory=list)
    swot: dict[str, list[str]] = Field(default_factory=dict)
    short_term_outlook: str
    long_term_outlook: str
    references: list[str] = Field(default_factory=list)
