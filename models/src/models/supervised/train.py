"""
Entraînement du modèle supervisé (LightGBM).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from ..base import BaseModel


class SupervisedModel(BaseModel):
    """Modèle supervisé LightGBM pour la détection de fraude."""

    def __init__(self, model_version: str = "1.0.0", config: Dict[str, Any] | None = None):
        """
        Initialise le modèle supervisé.

        Args:
            model_version: Version du modèle
            config: Configuration des hyperparamètres
        """
        super().__init__(model_version)
        self.config = config or {}
        # TODO: Importer et initialiser LightGBM
        # import lightgbm as lgb
        # self.model = lgb.LGBMClassifier(**self.config)

    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> None:
        """
        Entraîne le modèle LightGBM.

        Args:
            X: Features d'entraînement
            y: Labels (0/1 pour fraude)
            **kwargs: Arguments additionnels (ex: validation set)
        """
        # TODO: Implémenter l'entraînement
        # - Gérer le déséquilibre (scale_pos_weight)
        # - Optimiser PR-AUC
        # - Validation set si fourni
        # - Early stopping
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        Prédit la probabilité de fraude.

        Args:
            X: Features à prédire

        Returns:
            Probabilités de fraude [0,1]
        """
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant la prédiction")
        # TODO: Implémenter la prédiction
        # return self.model.predict_proba(X)[:, 1]
        return pd.Series([0.0] * len(X))

    def save(self, path: Path) -> None:
        """Sauvegarde le modèle."""
        # TODO: Implémenter la sauvegarde
        # import pickle
        # with open(path, 'wb') as f:
        #     pickle.dump(self.model, f)
        pass

    def load(self, path: Path) -> None:
        """Charge le modèle."""
        # TODO: Implémenter le chargement
        # import pickle
        # with open(path, 'rb') as f:
        #     self.model = pickle.load(f)
        self.is_trained = True


def train_supervised_model(
    train_data: pd.DataFrame,
    train_labels: pd.Series,
    val_data: pd.DataFrame | None = None,
    val_labels: pd.Series | None = None,
    config: Dict[str, Any] | None = None,
) -> SupervisedModel:
    """
    Entraîne un modèle supervisé.

    Args:
        train_data: Features d'entraînement
        train_labels: Labels d'entraînement
        val_data: Features de validation (optionnel)
        val_labels: Labels de validation (optionnel)
        config: Configuration des hyperparamètres

    Returns:
        Modèle entraîné
    """
    model = SupervisedModel(config=config)
    model.train(train_data, train_labels, val_data=val_data, val_labels=val_labels)
    return model
