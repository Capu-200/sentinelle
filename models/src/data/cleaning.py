"""
Logique de nettoyage des données transactionnelles.

Ce module contient les fonctions réutilisables pour nettoyer et normaliser
les données de transactions avant le feature engineering.
"""

from __future__ import annotations

from typing import Any, Dict


def clean_transaction_data(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoie et normalise une transaction.

    Args:
        transaction: Dictionnaire contenant les données de transaction brutes

    Returns:
        Transaction nettoyée et normalisée

    TODO:
        - Normaliser les timestamps (ISO-8601, UTC)
        - Normaliser direction (IN/OUT -> incoming/outgoing)
        - Parser metadata.raw_payload si présent
        - Valider les champs requis
        - Anti-leakage (retirer metadata.risk_score si présent)
    """
    cleaned = transaction.copy()

    # TODO: Implémenter la logique de nettoyage
    # - Normalisation des timestamps
    # - Normalisation de direction
    # - Parsing des métadonnées
    # - Validation des champs

    return cleaned
