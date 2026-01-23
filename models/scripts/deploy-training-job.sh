#!/bin/bash
# Script de déploiement de l'entraînement sur Cloud Run Jobs
# Usage: ./scripts/deploy-training-job.sh [PROJECT_ID] [JOB_NAME] [REGION] [VERSION]

set -e

PROJECT_ID=${1:-"sentinelle-485209"}
JOB_NAME=${2:-"sentinelle-training"}
REGION=${3:-"europe-west1"}
VERSION=${4:-"1.0.0"}

echo "🚀 Déploiement de l'entraînement sur Cloud Run Jobs..."
echo "   Projet: $PROJECT_ID"
echo "   Job: $JOB_NAME"
echo "   Région: $REGION"
echo "   Version: $VERSION"

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
    storage-api.googleapis.com \
    --project="$PROJECT_ID"

# Se déplacer dans le dossier models
cd "$(dirname "$0")/.." || exit 1

# Vérifier que les données existent
DATA_DIR="Data/processed"
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ Erreur: Le dossier $DATA_DIR n'existe pas"
    echo "   Exécutez d'abord: python scripts/clean_data.py"
    exit 1
fi

# Créer un Cloud Storage bucket pour les données (si n'existe pas)
BUCKET_NAME="${PROJECT_ID}-ml-data"
if ! gsutil ls -b "gs://$BUCKET_NAME" &>/dev/null 2>&1; then
    echo "📦 Création du bucket Cloud Storage..."
    gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$BUCKET_NAME"
    echo "   ✅ Bucket créé: gs://$BUCKET_NAME"
else
    echo "   ✅ Bucket existe déjà: gs://$BUCKET_NAME"
fi

# Uploader les données vers Cloud Storage
echo "📤 Upload des données vers Cloud Storage..."
echo "   Cela peut prendre quelques minutes..."
gsutil -m cp "$DATA_DIR"/*.csv "gs://$BUCKET_NAME/data/" 2>&1 | grep -E "(Copying|/)" || true
echo "   ✅ Données uploadées"

# Créer un .dockerignore pour exclure les gros fichiers
cat > .dockerignore << 'EOF'
Data/raw/*
Data/processed/*.csv
artifacts/*
__pycache__
*.pyc
.git
*.md
tests/
EOF

# Déployer le job Cloud Run avec le Dockerfile.training
echo "📦 Construction et déploiement du job..."
echo "   Cela peut prendre 5-10 minutes (première fois)..."

# Renommer temporairement Dockerfile.training en Dockerfile pour le build
if [ -f "Dockerfile.training" ]; then
    mv Dockerfile Dockerfile.api 2>/dev/null || true
    cp Dockerfile.training Dockerfile
fi

gcloud run jobs deploy "$JOB_NAME" \
    --source . \
    --region="$REGION" \
    --set-env-vars="DATA_DIR=/app/data,ARTIFACTS_DIR=/app/artifacts,BUCKET_NAME=$BUCKET_NAME,VERSION=$VERSION" \
    --memory=16Gi \
    --cpu=8 \
    --task-timeout=7200 \
    --max-retries=1 \
    --project="$PROJECT_ID" \
    --quiet

# Restaurer le Dockerfile original
if [ -f "Dockerfile.api" ]; then
    mv Dockerfile.api Dockerfile
fi

echo ""
echo "✅ Job créé!"
echo ""
echo "📋 Pour lancer l'entraînement:"
echo "   gcloud run jobs execute $JOB_NAME --region=$REGION --project=$PROJECT_ID"
echo ""
echo "📊 Pour suivre les logs en temps réel:"
echo "   gcloud run jobs executions list --job=$JOB_NAME --region=$REGION --project=$PROJECT_ID --limit=1"
echo "   gcloud run jobs executions logs read <EXECUTION_NAME> --region=$REGION --project=$PROJECT_ID"
echo ""
echo "💾 Les artefacts seront sauvegardés dans:"
echo "   gs://$BUCKET_NAME/artifacts/"

