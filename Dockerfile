FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr for clean logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default command for the web service (runs migrations then starts API across 4 different workers)
# each worker is still a separate process with its own SQLAlchemy connection poo
CMD ["sh", "-c", "alembic upgrade head && gunicorn main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:${PORT:-8000}"]