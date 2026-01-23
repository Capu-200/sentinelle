#!/bin/bash
# Script de déploiement sur Cloud Run
# Usage: ./scripts/deploy-cloud-run.sh [PROJECT_ID] [SERVICE_NAME] [REGION] [CLOUD_SQL_INSTANCE]

set -e

PROJECT_ID=${1:-"your-project-id"}
SERVICE_NAME=${2:-"sentinelle-api"}
REGION=${3:-"europe-west1"}
CLOUD_SQL_INSTANCE=${4:-"sentinelle-db"}

echo "🚀 Déploiement sur Cloud Run..."

# Vérifier si le projet existe
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
    echo "❌ Erreur: Le projet $PROJECT_ID n'existe pas ou vous n'avez pas les permissions"
    exit 1
fi

# Définir le projet actif
gcloud config set project "$PROJECT_ID"

# Obtenir le nom de connexion Cloud SQL
CONNECTION_NAME=$(gcloud sql instances describe "$CLOUD_SQL_INSTANCE" \
    --project="$PROJECT_ID" \
    --format="value(connectionName)")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Erreur: Impossible de trouver l'instance Cloud SQL $CLOUD_SQL_INSTANCE"
    exit 1
fi

echo "📦 Construction et déploiement de l'image Docker..."

# Activer les APIs nécessaires
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    --project="$PROJECT_ID"

# Se déplacer dans le dossier backend
cd "$(dirname "$0")/../backend" || exit 1

# Demander le mot de passe de la base de données
read -sp "Entrez le mot de passe de la base de données: " DB_PASSWORD
echo ""

# Déployer sur Cloud Run
# Note: Pour utiliser Secret Manager, décommentez les lignes --set-secrets
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --add-cloudsql-instances="$CONNECTION_NAME" \
    --set-env-vars="DATABASE_URL=postgresql+psycopg2://fraud_user:$DB_PASSWORD@/fraud_db?host=/cloudsql/$CONNECTION_NAME" \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --max-instances=10 \
    --project="$PROJECT_ID"

# Alternative avec Secret Manager (plus sécurisé):
# --set-secrets="DB_PASSWORD=db-password:latest,DB_NAME=db-name:latest" \
# --set-env-vars="DATABASE_URL=postgresql+psycopg2://fraud_user:\${DB_PASSWORD}@/\${DB_NAME}?host=/cloudsql/$CONNECTION_NAME" \

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "📋 Pour obtenir l'URL du service:"
echo "   gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'"
echo ""

