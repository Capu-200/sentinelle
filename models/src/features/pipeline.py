"""
Pipeline de feature engineering pour le scoring.

Une seule logique : format enrichi uniquement.
transaction doit contenir features.transactional et features.historical.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .aggregator import extract_historical_features
from .extractor import extract_transactional_features


def _is_blank_value(val: Any) -> bool:
    """True si valeur vide / sans signal (évite 'ambiguous truth value' avec ndarray/list)."""
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


class FeaturePipeline:
    """
    Pipeline de feature engineering pour le scoring.

    Format accepté : transaction enrichie uniquement.
    transaction doit contenir features.transactional et features.historical.
    """

    def __init__(
        self,
        feature_schema_path: Optional[Path] = None,
    ):
        """
        Initialise le pipeline de features.

        Args:
            feature_schema_path: Chemin vers le schéma de features versionné
        """
        self.feature_schema = None

        if feature_schema_path:
            self.load_schema(feature_schema_path)

    def load_schema(self, schema_path: Path) -> None:
        """Charge un schéma de features versionné."""
        with open(schema_path, "r") as f:
            self.feature_schema = json.load(f)

    def transform(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforme une transaction enrichie en features.

        Args:
            transaction: Transaction enrichie avec transaction.features.transactional
                         et transaction.features.historical (obligatoire).

        Returns:
            Dictionnaire de features prêt pour le modèle.

        Raises:
            ValueError: Si transaction ne contient pas features.transactional/historical.
        """
        if "features" not in transaction:
            raise ValueError(
                "Format enrichi obligatoire: transaction doit contenir 'features' "
                "avec 'transactional' et 'historical'."
            )
        feats = transaction.get("features") or {}
        if "transactional" not in feats or "historical" not in feats:
            raise ValueError(
                "transaction.features doit contenir 'transactional' et 'historical'."
            )

        tx_features = extract_transactional_features(transaction)
        historical_features = extract_historical_features(transaction)

        has_historical = any(
            not _is_blank_value(v) for v in historical_features.values()
        )

        # Combiner toutes les features
        all_features = {**tx_features, **historical_features}

        # Gérer les valeurs null dans les features historiques
        # (cas 0 transaction historique)
        # Passer has_historical pour une gestion intelligente
        all_features = self._handle_null_features(all_features, has_historical=has_historical)

        # S'assurer que toutes les features one-hot sont présentes
        all_features = self._ensure_one_hot_features(all_features)

        # TODO: Valider contre le schéma si présent
        # if self.feature_schema:
        #     self._validate_features(all_features)

        return all_features
    
    def _ensure_one_hot_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        S'assure que toutes les features one-hot encodées sont présentes.
        
        Ajoute les features manquantes avec 0 (non activées).
        
        Args:
            features: Dictionnaire de features
            
        Returns:
            Dictionnaire avec toutes les features one-hot
        """
        handled_features = features.copy()
        
        # Features one-hot pour transaction_type
        tx_type_features = [
            "transaction_type_p2p",
            "transaction_type_merchant",
            "transaction_type_cashin",
            "transaction_type_cashout",
            "transaction_type_TRANSFER",  # Ajout pour TRANSFER
        ]
        for feature in tx_type_features:
            if feature not in handled_features:
                handled_features[feature] = 0
        
        # Features one-hot pour direction
        direction_features = [
            "direction_outgoing",
            "direction_incoming",
        ]
        for feature in direction_features:
            if feature not in handled_features:
                handled_features[feature] = 0
        
        # Features one-hot pour country
        country_features = [
            "country_fr",
            "country_be",
            "country_kp",
        ]
        for feature in country_features:
            if feature not in handled_features:
                handled_features[feature] = 0
        
        return handled_features

    def _handle_null_features(self, features: Dict[str, Any], has_historical: bool = False) -> Dict[str, Any]:
        """
        Gère les valeurs null dans les features historiques.

        Convertit les null en valeurs par défaut intelligentes :
        - Si historique présent : valeurs = "pas de données" (0, -1, etc.)
        - Si historique absent : valeurs = "nouveau compte" (0, -1, 1 pour "new", etc.)

        Args:
            features: Dictionnaire de features
            has_historical: True si l'historique est présent (au moins une feature non-nulle)

        Returns:
            Dictionnaire avec null remplacés par valeurs par défaut
        """
        handled_features = features.copy()

        for key, value in handled_features.items():
            if value is None:
                # Déterminer le type attendu depuis le nom de la feature
                if "count" in key or "tx_last" in key or "blocked" in key:
                    # Counts : 0 = pas de transactions
                    handled_features[key] = 0
                elif "amount" in key or "mean" in key or "sum" in key or "max" in key:
                    # Amounts : 0.0 = pas de montant
                    handled_features[key] = 0.0
                elif "is_" in key:
                    # Booléens : gestion selon présence d'historique
                    if "new" in key:
                        # Nouveau = 1 si pas d'historique (plus conservateur), 0 si historique présent
                        handled_features[key] = 1 if not has_historical else 0
                    else:
                        handled_features[key] = 0
                elif "mismatch" in key:
                    # Mismatch : 0 = pas de mismatch
                    handled_features[key] = 0
                elif "history" in key or "country" in key:
                    # Arrays : liste vide
                    handled_features[key] = []
                elif "concentration" in key or "ratio" in key or "entropy" in key:
                    # Ratios/entropy : 0.0 = pas de dispersion
                    handled_features[key] = 0.0
                elif "days_since" in key:
                    # Convertir None en -1.0 pour indiquer "jamais" (LightGBM n'accepte pas None/object)
                    handled_features[key] = -1.0
                else:
                    # Par défaut : 0
                    handled_features[key] = 0

        return handled_features

    def fit(self, transactions: List[Dict[str, Any]]) -> None:
        """
        Ajuste le pipeline sur un dataset (pour calibration, etc.).

        Args:
            transactions: Liste de transactions pour l'ajustement
        """
        # TODO: Implémenter si nécessaire (ex: calibration de quantiles)
        pass
