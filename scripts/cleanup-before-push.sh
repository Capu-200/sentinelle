#!/bin/bash
# Script pour nettoyer les fichiers avant push GitHub
# Supprime les fichiers volumineux et temporaires du tracking Git

set -e

echo "🧹 Nettoyage avant push GitHub..."
echo ""

# 1. Supprimer les CSV volumineux du tracking
echo "📊 Suppression des fichiers CSV volumineux du tracking..."
git rm --cached models/Data/raw/*.csv 2>/dev/null || echo "   ℹ️  Aucun CSV raw tracké"
git rm --cached models/Data/processed/*.csv 2>/dev/null || echo "   ℹ️  Aucun CSV processed tracké"
echo "   ✅ CSV supprimés du tracking (restent localement)"

# 2. Supprimer les __pycache__ du tracking
echo ""
echo "🗑️  Suppression des __pycache__ du tracking..."
find . -type d -name __pycache__ | while read dir; do
    git rm -r --cached "$dir" 2>/dev/null || true
done
echo "   ✅ __pycache__ supprimés du tracking"

# 3. Supprimer les .pkl du tracking
echo ""
echo "🤖 Suppression des modèles ML (.pkl) du tracking..."
git rm --cached models/artifacts/*.pkl 2>/dev/null || echo "   ℹ️  Aucun .pkl tracké"
echo "   ✅ Modèles ML supprimés du tracking"

# 4. Supprimer venv du tracking (si tracké)
echo ""
echo "🐍 Vérification du venv..."
if git ls-files | grep -q "backend/venv/"; then
    git rm -r --cached backend/venv/ 2>/dev/null || true
    echo "   ✅ venv supprimé du tracking"
else
    echo "   ℹ️  venv non tracké (déjà ignoré)"
fi

echo ""
echo "✅ Nettoyage terminé !"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. Vérifier : git status"
echo "   2. Ajouter : git add ."
echo "   3. Commit : git commit -m 'feat: Intégration ML Engine + nettoyage'"
echo "   4. Push : git push origin main"
echo ""

