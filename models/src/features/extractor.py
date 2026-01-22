"""
Extraction de features transactionnelles.

Ce module extrait les features directement depuis une transaction
(sans besoin d'historique).
"""

from __future__ import annotations

from typing import Any, Dict


def extract_transaction_features(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait les features transactionnelles d'une transaction.

    Features extraites :
    - amount, log_amount
    - currency_is_pyc
    - direction (one-hot)
    - transaction_type (one-hot)
    - hour_of_day, day_of_week
    - country (one-hot ou hashing)

    Args:
        transaction: Dictionnaire contenant les données de transaction

    Returns:
        Dictionnaire de features transactionnelles

    TODO:
        - Extraire amount et log_amount
        - Extraire les features temporelles (hour, day_of_week)
        - Encoder direction, transaction_type, country
        - Valider currency
    """
    features = {}

    # TODO: Implémenter l'extraction des features
    # - amount, log(1 + amount)
    # - currency_is_pyc
    # - direction encoding
    # - transaction_type encoding
    # - hour_of_day, day_of_week
    # - country encoding

    return features
