"""
Entraînement du modèle supervisé (LightGBM).
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

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
        
        # Configuration par défaut optimisée pour la détection de fraude
        default_config = {
            "objective": "binary",
            "metric": "binary_logloss",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "random_state": 42,
        }
        
        # Fusionner avec la config fournie
        self.config = {**default_config, **(config or {})}
        
        # Initialiser le modèle
        self.model = lgb.LGBMClassifier(**self.config)

    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> None:
        """
        Entraîne le modèle LightGBM.

        Args:
            X: Features d'entraînement
            y: Labels (0/1 pour fraude)
            **kwargs: Arguments additionnels (ex: val_data, val_labels)
        """
        # Calculer scale_pos_weight pour gérer le déséquilibre
        fraud_count = y.sum()
        legit_count = len(y) - fraud_count
        
        if fraud_count > 0:
            scale_pos_weight = legit_count / fraud_count
        else:
            scale_pos_weight = 1.0
        
        # Mettre à jour la config avec scale_pos_weight
        self.model.set_params(scale_pos_weight=scale_pos_weight)
        
        # Préparer les données de validation si fournies
        val_data = kwargs.get("val_data")
        val_labels = kwargs.get("val_labels")
        
        if val_data is not None and val_labels is not None:
            # Early stopping avec validation set
            callbacks = [
                lgb.early_stopping(stopping_rounds=50, verbose=False),
                lgb.log_evaluation(period=100, show_stdv=False),
            ]
            
            self.model.fit(
                X,
                y,
                eval_set=[(val_data, val_labels)],
                callbacks=callbacks,
            )
            
            # Calculer PR-AUC sur le validation set
            val_pred = self.model.predict_proba(val_data)[:, 1]
            pr_auc = average_precision_score(val_labels, val_pred)
            print(f"   📊 PR-AUC (validation): {pr_auc:.4f}")
        else:
            # Entraînement sans validation set
            self.model.fit(X, y)
        
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
        
        # Prédire les probabilités (classe 1 = fraude)
        probabilities = self.model.predict_proba(X)[:, 1]
        return pd.Series(probabilities, index=X.index)

    def save(self, path: Path) -> None:
        """Sauvegarde le modèle."""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "model": self.model,
                    "config": self.config,
                    "model_version": self.model_version,
                },
                f,
            )

    def load(self, path: Path) -> None:
        """Charge le modèle."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.config = data.get("config", {})
            self.model_version = data.get("model_version", "1.0.0")
        
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
