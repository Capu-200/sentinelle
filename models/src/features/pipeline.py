"""
Pipeline complet de feature engineering.

Ce module orchestre l'extraction et l'agrégation des features.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .aggregator import compute_historical_aggregates
from .extractor import extract_transaction_features


class FeaturePipeline:
    """
    Pipeline de feature engineering pour les transactions.

    Gère l'extraction des features transactionnelles et le calcul
    des agrégats historiques.
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
            windows: Liste des fenêtres temporelles à utiliser
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

        Args:
            transaction: Transaction à transformer
            historical_data: Historique des transactions (optionnel)

        Returns:
            Dictionnaire de features complètes
        """
        # Features transactionnelles
        tx_features = extract_transaction_features(transaction)

        # Agrégats historiques
        historical_features = compute_historical_aggregates(
            transaction, historical_data, self.windows
        )

        # Combiner toutes les features
        all_features = {**tx_features, **historical_features}

        # TODO: Valider contre le schéma si présent
        # if self.feature_schema:
        #     self._validate_features(all_features)

        return all_features

    def fit(self, transactions: List[Dict[str, Any]]) -> None:
        """
        Ajuste le pipeline sur un dataset (pour calibration, etc.).

        Args:
            transactions: Liste de transactions pour l'ajustement
        """
        # TODO: Implémenter si nécessaire (ex: calibration de quantiles)
        pass
