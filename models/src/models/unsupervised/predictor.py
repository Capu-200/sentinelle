"""
Prédiction avec le modèle non supervisé.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from .train import UnsupervisedModel


class UnsupervisedPredictor:
    """Prédicteur pour le modèle non supervisé."""

    def __init__(self, model_path: Path | None = None, model: UnsupervisedModel | None = None):
        """
        Initialise le prédicteur.

        Args:
            model_path: Chemin vers le modèle sauvegardé
            model: Instance de modèle (alternative à model_path)
        """
        if model:
            self.model = model
        elif model_path:
            self.model = UnsupervisedModel()
            self.model.load(model_path)
        else:
            raise ValueError("Il faut fournir model_path ou model")

    def predict(self, features: Dict[str, Any] | pd.DataFrame) -> float:
        """
        Prédit le score d'anomalie calibré pour une transaction.

        Args:
            features: Features de la transaction (dict ou DataFrame)

        Returns:
            Score d'anomalie calibré [0,1]
        """
        # Convertir dict en DataFrame si nécessaire
        if isinstance(features, dict):
            df = pd.DataFrame([features])
        else:
            df = features

        # Prédire
        predictions = self.model.predict(df)
        return float(predictions.iloc[0] if isinstance(predictions, pd.Series) else predictions[0])
