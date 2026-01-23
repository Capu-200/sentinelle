#!/bin/bash
# Script de déploiement de Cloud SQL
# Usage: ./scripts/deploy-cloud-sql.sh [PROJECT_ID] [INSTANCE_NAME] [DATABASE_NAME] [USER_NAME] [PASSWORD]

set -e

PROJECT_ID=${1:-"your-project-id"}
INSTANCE_NAME=${2:-"sentinelle-db"}
DATABASE_NAME=${3:-"fraud_db"}
DB_USER=${4:-"fraud_user"}
DB_PASSWORD=${5:-""}

REGION="europe-west1"
TIER="db-f1-micro"  # Instance de base pour développement (peut être changé)

echo "🚀 Création de l'instance Cloud SQL PostgreSQL..."

# Vérifier si le projet existe
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
    echo "❌ Erreur: Le projet $PROJECT_ID n'existe pas ou vous n'avez pas les permissions"
    exit 1
fi

# Définir le projet actif
gcloud config set project "$PROJECT_ID"

# Activer l'API Cloud SQL Admin (nécessaire pour créer des instances)
echo "🔧 Activation de l'API Cloud SQL Admin..."
gcloud services enable sqladmin.googleapis.com --project="$PROJECT_ID" 2>/dev/null || echo "⚠️  API déjà activée ou erreur (peut être ignorée)"

# Vérifier si l'instance existe déjà
if gcloud sql instances describe "$INSTANCE_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "⚠️  L'instance $INSTANCE_NAME existe déjà. Passage à la configuration..."
else
    echo "📦 Création de l'instance Cloud SQL..."
    gcloud sql instances create "$INSTANCE_NAME" \
        --database-version=POSTGRES_15 \
        --tier="$TIER" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup-start-time=03:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=04 \
        --maintenance-release-channel=production \
        --no-deletion-protection
fi

# Créer la base de données si elle n'existe pas
echo "📊 Création de la base de données $DATABASE_NAME..."
gcloud sql databases create "$DATABASE_NAME" \
    --instance="$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    2>/dev/null || echo "⚠️  La base de données existe déjà ou erreur (peut être ignorée)"

# Créer l'utilisateur si le mot de passe est fourni
if [ -n "$DB_PASSWORD" ]; then
    echo "👤 Création de l'utilisateur $DB_USER..."
    gcloud sql users create "$DB_USER" \
        --instance="$INSTANCE_NAME" \
        --password="$DB_PASSWORD" \
        --project="$PROJECT_ID" \
        2>/dev/null || echo "⚠️  L'utilisateur existe déjà, mise à jour du mot de passe..."
    
    # Mettre à jour le mot de passe si l'utilisateur existe
    gcloud sql users set-password "$DB_USER" \
        --instance="$INSTANCE_NAME" \
        --password="$DB_PASSWORD" \
        --project="$PROJECT_ID" \
        2>/dev/null || true
fi

# Obtenir le nom de connexion
CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --format="value(connectionName)")

echo ""
echo "✅ Instance Cloud SQL créée avec succès!"
echo ""
echo "📋 Informations de connexion:"
echo "   Instance: $INSTANCE_NAME"
echo "   Base de données: $DATABASE_NAME"
echo "   Utilisateur: $DB_USER"
echo "   Connection Name: $CONNECTION_NAME"
echo ""
echo "🔗 Pour se connecter localement, utilisez Cloud SQL Auth Proxy:"
echo "   cloud-sql-proxy $CONNECTION_NAME"
echo ""
echo "💡 URL de connexion pour Cloud Run (Unix socket):"
echo "   postgresql+psycopg2://$DB_USER:$DB_PASSWORD@/$DATABASE_NAME?host=/cloudsql/$CONNECTION_NAME"
echo ""

