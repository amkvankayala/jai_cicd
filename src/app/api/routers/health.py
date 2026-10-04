"""Health endpoints."""

from fastapi import APIRouter

from src.app.core.logging import logger

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Report whether the service is running."""
    logger.info("Health check requested")
    return {"status": "ok"}
