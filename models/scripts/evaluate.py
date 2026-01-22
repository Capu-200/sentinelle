"""
Script d'évaluation des modèles.

Calcule les métriques (PR-AUC, Recall, Precision) et calibre les seuils.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# TODO: Implémenter l'évaluation
# from src.models.supervised import SupervisedPredictor
# from src.models.unsupervised import UnsupervisedPredictor
# from src.scoring.scorer import GlobalScorer
# from src.scoring.decision import DecisionEngine


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Évaluation des modèles")
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts/latest"),
        help="Dossier contenant les artefacts du modèle",
    )
    parser.add_argument(
        "--test-data",
        type=Path,
        required=True,
        help="Chemin vers les données de test",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Chemin où sauvegarder les résultats d'évaluation",
    )

    args = parser.parse_args()

    print(f"📊 Évaluation des modèles")
    print(f"💾 Artefacts : {args.artifacts_dir}")
    print(f"📁 Données de test : {args.test_data}")

    # TODO: Implémenter l'évaluation
    # 1. Charger les modèles
    # 2. Charger les données de test
    # 3. Calculer les prédictions
    # 4. Calculer les métriques (PR-AUC, Recall, Precision)
    # 5. Calibrer les seuils (BLOCK/REVIEW)
    # 6. Sauvegarder les résultats

    print("✅ Évaluation terminée")


if __name__ == "__main__":
    main()
