"""
Extraction de features transactionnelles depuis une transaction enrichie.

Ce module extrait les features transactionnelles pré-calculées depuis la
structure de transaction enrichie (format backend). Les features sont
calculées côté backend, le ML Engine ne fait que les extraire.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict


def extract_transactional_features(enriched_transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait les features transactionnelles depuis une transaction enrichie.

    Les features transactionnelles sont pré-calculées côté backend et incluses
    dans `enriched_transaction["features"]["transactional"]`.

    Args:
        enriched_transaction: Transaction enrichie avec structure complète
            {
                "features": {
                    "transactional": {
                        "amount": ...,
                        "log_amount": ...,
                        ...
                    }
                }
            }

    Returns:
        Dictionnaire de features transactionnelles

    Raises:
        KeyError: Si la structure enrichie n'est pas valide
    """
    # Extraire les features transactionnelles
    features = enriched_transaction.get("features", {})
    transactional_features = features.get("transactional", {})

    # Si pas de section transactional, retourner dict vide
    if not transactional_features:
        return {}

    # Retourner toutes les features transactionnelles
    return transactional_features.copy()


def extract_transaction_features(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    DEPRECATED: Utiliser extract_transactional_features() pour les transactions enrichies.

    Cette fonction est conservée pour compatibilité avec l'ancien format.
    Elle calcule les features depuis une transaction simple (fallback).

    Args:
        transaction: Transaction simple (ancien format)

    Returns:
        Dictionnaire de features transactionnelles calculées
    """
    features = {}

    # Extraire amount et log_amount
    amount = transaction.get("amount", 0)
    features["amount"] = amount
    features["log_amount"] = math.log(1 + amount) if amount > 0 else 0.0

    # Currency
    features["currency_is_pyc"] = transaction.get("currency") == "PYC"

    # Direction (one-hot)
    direction = transaction.get("direction", "")
    features["direction_outgoing"] = 1 if direction == "outgoing" else 0
    features["direction_incoming"] = 1 if direction == "incoming" else 0

    # Transaction type (one-hot)
    tx_type = transaction.get("transaction_type", "")
    features["transaction_type_p2p"] = 1 if tx_type == "P2P" else 0
    features["transaction_type_merchant"] = 1 if tx_type == "MERCHANT" else 0
    features["transaction_type_cashin"] = 1 if tx_type == "CASHIN" else 0
    features["transaction_type_cashout"] = 1 if tx_type == "CASHOUT" else 0

    # Features temporelles
    created_at_str = transaction.get("created_at")
    if created_at_str:
        try:
            from dateutil import parser
            from dateutil.tz import UTC

            dt = parser.parse(created_at_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            else:
                dt = dt.astimezone(UTC)

            features["hour_of_day"] = dt.hour
            features["day_of_week"] = dt.weekday()  # 0=lundi, 6=dimanche
        except Exception:
            features["hour_of_day"] = 0
            features["day_of_week"] = 0
    else:
        features["hour_of_day"] = 0
        features["day_of_week"] = 0

    # Country (one-hot basique - peut être étendu)
    country = transaction.get("country", "")
    features["country_fr"] = 1 if country == "FR" else 0
    features["country_be"] = 1 if country == "BE" else 0
    features["country_kp"] = 1 if country == "KP" else 0

    return features
