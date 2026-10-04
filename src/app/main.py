"""FastAPI application entry point."""

from fastapi import FastAPI

from src.app.api.routers import health, stocks
from src.app.core.logging import logger

app = FastAPI(title="Stock Insights API", version="0.1.0")
app.include_router(health.router)
app.include_router(stocks.router, prefix="/api/v1")

x = 10


@app.on_event("startup")
def startup() -> None:
    """Log application startup."""
    logger.info("Stock Insights API started")
