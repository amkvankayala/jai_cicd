"""Tests for application configuration."""

from fastapi.testclient import TestClient

from src.app.main import app


def test_application_metadata_and_routes() -> None:
    client = TestClient(app)

    assert app.title == "Stock Insights API"
    assert client.get("/health").status_code == 200
    assert client.get("/openapi.json").status_code == 200
