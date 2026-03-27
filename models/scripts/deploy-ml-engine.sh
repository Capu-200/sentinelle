#!/bin/bash
# Script de déploiement du ML Engine sur Cloud Run
# Usage: ./scripts/deploy-ml-engine.sh [PROJECT_ID] [SERVICE_NAME] [REGION] [MODEL_VERSION]

set -e

PROJECT_ID=${1:-"sentinelle-485209"}
SERVICE_NAME=${2:-"sentinelle-ml-engine-v2"}
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

# Se déplacer dans le dossier models (contexte de build = ce dossier)
MODELS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$MODELS_DIR" || exit 1
echo "   Contexte de build: $MODELS_DIR"

# Bucket Cloud Storage pour les artefacts
BUCKET_NAME="${PROJECT_ID}-ml-data"

# Créer un .dockerignore temporaire pour exclure les gros fichiers
cat > .dockerignore << 'EOF'
Data/raw/*
*.csv
artifacts/*
__pycache__
*.pyc
.git
Dockerfile.training
EOF

# Renommer temporairement Dockerfile.api en Dockerfile pour le build
if [ -f "Dockerfile.api" ]; then
    mv Dockerfile Dockerfile.training 2>/dev/null || true
    cp Dockerfile.api Dockerfile
fi

# Déployer sur Cloud Run
echo "📦 Construction et déploiement de l'image Docker..."
echo "   Les modèles seront téléchargés depuis gs://$BUCKET_NAME/artifacts/ au démarrage"
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="MODEL_VERSION=$MODEL_VERSION,ARTIFACTS_DIR=/app/artifacts,BUCKET_NAME=$BUCKET_NAME,MONITORING_GCS_BUCKET=$BUCKET_NAME,MONITORING_SAMPLE_RATE=0.1" \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --min-instances=0 \
    --project="$PROJECT_ID"

# Restaurer le Dockerfile original
if [ -f "Dockerfile.training" ]; then
    mv Dockerfile.training Dockerfile
fi

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

