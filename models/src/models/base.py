"""
Classe de base pour les modèles ML.

Définit l'interface commune pour tous les modèles.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseModel(ABC):
    """Classe de base abstraite pour les modèles ML."""

    def __init__(self, model_version: str = "1.0.0"):
        """
        Initialise le modèle.

        Args:
            model_version: Version du modèle (SemVer)
        """
        self.model_version = model_version
        self.model = None
        self.is_trained = False

    @abstractmethod
    def train(self, X, y=None, **kwargs) -> None:
        """
        Entraîne le modèle.

        Args:
            X: Features d'entraînement
            y: Labels (optionnel pour modèles non supervisés)
            **kwargs: Arguments additionnels
        """
        pass

    @abstractmethod
    def predict(self, X) -> Any:
        """
        Prédit pour de nouvelles données.

        Args:
            X: Features à prédire

        Returns:
            Prédictions (probabilités ou scores)
        """
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """
        Sauvegarde le modèle.

        Args:
            path: Chemin où sauvegarder le modèle
        """
        pass

    @abstractmethod
    def load(self, path: Path) -> None:
        """
        Charge le modèle.

        Args:
            path: Chemin vers le modèle sauvegardé
        """
        pass

    def get_version(self) -> str:
        """Retourne la version du modèle."""
        return self.model_version
