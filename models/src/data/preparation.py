"""
Pipeline de préparation des données pour l'entraînement.

Ce module gère le split temporel, la validation, et la préparation
des datasets pour l'entraînement des modèles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


def prepare_training_data(
    data_path: Path,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prépare les données pour l'entraînement avec split temporel.

    Args:
        data_path: Chemin vers le fichier de données nettoyées
        train_ratio: Proportion pour l'entraînement (défaut: 0.7)
        val_ratio: Proportion pour la validation (défaut: 0.15)
        test_ratio: Proportion pour le test (défaut: 0.15)

    Returns:
        Tuple de (train_df, val_df, test_df)

    Raises:
        ValueError: Si les ratios ne somment pas à 1.0
        FileNotFoundError: Si le fichier de données n'existe pas
    """
    # Validation des ratios
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError(
            f"Les ratios doivent sommer à 1.0, reçu: "
            f"train={train_ratio}, val={val_ratio}, test={test_ratio}"
        )

    # Charger les données
    if not data_path.exists():
        raise FileNotFoundError(f"Fichier de données non trouvé: {data_path}")

    print(f"📊 Chargement des données depuis {data_path}...")
    df = pd.read_csv(data_path)

    print(f"   ✅ {len(df)} transactions chargées")

    # Convertir created_at en datetime si ce n'est pas déjà fait
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
        # Trier par date pour le split temporel
        df = df.sort_values("created_at").reset_index(drop=True)
    else:
        raise ValueError("Colonne 'created_at' manquante dans les données")

    # Validation : vérifier qu'il n'y a pas de valeurs manquantes dans created_at
    if df["created_at"].isna().any():
        n_missing = df["created_at"].isna().sum()
        print(f"   ⚠️  {n_missing} transactions avec created_at manquant, suppression...")
        df = df.dropna(subset=["created_at"])

    # Split temporel
    n_total = len(df)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)
    # Le reste va au test

    train_df = df.iloc[:n_train].copy()
    val_df = df.iloc[n_train : n_train + n_val].copy()
    test_df = df.iloc[n_train + n_val :].copy()

    print(f"\n📊 Split temporel:")
    print(f"   Train: {len(train_df)} transactions ({len(train_df)/n_total*100:.1f}%)")
    print(f"      Période: {train_df['created_at'].min()} → {train_df['created_at'].max()}")
    print(f"   Val:   {len(val_df)} transactions ({len(val_df)/n_total*100:.1f}%)")
    print(f"      Période: {val_df['created_at'].min()} → {val_df['created_at'].max()}")
    print(f"   Test:  {len(test_df)} transactions ({len(test_df)/n_total*100:.1f}%)")
    print(f"      Période: {test_df['created_at'].min()} → {test_df['created_at'].max()}")

    # Validation : vérifier qu'il n'y a pas de leakage temporel
    # On permet une égalité exacte (frontière) mais pas de chevauchement
    if len(train_df) > 0 and len(val_df) > 0:
        train_max = train_df["created_at"].max()
        val_min = val_df["created_at"].min()
        # Vérifier qu'il n'y a pas de transactions du train après le début de val
        # On permet l'égalité car c'est la frontière exacte du split
        if train_max > val_min:
            raise ValueError(
                "⚠️  LEAKAGE TEMPOREL DÉTECTÉ: "
                f"Train max ({train_max}) > Val min ({val_min})"
            )
        # Vérifier qu'il n'y a pas de transactions du train dans val
        train_in_val = train_df[train_df["created_at"] == val_min]
        if len(train_in_val) > 0 and len(val_df[val_df["created_at"] == val_min]) > 0:
            # Il y a des transactions avec le même timestamp dans train et val
            # C'est acceptable si c'est juste la frontière, mais on vérifie qu'elles sont bien séparées
            pass  # Acceptable si c'est juste la frontière

    if len(val_df) > 0 and len(test_df) > 0:
        val_max = val_df["created_at"].max()
        test_min = test_df["created_at"].min()
        if val_max > test_min:
            raise ValueError(
                "⚠️  LEAKAGE TEMPOREL DÉTECTÉ: "
                f"Val max ({val_max}) > Test min ({test_min})"
            )

    print("   ✅ Aucun leakage temporel détecté")

    return train_df, val_df, test_df


