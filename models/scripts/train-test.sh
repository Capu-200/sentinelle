#!/bin/bash
# Script d'entraînement en mode TEST (dataset limité)
# Usage: ./scripts/train-test.sh [VERSION] [TEST_SIZE] [DATA_DIR] [ARTIFACTS_DIR]

set -e

VERSION=${1:-"1.0.0-test"}
TEST_SIZE=${2:-"300000"}
DATA_DIR=${3:-"Data/processed"}
ARTIFACTS_DIR=${4:-"artifacts"}

echo "🧪 Entraînement en MODE TEST"
echo "   Version: $VERSION"
echo "   Taille test: $TEST_SIZE transactions (les plus récentes)"
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

# Détecter la commande python
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Erreur: Python non trouvé. Veuillez installer Python 3."
    exit 1
fi

# Lancer l'entraînement en mode test
echo "📊 Démarrage de l'entraînement TEST..."
echo "   💡 Mode test: $TEST_SIZE transactions PaySim + Payon (les plus récentes)"
echo "   💡 Utilise tous les cores disponibles"
echo ""

"$PYTHON_CMD" scripts/train.py \
    --data-dir "$DATA_DIR" \
    --artifacts-dir "$ARTIFACTS_DIR" \
    --version "$VERSION" \
    --local \
    --test-size "$TEST_SIZE"

echo ""
echo "✅ Entraînement TEST terminé !"
echo "   Artefacts sauvegardés dans: $ARTIFACTS_DIR/v$VERSION/"
echo ""
echo "💡 Pour l'entraînement complet (sans --test-size):"
echo "   ./scripts/train-local.sh 1.0.0"

