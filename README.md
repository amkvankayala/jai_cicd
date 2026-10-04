# Stock Insights

FastAPI backend and Streamlit UI for stock quotes, fundamentals, technical indicators, and
AI-assisted weekly research.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn src.app.main:app --reload
streamlit run src/ui/app.py
```

Copy `.env.example` to `.env` and supply an OpenAI API key to enable web-search analysis.
`ALPHAVANTAGE_API_KEY` is optional; its free tier enriches the fundamentals endpoint, which
otherwise falls back to Yahoo Finance data via yfinance.

## Quality checks

```powershell
ruff check .
pytest
```