def map_paysim_to_payon(
    paysim_path: Path,
    max_amount: float | None = None,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """
    Mappe le dataset PaySim vers le format Payon.

    Mapping:
    - step → created_at (step = heures depuis le début, converti en timestamp)
    - type → transaction_type
    - amount → amount (filtré si max_amount spécifié)
    - nameOrig → source_wallet_id
    - nameDest → destination_wallet_id
    - isFraud → label (pour supervisé)
    - Balances (oldbalanceOrg, etc.) → IGNORÉES (pas disponibles en prod)

    Args:
        paysim_path: Chemin vers le fichier PaySim CSV
        max_amount: Montant maximum autorisé (None = pas de filtrage, recommandé pour l'entraînement)
        output_path: Chemin optionnel pour sauvegarder le résultat

    Returns:
        DataFrame au format Payon
    """
    print(f"📊 Mapping PaySim → Payon depuis {paysim_path}...")

    # Charger PaySim
    df = pd.read_csv(paysim_path)

    print(f"   ✅ {len(df)} transactions PaySim chargées")

    # Filtrer les montants si max_amount est spécifié
    if max_amount is not None:
        n_before = len(df)
        df = df[df["amount"] <= max_amount].copy()
        n_filtered = n_before - len(df)
        if n_filtered > 0:
            print(f"   ⚠️  {n_filtered} transactions filtrées (amount > {max_amount})")
    else:
        print(f"   ℹ️  Aucun filtrage sur le montant (toutes les transactions conservées)")

    # Mapping des colonnes
    payon_df = pd.DataFrame()

    # Identifiants
    payon_df["transaction_id"] = [f"paysim_{i}" for i in range(len(df))]
    payon_df["source_wallet_id"] = df["nameOrig"].astype(str)
    payon_df["destination_wallet_id"] = df["nameDest"].astype(str)

    # Montant
    payon_df["amount"] = df["amount"].astype(float)

    # Type de transaction
    payon_df["transaction_type"] = df["type"].astype(str)

    # Direction : dérivée du type PaySim
    # CASH_OUT, DEBIT, TRANSFER → outgoing
    # CASH_IN, PAYMENT → incoming (approximation)
    outgoing_types = {"CASH_OUT", "DEBIT", "TRANSFER"}
    payon_df["direction"] = df["type"].apply(
        lambda x: "outgoing" if x in outgoing_types else "incoming"
    )

    # Timestamp : step = heures depuis le début
    # On crée un timestamp de base et on ajoute les heures
    # Pour éviter les doublons, on ajoute aussi des secondes basées sur l'index
    base_timestamp = pd.Timestamp("2020-01-01 00:00:00", tz="UTC")
    # Créer des timestamps uniques en ajoutant des secondes basées sur l'index
    # On groupe par step et on ajoute des secondes incrémentales pour chaque transaction
    df_sorted = df.sort_values("step").reset_index(drop=True)
    df_sorted["step_rank"] = df_sorted.groupby("step").cumcount()
    payon_df["created_at"] = (
        base_timestamp
        + pd.to_timedelta(df_sorted["step"], unit="h")
        + pd.to_timedelta(df_sorted["step_rank"], unit="s")  # Ajouter des secondes pour différencier
    )

    # Currency : PaySim n'a pas de currency, on ajoute PYC
    payon_df["currency"] = "PYC"

    # Champs optionnels (vides pour PaySim)
    payon_df["provider"] = "PAYSIM"
    payon_df["provider_tx_id"] = None
    payon_df["initiator_user_id"] = payon_df["source_wallet_id"]  # Approximation
    payon_df["country"] = None
    payon_df["city"] = None
    payon_df["description"] = None

    # Label pour supervisé (si présent)
    if "isFraud" in df.columns:
        payon_df["is_fraud"] = df["isFraud"].astype(int)
        print(f"   ✅ Label 'is_fraud' ajouté ({payon_df['is_fraud'].sum()} fraudes)")

    # Trier par created_at
    payon_df = payon_df.sort_values("created_at").reset_index(drop=True)

    print(f"   ✅ {len(payon_df)} transactions mappées au format Payon")

    # Sauvegarder si demandé
    if output_path:
        payon_df.to_csv(output_path, index=False)
        print(f"   💾 Sauvegardé dans {output_path}")

    return payon_df
