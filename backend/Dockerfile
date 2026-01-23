# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Use environment variable for port (Cloud Run requirement)
ENV PORT=8000

# Run uvicorn
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}