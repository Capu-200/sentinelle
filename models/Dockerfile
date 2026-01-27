# Dockerfile pour le ML Engine (Cloud Run Service)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + gsutil (via gcloud CLI)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install gcloud CLI (pour gsutil)
RUN curl https://sdk.cloud.google.com | bash
ENV PATH="$PATH:/root/google-cloud-sdk/bin"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/artifacts

# Set environment variables
ENV ARTIFACTS_DIR=/app/artifacts
ENV MODEL_VERSION=latest
ENV BUCKET_NAME=""

# Script de démarrage qui télécharge les modèles depuis GCS si nécessaire
RUN echo '#!/bin/bash\n\
set -e\n\
if [ -n "$BUCKET_NAME" ] && [ -n "$MODEL_VERSION" ]; then\n\
  echo "📥 Téléchargement des modèles depuis Cloud Storage..."\n\
  /app/scripts/download-artifacts.sh "$MODEL_VERSION" "$BUCKET_NAME" "$ARTIFACTS_DIR" || echo "⚠️  Erreur lors du téléchargement, utilisation des modèles locaux si présents"\n\
fi\n\
echo "🚀 Démarrage du ML Engine..."\n\
exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Make scripts executable
RUN chmod +x scripts/*.sh 2>/dev/null || true

# Default command: run API
CMD ["/app/entrypoint.sh"]

