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
    """Prédicteur pour le modèle supervisé avec support du versioning."""

    def __init__(
        self,
        model_path: Path | None = None,
        model: SupervisedModel | None = None,
        model_version: str | None = None,
    ):
        """
        Initialise le prédicteur.

        Args:
            model_path: Chemin vers le modèle sauvegardé
            model: Instance de modèle (alternative à model_path)
            model_version: Version du modèle (ex: "v1.0.0" ou "latest")
        """
        self.model_version = model_version or "unknown"
        
        if model:
            self.model = model
            if hasattr(model, "model_version"):
                self.model_version = model.model_version
        elif model_path:
            self.model = SupervisedModel()
            self.model.load(model_path)
        else:
            raise ValueError("Il faut fournir model_path ou model")

    @classmethod
    def load_version(cls, version: str, artifacts_dir: Path | None = None):
        """
        Charge un modèle depuis une version spécifique.

        Args:
            version: Version du modèle (ex: "v1.0.0" ou "latest")
            artifacts_dir: Dossier des artefacts (défaut: "artifacts")

        Returns:
            Instance de SupervisedPredictor
        """
        if artifacts_dir is None:
            artifacts_dir = Path("artifacts")
        
        # Résoudre "latest" vers la vraie version
        if version == "latest":
            latest_path = artifacts_dir / "latest"
            if latest_path.exists() and latest_path.is_symlink():
                version = latest_path.readlink().name
            else:
                # Chercher la dernière version
                version_dirs = [d for d in artifacts_dir.iterdir() 
                              if d.is_dir() and d.name.startswith("v")]
                if version_dirs:
                    version = sorted(version_dirs, key=lambda x: x.name)[-1].name
                else:
                    raise FileNotFoundError(f"Aucune version trouvée dans {artifacts_dir}")
        
        # Normaliser le format (ajouter "v" si absent)
        if not version.startswith("v"):
            version = f"v{version}"
        
        model_path = artifacts_dir / version / "supervised_model.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Modèle non trouvé: {model_path}")
        
        predictor = cls(model_path=model_path, model_version=version)
        return predictor

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
