#!/usr/bin/env python3
"""
Script de préparation des données pour l'entraînement.

Génère les fichiers attendus dans Data/processed/ :
- paysim_mapped.csv (depuis PaySim raw)
- payon_legit_clean.csv (depuis Payon raw)

Usage:
    python scripts/prepare_data.py
    python scripts/prepare_data.py --paysim Data/raw/mon_fichier.csv --payon Data/raw/mon_payon.csv
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.preparation import map_paysim_to_payon


def main():
    parser = argparse.ArgumentParser(description="Préparer les données pour l'entraînement")
    parser.add_argument(
        "--paysim",
        type=Path,
        default=Path("Data/raw/paysim dataset 2.csv"),
        help="Fichier PaySim brut (CSV avec step, type, amount, nameOrig, nameDest, isFraud)",
    )
    parser.add_argument(
        "--payon",
        type=Path,
        default=Path("Data/raw/dataset_payon_legit.csv"),
        help="Fichier Payon brut (transactions légitimes)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("Data/processed"),
        help="Dossier de sortie",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    # 1. PaySim → paysim_mapped.csv
    if not args.paysim.exists():
        print(f"❌ Fichier PaySim non trouvé: {args.paysim}")
        print("\n📋 Fichiers PaySim attendus dans Data/raw/ :")
        print("   - paysim dataset 2.csv")
        print("   - Ou Dataset_flaged.csv (avec colonnes: step, type, amount, nameOrig, nameDest, isFraud)")
        sys.exit(1)

    map_paysim_to_payon(
        paysim_path=args.paysim,
        output_path=args.out_dir / "paysim_mapped.csv",
    )

    # 2. Payon → payon_legit_clean.csv
    if not args.payon.exists():
        print(f"❌ Fichier Payon non trouvé: {args.payon}")
        print("\n📋 Fichiers Payon attendus dans Data/raw/ :")
        print("   - dataset_payon_legit.csv")
        print("   - Ou dataset_legit_no_status.csv")
        sys.exit(1)

    payon_out = args.out_dir / "payon_legit_clean.csv"
    shutil.copy(args.payon, payon_out)
    print(f"✅ Payon copié: {args.payon} → {payon_out}")

    print("\n" + "=" * 50)
    print("✅ Préparation terminée !")
    print(f"   {args.out_dir}/paysim_mapped.csv")
    print(f"   {args.out_dir}/payon_legit_clean.csv")
    print("\n💡 Lancer l'entraînement :")
    print("   ./scripts/train-test.sh 2.0.1-mlflow 50000")
    print("   ou: ./scripts/train-local.sh 2.0.1-mlflow")


if __name__ == "__main__":
    main()
