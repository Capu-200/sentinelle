"""
Prédiction avec le modèle supervisé.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from ..base import BaseModel
from .train import SupervisedModel


class SupervisedPredictor:
    """Prédicteur pour le modèle supervisé."""

    def __init__(self, model_path: Path | None = None, model: SupervisedModel | None = None):
        """
        Initialise le prédicteur.

        Args:
            model_path: Chemin vers le modèle sauvegardé
            model: Instance de modèle (alternative à model_path)
        """
        if model:
            self.model = model
        elif model_path:
            self.model = SupervisedModel()
            self.model.load(model_path)
        else:
            raise ValueError("Il faut fournir model_path ou model")

    def predict(self, features: Dict[str, Any] | pd.DataFrame) -> float:
        """
        Prédit la probabilité de fraude pour une transaction.

        Args:
            features: Features de la transaction (dict ou DataFrame)

        Returns:
            Probabilité de fraude [0,1]
        """
        # Convertir dict en DataFrame si nécessaire
        if isinstance(features, dict):
            df = pd.DataFrame([features])
        else:
            df = features

        # Prédire
        predictions = self.model.predict(df)
        return float(predictions.iloc[0] if isinstance(predictions, pd.Series) else predictions[0])
