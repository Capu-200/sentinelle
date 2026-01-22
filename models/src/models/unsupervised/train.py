"""
Entraînement du modèle non supervisé (IsolationForest).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from ..base import BaseModel


class UnsupervisedModel(BaseModel):
    """Modèle non supervisé IsolationForest pour la détection d'anomalies."""

    def __init__(self, model_version: str = "1.0.0", config: Dict[str, Any] | None = None):
        """
        Initialise le modèle non supervisé.

        Args:
            model_version: Version du modèle
            config: Configuration des hyperparamètres
        """
        super().__init__(model_version)
        self.config = config or {}
        self.model = IsolationForest(**self.config)
        self.quantile_mapper = None  # Pour calibration [0,1]

    def train(self, X: pd.DataFrame, y=None, **kwargs) -> None:
        """
        Entraîne le modèle IsolationForest.

        Args:
            X: Features d'entraînement (dataset normal-only)
            y: Non utilisé (modèle non supervisé)
            **kwargs: Arguments additionnels
        """
        # Entraîner le modèle
        self.model.fit(X)

        # Calibrer les scores vers [0,1] via quantiles
        train_scores = self.model.score_samples(X)
        self.quantile_mapper = {
            "min": float(np.min(train_scores)),
            "max": float(np.max(train_scores)),
        }

        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        Prédit le score d'anomalie calibré [0,1].

        Args:
            X: Features à prédire

        Returns:
            Scores d'anomalie calibrés [0,1]
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant la prédiction")

        # Scores bruts (négatifs = anomalie)
        raw_scores = self.model.score_samples(X)

        # Calibration vers [0,1] via quantile mapping
        if self.quantile_mapper:
            min_score = self.quantile_mapper["min"]
            max_score = self.quantile_mapper["max"]
            # Normaliser et inverser (anomalie = score élevé)
            calibrated = 1.0 - (raw_scores - min_score) / (max_score - min_score)
            calibrated = np.clip(calibrated, 0.0, 1.0)
        else:
            calibrated = raw_scores

        return pd.Series(calibrated)

    def save(self, path: Path) -> None:
        """Sauvegarde le modèle."""
        import pickle

        with open(path, "wb") as f:
            pickle.dump(
                {
                    "model": self.model,
                    "quantile_mapper": self.quantile_mapper,
                },
                f,
            )

    def load(self, path: Path) -> None:
        """Charge le modèle."""
        import pickle

        with open(path, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.quantile_mapper = data["quantile_mapper"]
        self.is_trained = True


def train_unsupervised_model(
    train_data: pd.DataFrame,
    config: Dict[str, Any] | None = None,
) -> UnsupervisedModel:
    """
    Entraîne un modèle non supervisé.

    Args:
        train_data: Features d'entraînement (dataset normal-only)
        config: Configuration des hyperparamètres

    Returns:
        Modèle entraîné
    """
    model = UnsupervisedModel(config=config)
    model.train(train_data)
    return model
