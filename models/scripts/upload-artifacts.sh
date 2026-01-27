#!/bin/bash
# Script pour uploader les artefacts vers Cloud Storage
# Usage: ./scripts/upload-artifacts.sh [VERSION] [BUCKET_NAME] [ARTIFACTS_DIR]

set -e

VERSION=${1:-"1.0.0"}
BUCKET_NAME=${2:-"sentinelle-485209-ml-data"}
ARTIFACTS_DIR=${3:-"artifacts"}
PROJECT_ID=${4:-"sentinelle-485209"}

echo "📤 Upload des artefacts vers Cloud Storage"
echo "   Version: $VERSION"
echo "   Bucket: gs://$BUCKET_NAME"
echo "   Artefacts locaux: $ARTIFACTS_DIR"
echo ""

# Vérifier que gsutil est installé
if ! command -v gsutil &> /dev/null; then
    echo "❌ Erreur: gsutil n'est pas installé"
    echo "   Installez Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Vérifier que les artefacts existent
VERSION_DIR="$ARTIFACTS_DIR/v$VERSION"
if [ ! -d "$VERSION_DIR" ]; then
    echo "❌ Erreur: $VERSION_DIR non trouvé"
    echo "   Lancez d'abord l'entraînement: ./scripts/train-local.sh $VERSION"
    exit 1
fi

# Vérifier l'authentification
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Erreur: Non authentifié avec Google Cloud"
    echo "   Lancez: gcloud auth login"
    exit 1
fi

# Créer le bucket s'il n'existe pas
echo "🔍 Vérification du bucket..."
if ! gsutil ls -b "gs://$BUCKET_NAME" &>/dev/null; then
    echo "📦 Création du bucket gs://$BUCKET_NAME..."
    gsutil mb -p "$PROJECT_ID" -l europe-west1 "gs://$BUCKET_NAME" || true
fi

# Upload des artefacts
echo ""
echo "📤 Upload des artefacts..."
gsutil -m cp -r "$VERSION_DIR" "gs://$BUCKET_NAME/artifacts/"

# Upload du symlink latest si présent
if [ -L "$ARTIFACTS_DIR/latest" ]; then
    echo "📤 Upload du symlink latest..."
    LATEST_TARGET=$(readlink "$ARTIFACTS_DIR/latest")
    # Créer un fichier texte avec la version cible
    echo "$LATEST_TARGET" > /tmp/latest.txt
    gsutil cp /tmp/latest.txt "gs://$BUCKET_NAME/artifacts/latest.txt"
    rm /tmp/latest.txt
fi

echo ""
echo "✅ Upload terminé !"
echo ""
echo "📊 Artefacts disponibles dans:"
echo "   gs://$BUCKET_NAME/artifacts/v$VERSION/"
echo ""
echo "🔧 Le ML Engine chargera automatiquement ces modèles au prochain démarrage"
