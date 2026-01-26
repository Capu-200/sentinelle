#!/bin/bash
# Script pour télécharger les artefacts depuis Cloud Storage
# Utilisé par le ML Engine au démarrage
# Usage: ./scripts/download-artifacts.sh [VERSION] [BUCKET_NAME] [ARTIFACTS_DIR]

set -e

VERSION=${1:-"latest"}
BUCKET_NAME=${2:-"sentinelle-485209-ml-data"}
ARTIFACTS_DIR=${3:-"artifacts"}

echo "📥 Téléchargement des artefacts depuis Cloud Storage..."
echo "   Version: $VERSION"
echo "   Bucket: gs://$BUCKET_NAME"
echo "   Destination: $ARTIFACTS_DIR"
echo ""

# Vérifier que gsutil est installé
if ! command -v gsutil &> /dev/null; then
    echo "⚠️  gsutil non disponible, les modèles doivent être dans $ARTIFACTS_DIR"
    exit 0
fi

# Créer le dossier artifacts si nécessaire
mkdir -p "$ARTIFACTS_DIR"

# Résoudre "latest" vers la vraie version
if [ "$VERSION" = "latest" ]; then
    # Télécharger le fichier latest.txt s'il existe
    if gsutil -q stat "gs://$BUCKET_NAME/artifacts/latest.txt" 2>/dev/null; then
        VERSION=$(gsutil cat "gs://$BUCKET_NAME/artifacts/latest.txt" | tr -d '\n')
        echo "   📌 Version 'latest' résolue: $VERSION"
    else
        # Chercher la dernière version
        VERSION=$(gsutil ls "gs://$BUCKET_NAME/artifacts/" | grep -o 'v[0-9.]*/$' | sort -V | tail -1 | tr -d '/')
        if [ -z "$VERSION" ]; then
            echo "❌ Aucune version trouvée dans gs://$BUCKET_NAME/artifacts/"
            exit 1
        fi
        echo "   📌 Dernière version trouvée: $VERSION"
    fi
fi

# Normaliser le format (ajouter "v" si absent)
if [[ ! "$VERSION" =~ ^v ]]; then
    VERSION="v$VERSION"
fi

# Vérifier si la version existe déjà localement
if [ -d "$ARTIFACTS_DIR/$VERSION" ]; then
    echo "✅ Version $VERSION déjà présente localement"
    exit 0
fi

# Télécharger la version depuis GCS
echo "📥 Téléchargement de $VERSION depuis gs://$BUCKET_NAME/artifacts/$VERSION/..."
gsutil -m cp -r "gs://$BUCKET_NAME/artifacts/$VERSION" "$ARTIFACTS_DIR/"

# Créer le symlink latest si nécessaire
if [ ! -L "$ARTIFACTS_DIR/latest" ] && [ ! -e "$ARTIFACTS_DIR/latest" ]; then
    echo "🔗 Création du symlink latest → $VERSION"
    ln -s "$VERSION" "$ARTIFACTS_DIR/latest"
fi

echo ""
echo "✅ Artefacts téléchargés !"
echo "   Disponibles dans: $ARTIFACTS_DIR/$VERSION/"

