"""Configuration loaded from environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for external providers."""

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    alphavantage_api_key: str | None = os.getenv("ALPHAVANTAGE_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


settings = Settings()
