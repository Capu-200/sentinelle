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
    train_split_date: str,
    val_split_date: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prépare les données pour l'entraînement avec split temporel.

    Args:
        data_path: Chemin vers le fichier de données nettoyées
        train_split_date: Date de fin du set d'entraînement (ISO format)
        val_split_date: Date de fin du set de validation (ISO format)

    Returns:
        Tuple de (train_df, val_df, test_df)

    TODO:
        - Charger les données nettoyées
        - Split temporel basé sur created_at
        - Validation des splits (pas de leakage temporel)
        - Retourner les trois datasets
    """
    # TODO: Implémenter le split temporel
    # - Charger les données
    # - Convertir created_at en datetime
    # - Split temporel
    # - Validation

    train_df = pd.DataFrame()
    val_df = pd.DataFrame()
    test_df = pd.DataFrame()

    return train_df, val_df, test_df
