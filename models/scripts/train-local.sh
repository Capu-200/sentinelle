#!/bin/bash
# Script d'entraînement local optimisé
# Usage: ./scripts/train-local.sh [VERSION] [DATA_DIR] [ARTIFACTS_DIR]

set -e

VERSION=${1:-"1.0.0"}
DATA_DIR=${2:-"Data/processed"}
ARTIFACTS_DIR=${3:-"artifacts"}

echo "🚀 Entraînement LOCAL des modèles ML"
echo "   Version: $VERSION"
echo "   Données: $DATA_DIR"
echo "   Artefacts: $ARTIFACTS_DIR"
echo ""

# Vérifier que les données existent
if [ ! -f "$DATA_DIR/paysim_mapped.csv" ]; then
    echo "❌ Erreur: $DATA_DIR/paysim_mapped.csv non trouvé"
    exit 1
fi

if [ ! -f "$DATA_DIR/payon_legit_clean.csv" ]; then
    echo "❌ Erreur: $DATA_DIR/payon_legit_clean.csv non trouvé"
    exit 1
fi

# Créer le dossier artifacts si nécessaire
mkdir -p "$ARTIFACTS_DIR"

# Détecter la commande Python (python3 ou python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Erreur: python3 ou python non trouvé"
    echo "   Installez Python 3.11+ ou activez votre environnement virtuel"
    exit 1
fi

# Lancer l'entraînement en mode local (dataset complet, tous les cores)
echo "📊 Démarrage de l'entraînement LOCAL..."
echo "   💡 Mode local: dataset complet, pas d'échantillonnage"
echo "   💡 Utilise tous les cores disponibles"
echo "   💡 Python: $PYTHON_CMD"
echo ""

$PYTHON_CMD scripts/train.py \
    --data-dir "$DATA_DIR" \
    --artifacts-dir "$ARTIFACTS_DIR" \
    --version "$VERSION" \
    --local

echo ""
echo "✅ Entraînement terminé !"
echo "   Artefacts sauvegardés dans: $ARTIFACTS_DIR/v$VERSION/"
echo ""
echo "📤 Pour uploader vers Cloud Storage:"
echo "   ./scripts/upload-artifacts.sh $VERSION"
