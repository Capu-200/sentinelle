"""
Pipeline complet de feature engineering.

Ce module orchestre l'extraction des features depuis une transaction enrichie
(format backend) ou depuis une transaction simple (format legacy).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .aggregator import extract_historical_features, compute_historical_aggregates
from .extractor import extract_transactional_features, extract_transaction_features


class FeaturePipeline:
    """
    Pipeline de feature engineering pour les transactions.

    Supporte deux formats :
    1. Transaction enrichie (nouveau format) : extrait les features pré-calculées
    2. Transaction simple (legacy) : calcule les features (fallback)
    """

    def __init__(
        self,
        feature_schema_path: Optional[Path] = None,
        windows: Optional[List[str]] = None,
    ):
        """
        Initialise le pipeline de features.

        Args:
            feature_schema_path: Chemin vers le schéma de features versionné
            windows: Liste des fenêtres temporelles à utiliser (legacy uniquement)
        """
        self.windows = windows or ["5m", "1h", "24h", "7d", "30d"]
        self.feature_schema = None

        if feature_schema_path:
            self.load_schema(feature_schema_path)

    def load_schema(self, schema_path: Path) -> None:
        """Charge un schéma de features versionné."""
        with open(schema_path, "r") as f:
            self.feature_schema = json.load(f)

    def transform(
        self,
        transaction: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Transforme une transaction en features.

        Détecte automatiquement le format :
        - Transaction enrichie : si `transaction.get("features")` existe
        - Transaction simple : sinon (legacy)

        Args:
            transaction: Transaction à transformer (enrichie ou simple)
            historical_data: Historique des transactions (legacy uniquement)

        Returns:
            Dictionnaire de features complètes
        """
        # Détecter le format : transaction enrichie ou simple ?
        is_enriched = "features" in transaction

        if is_enriched:
            # Format enrichi : extraire les features pré-calculées
            tx_features = extract_transactional_features(transaction)
            historical_features = extract_historical_features(transaction)
            
            # Détecter si l'historique est réellement présent (au moins une feature non-nulle)
            has_historical = any(
                v not in [None, 0, 0.0, -1.0, False, []]
                for v in historical_features.values()
            )
        else:
            # Format legacy : calculer les features
            tx_features = extract_transaction_features(transaction)
            historical_features = compute_historical_aggregates(
                transaction, historical_data, self.windows
            )
            
            # Si historical_data est fourni et non vide, historique présent
            has_historical = historical_data is not None and len(historical_data) > 0

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
