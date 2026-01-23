# Dockerfile pour l'entraînement (Cloud Run Jobs)
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
RUN mkdir -p /app/data /app/artifacts

# Set working directory for data
ENV DATA_DIR=/app/data
ENV ARTIFACTS_DIR=/app/artifacts

# Script d'entraînement qui télécharge les données depuis GCS
RUN echo '#!/bin/bash\n\
set -e\n\
echo "📥 Téléchargement des données depuis Cloud Storage..."\n\
if [ -n "$BUCKET_NAME" ]; then\n\
  gsutil -m cp "gs://${BUCKET_NAME}/data/*.csv" /app/data/ 2>&1 || echo "⚠️  Erreur lors du téléchargement"\n\
fi\n\
echo "🚀 Lancement de l'\''entraînement..."\n\
python scripts/train.py --data-dir /app/data --artifacts-dir /app/artifacts --version ${VERSION:-1.0.0}\n\
echo "📤 Upload des artefacts vers Cloud Storage..."\n\
if [ -n "$BUCKET_NAME" ]; then\n\
  gsutil -m cp -r /app/artifacts/* "gs://${BUCKET_NAME}/artifacts/" 2>&1 || echo "⚠️  Erreur lors de l'\''upload"\n\
fi\n\
echo "✅ Entraînement terminé!"' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Default command: run training script
CMD ["/app/entrypoint.sh"]

