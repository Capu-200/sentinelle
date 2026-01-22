"""
Modèle non supervisé (IsolationForest).

Ce module contient le modèle non supervisé pour la détection d'anomalies.
"""

from .predictor import UnsupervisedPredictor
from .train import train_unsupervised_model

__all__ = ["train_unsupervised_model", "UnsupervisedPredictor"]
