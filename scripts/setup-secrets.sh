#!/bin/bash
# Script pour créer les secrets dans Google Cloud Secret Manager
# Usage: ./scripts/setup-secrets.sh [PROJECT_ID] [DB_PASSWORD] [DB_NAME]

set -e

PROJECT_ID=${1:-"your-project-id"}
DB_PASSWORD=${2:-""}
DB_NAME=${3:-"fraud_db"}

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Erreur: Vous devez fournir un mot de passe"
    echo "Usage: $0 [PROJECT_ID] [DB_PASSWORD] [DB_NAME]"
    exit 1
fi

echo "🔐 Configuration des secrets dans Secret Manager..."

# Définir le projet actif
gcloud config set project "$PROJECT_ID"

# Activer l'API Secret Manager
gcloud services enable secretmanager.googleapis.com --project="$PROJECT_ID"

# Créer le secret pour le mot de passe de la base de données
echo -n "$DB_PASSWORD" | gcloud secrets create db-password \
    --data-file=- \
    --replication-policy="automatic" \
    --project="$PROJECT_ID" \
    2>/dev/null || echo -n "$DB_PASSWORD" | gcloud secrets versions add db-password \
    --data-file=- \
    --project="$PROJECT_ID"

# Créer le secret pour le nom de la base de données
echo -n "$DB_NAME" | gcloud secrets create db-name \
    --data-file=- \
    --replication-policy="automatic" \
    --project="$PROJECT_ID" \
    2>/dev/null || echo -n "$DB_NAME" | gcloud secrets versions add db-name \
    --data-file=- \
    --project="$PROJECT_ID"

echo ""
echo "✅ Secrets créés avec succès!"
echo ""
echo "📋 Secrets disponibles:"
echo "   - db-password"
echo "   - db-name"
echo ""

