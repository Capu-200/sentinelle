"""
Prédiction avec le modèle supervisé.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np
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
        
        predictor = cls(model_path=model_path, model_version=version, artifacts_dir=artifacts_dir)
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
        S'assure que toutes les features attendues par le modèle sont présentes.
        
        Ajoute les features manquantes avec des valeurs par défaut intelligentes :
        - Si historique présent : valeurs par défaut = "pas d'historique" (0, -1, etc.)
        - Si historique absent : valeurs par défaut = "nouveau compte" (0, -1, etc.)
        
        Args:
            df: DataFrame avec les features
            
        Returns:
            DataFrame avec toutes les features requises
        """
        # Features attendues par le modèle (depuis feature_schema.json ou depuis le modèle)
        # On récupère les noms de features depuis le modèle LightGBM
        if hasattr(self.model, 'model') and hasattr(self.model.model, 'feature_name_'):
            expected_features = self.model.model.feature_name_
        else:
            # Fallback : utiliser le schéma si disponible
            expected_features = self._get_expected_features()
        
        # Créer une copie pour ne pas modifier l'original
        df_complete = df.copy()
        
        # Détecter si l'historique est présent (au moins une feature historique non-nulle)
        # Vérifier les features historiques dans le DataFrame
        historical_cols = [
            col for col in df_complete.columns
            if (col.startswith('src_tx_') or col.startswith('is_new_') or 
                col.startswith('days_since') or col.startswith('src_to_dst') or
                col.startswith('src_destination') or col.startswith('src_failed'))
            and col in expected_features
        ]
        
        has_historical = False
        if len(df_complete) > 0 and historical_cols:
            for col in historical_cols:
                val = df_complete[col].iloc[0]
                if not self._is_blank_value(val):
                    has_historical = True
                    break
        
        # Ajouter les features manquantes avec des valeurs par défaut intelligentes
        for feature in expected_features:
            if feature not in df_complete.columns:
                # Valeur par défaut selon le type de feature et présence d'historique
                if 'count' in feature or 'tx_' in feature:
                    # Counts : 0 = pas de transactions (normal pour nouveau compte ou pas d'historique)
                    default_value = 0
                elif 'amount' in feature or 'mean' in feature or 'sum' in feature or 'max' in feature:
                    # Amounts : 0.0 = pas de montant (normal)
                    default_value = 0.0
                elif 'is_' in feature:
                    # Booléens : 1 = nouveau/oui si pas d'historique, 0 = non si historique présent
                    if 'new' in feature:
                        # Nouveau = 1 si pas d'historique (plus conservateur)
                        default_value = 1 if not has_historical else 0
                    else:
                        default_value = 0
                elif 'mismatch' in feature:
                    # Mismatch : 0 = pas de mismatch
                    default_value = 0
                elif 'days_since' in feature:
                    # Days since : -1.0 = jamais (normal si pas d'historique)
                    default_value = -1.0
                elif 'concentration' in feature or 'ratio' in feature or 'entropy' in feature:
                    # Ratios/entropy : 0.0 = pas de dispersion (normal si pas d'historique)
                    default_value = 0.0
                else:
                    # Par défaut : 0
                    default_value = 0
                
                df_complete[feature] = default_value
        
        # Réordonner les colonnes selon l'ordre attendu par le modèle
        if expected_features:
            # Garder seulement les features attendues dans le bon ordre
            missing_cols = [f for f in expected_features if f not in df_complete.columns]
            if missing_cols:
                # Ajouter les colonnes manquantes
                for col in missing_cols:
                    df_complete[col] = 0.0
            
            # Réordonner selon l'ordre attendu
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
        
        # Fallback : retourner une liste vide (le modèle utilisera ses propres features)
        return []
