#!/bin/bash
# Script pour exécuter les migrations Alembic sur Cloud SQL
# Usage: ./scripts/run-migrations.sh [PROJECT_ID] [INSTANCE_NAME] [DATABASE_NAME] [USER_NAME] [PASSWORD]

set -e

PROJECT_ID=${1:-"your-project-id"}
INSTANCE_NAME=${2:-"sentinelle-db"}
DATABASE_NAME=${3:-"fraud_db"}
DB_USER=${4:-"fraud_user"}
DB_PASSWORD=${5:-""}

echo "🔄 Exécution des migrations Alembic..."

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Erreur: Vous devez fournir un mot de passe"
    echo "Usage: $0 [PROJECT_ID] [INSTANCE_NAME] [DATABASE_NAME] [USER_NAME] [PASSWORD]"
    exit 1
fi

# Obtenir le nom de connexion
CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --format="value(connectionName)")

if [ -z "$CONNECTION_NAME" ]; then
    echo "❌ Erreur: Impossible de trouver l'instance Cloud SQL $INSTANCE_NAME"
    exit 1
fi

# Se déplacer dans le dossier backend
cd "$(dirname "$0")/../backend" || exit 1

# Vérifier si cloud-sql-proxy est installé
if ! command -v cloud-sql-proxy &> /dev/null; then
    echo "⚠️  cloud-sql-proxy n'est pas installé. Installation..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.arm64
        chmod +x cloud-sql-proxy
        export PATH="$PWD:$PATH"
    else
        echo "❌ Veuillez installer cloud-sql-proxy manuellement"
        exit 1
    fi
fi

# Démarrer cloud-sql-proxy en arrière-plan
echo "🔌 Démarrage de Cloud SQL Auth Proxy..."
cloud-sql-proxy "$CONNECTION_NAME" --port=5432 &
PROXY_PID=$!

# Attendre que le proxy soit prêt
sleep 3

# Configurer la variable d'environnement DATABASE_URL
export DATABASE_URL="postgresql+psycopg2://$DB_USER:$DB_PASSWORD@127.0.0.1:5432/$DATABASE_NAME"

# Exécuter les migrations
echo "📊 Exécution des migrations..."
alembic upgrade head

# Arrêter le proxy
kill $PROXY_PID 2>/dev/null || true

echo ""
echo "✅ Migrations exécutées avec succès!"
echo ""

