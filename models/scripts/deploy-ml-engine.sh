#!/bin/bash
# Script de déploiement du ML Engine sur Cloud Run
# Usage: ./scripts/deploy-ml-engine.sh [PROJECT_ID] [SERVICE_NAME] [REGION] [MODEL_VERSION]

set -e

PROJECT_ID=${1:-"sentinelle-485209"}
SERVICE_NAME=${2:-"sentinelle-ml-engine"}
REGION=${3:-"europe-west1"}
MODEL_VERSION=${4:-"latest"}

echo "🚀 Déploiement du ML Engine sur Cloud Run..."
echo "   Projet: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Région: $REGION"
echo "   Version modèle: $MODEL_VERSION"

# Vérifier si le projet existe
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
    echo "❌ Erreur: Le projet $PROJECT_ID n'existe pas ou vous n'avez pas les permissions"
    exit 1
fi

# Définir le projet actif
gcloud config set project "$PROJECT_ID"

# Activer les APIs nécessaires
echo "🔧 Activation des APIs..."
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project="$PROJECT_ID"

# Se déplacer dans le dossier models
cd "$(dirname "$0")/.." || exit 1

# Vérifier que les artefacts existent
ARTIFACTS_DIR="artifacts"
if [ ! -d "$ARTIFACTS_DIR" ]; then
    echo "❌ Erreur: Le dossier $ARTIFACTS_DIR n'existe pas"
    echo "   Exécutez d'abord: python scripts/train.py --version 1.0.0"
    exit 1
fi

# Déployer sur Cloud Run
echo "📦 Construction et déploiement de l'image Docker..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="MODEL_VERSION=$MODEL_VERSION,ARTIFACTS_DIR=/app/artifacts" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0 \
    --project="$PROJECT_ID"

# Obtenir l'URL du service
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(status.url)")

echo ""
echo "✅ Déploiement terminé!"
echo "   URL: $SERVICE_URL"
echo "   Health check: $SERVICE_URL/health"
echo "   Score endpoint: $SERVICE_URL/score"

