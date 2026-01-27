"""
Prédiction avec le modèle non supervisé.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from .train import UnsupervisedModel


class UnsupervisedPredictor:
    """Prédicteur pour le modèle non supervisé avec support du versioning."""

    def __init__(
        self,
        model_path: Path | None = None,
        model: UnsupervisedModel | None = None,
        model_version: str | None = None,
        artifacts_dir: Path | None = None,
    ):
        """
        Initialise le prédicteur.

        Args:
            model_path: Chemin vers le modèle sauvegardé
            model: Instance de modèle (alternative à model_path)
            model_version: Version du modèle (ex: "v1.0.0" ou "latest")
            artifacts_dir: Dossier des artefacts (pour charger feature_schema.json)
        """
        self.model_version = model_version or "unknown"
        self.artifacts_dir = artifacts_dir or Path("artifacts")
        
        if model:
            self.model = model
            if hasattr(model, "model_version"):
                self.model_version = model.model_version
        elif model_path:
            self.model = UnsupervisedModel()
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
            Instance de UnsupervisedPredictor
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
        
        model_path = artifacts_dir / version / "unsupervised_model.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Modèle non trouvé: {model_path}")
        
        predictor = cls(model_path=model_path, model_version=version, artifacts_dir=artifacts_dir)
        return predictor

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

        # Valider et compléter les features manquantes
        df = self._ensure_all_features(df)

        # Prédire
        predictions = self.model.predict(df)
        return float(predictions.iloc[0] if isinstance(predictions, pd.Series) else predictions[0])

    @staticmethod
    def _is_blank_value(val: Any) -> bool:
        """
        True si la valeur est considérée comme vide / pas d'historique.
        Utilise des tests explicites pour éviter "ambiguous truth value" avec ndarray/list.
        """
        if val is None:
            return True
        if isinstance(val, np.ndarray):
            return val.size == 0 or not (np.any(np.isfinite(val)) and np.any(val != 0))
        if isinstance(val, (list, tuple)):
            return len(val) == 0
        try:
            return val in (0, 0.0, -1.0, False)
        except (ValueError, TypeError):
            return True

    def _ensure_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        S'assure que toutes les features attendues par le modèle sont présentes
        et que seules les features attendues sont passées au modèle.
        
        IsolationForest (sklearn) vérifie strictement les feature names.
        On filtre pour ne garder QUE les features attendues.
        
        Args:
            df: DataFrame avec les features
            
        Returns:
            DataFrame avec uniquement les features attendues, dans le bon ordre
        """
        # Récupérer les features attendues depuis feature_schema.json
        expected_features = self._get_expected_features()
        
        if not expected_features:
            # Fallback : si pas de schéma, essayer de déduire depuis les colonnes présentes
            # en enlevant les features "suspectes" ajoutées par le pipeline mais absentes à l'entraînement
            # (ex: transaction_type_TRANSFER si les autres transaction_type_* sont présentes)
            df_filtered = df.copy()
            tx_type_cols = [c for c in df_filtered.columns if c.startswith("transaction_type_")]
            if tx_type_cols and "transaction_type_TRANSFER" in df_filtered.columns:
                # Si on a d'autres transaction_type_* mais pas TRANSFER dans le modèle,
                # enlever TRANSFER (probablement ajouté par _ensure_one_hot_features)
                if "transaction_type_p2p" in tx_type_cols or "transaction_type_merchant" in tx_type_cols:
                    df_filtered = df_filtered.drop(columns=["transaction_type_TRANSFER"])
                    print("⚠️  Pas de feature_schema.json: retiré transaction_type_TRANSFER (non attendu par le modèle)")
            return df_filtered
        
        # Créer une copie pour ne pas modifier l'original
        df_complete = df.copy()
        
        # Ajouter les features manquantes avec des valeurs par défaut
        for feature in expected_features:
            if feature not in df_complete.columns:
                # Valeur par défaut selon le type de feature
                if 'count' in feature or 'tx_' in feature:
                    default_value = 0
                elif 'amount' in feature or 'mean' in feature or 'sum' in feature or 'max' in feature:
                    default_value = 0.0
                elif 'is_' in feature:
                    if 'new' in feature:
                        default_value = 1  # Nouveau compte par défaut
                    else:
                        default_value = 0
                elif 'mismatch' in feature:
                    default_value = 0
                elif 'days_since' in feature:
                    default_value = -1.0
                elif 'concentration' in feature or 'ratio' in feature or 'entropy' in feature:
                    default_value = 0.0
                else:
                    default_value = 0
                
                df_complete[feature] = default_value
        
        # CRITIQUE : Ne garder QUE les features attendues (filtre les features en trop)
        # IsolationForest vérifie strictement les feature names
        # Vérifier qu'on a toutes les features attendues
        missing = [f for f in expected_features if f not in df_complete.columns]
        if missing:
            print(f"⚠️  Features manquantes après complétion: {missing}")
        
        # Filtrer pour ne garder QUE les features attendues
        df_complete = df_complete[expected_features]
        
        return df_complete
    
    def _get_expected_features(self) -> list:
        """
        Récupère la liste des features attendues depuis le feature_schema.json.
        
        Returns:
            Liste des noms de features
        """
        import json
        
        # Chercher le feature_schema.json dans les artefacts
        if self.model_version and self.model_version != "unknown":
            version = self.model_version.replace("v", "")
            schema_path = self.artifacts_dir / f"v{version}" / "feature_schema.json"
        else:
            # Chercher dans latest ou la dernière version
            schema_path = self.artifacts_dir / "latest" / "feature_schema.json"
            if not schema_path.exists():
                version_dirs = [d for d in self.artifacts_dir.iterdir() 
                              if d.is_dir() and d.name.startswith("v")]
                if version_dirs:
                    latest_version = sorted(version_dirs, key=lambda x: x.name)[-1].name
                    schema_path = self.artifacts_dir / latest_version / "feature_schema.json"
        
        if schema_path.exists():
            try:
                with open(schema_path, 'r') as f:
                    schema = json.load(f)
                    return schema.get("features", [])
            except Exception:
                pass
        
        # Fallback : retourner une liste vide (le modèle utilisera toutes les colonnes)
        return []
