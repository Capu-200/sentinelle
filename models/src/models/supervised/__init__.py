"""
Modèle supervisé (LightGBM).

Ce module contient le modèle supervisé pour la détection de fraude.
"""

from .predictor import SupervisedPredictor
from .train import train_supervised_model

__all__ = ["train_supervised_model", "SupervisedPredictor"]
