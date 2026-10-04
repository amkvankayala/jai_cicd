FROM python:3.13-slim

# Python configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy dependency/project configuration first
COPY pyproject.toml .
RUN pip install -e ".[dev]"

# Install the project and dev dependencies
COPY src ./src

# Copy the remaining project files
COPY . .

# FastAPI port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]