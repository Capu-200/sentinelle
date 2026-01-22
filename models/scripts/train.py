"""
Script principal d'entraînement du pipeline ML complet.

Orchestre :
1. Nettoyage des données
2. Préparation (split temporel)
3. Feature engineering
4. Entraînement supervisé
5. Entraînement non supervisé
6. Calibration des seuils
7. Sauvegarde des artefacts
"""

from __future__ import annotations

import argparse
from pathlib import Path

# TODO: Implémenter le pipeline complet
# from src.data.preparation import prepare_training_data
# from src.features.pipeline import FeaturePipeline
# from src.models.supervised import train_supervised_model
# from src.models.unsupervised import train_unsupervised_model
# from src.utils.versioning import save_artifacts


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Entraînement du pipeline ML")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("Data/processed"),
        help="Dossier contenant les données nettoyées",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("configs"),
        help="Dossier contenant les configurations",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts"),
        help="Dossier où sauvegarder les artefacts",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1.0.0",
        help="Version du modèle (SemVer)",
    )
    parser.add_argument(
        "--train-split-date",
        type=str,
        help="Date de fin du set d'entraînement (ISO format)",
    )
    parser.add_argument(
        "--val-split-date",
        type=str,
        help="Date de fin du set de validation (ISO format)",
    )

    args = parser.parse_args()

    print(f"🚀 Démarrage de l'entraînement (version {args.version})")
    print(f"📁 Données : {args.data_dir}")
    print(f"⚙️  Config : {args.config_dir}")
    print(f"💾 Artefacts : {args.artifacts_dir}")

    # TODO: Implémenter le pipeline
    # 1. Charger les données nettoyées
    # 2. Préparer les splits (train/val/test)
    # 3. Feature engineering
    # 4. Entraîner modèle supervisé
    # 5. Entraîner modèle non supervisé
    # 6. Calibrer les seuils
    # 7. Sauvegarder les artefacts

    print("✅ Entraînement terminé")


if __name__ == "__main__":
    main()
