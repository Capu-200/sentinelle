"""
Calcul des agrégats historiques (fenêtres temporelles).

Ce module calcule les features comportementales basées sur l'historique
des transactions (profils de wallet, relations, etc.).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def compute_historical_aggregates(
    transaction: Dict[str, Any],
    historical_data: Optional[List[Dict[str, Any]]] = None,
    windows: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Calcule les agrégats historiques pour une transaction.

    Agrégats calculés :
    - Profil wallet source (tx_count, amount_sum/mean/max, unique_destinations)
    - Relation source->dest (is_new_destination, tx_count, days_since_last)
    - Dispersion/concentration des destinataires
    - Localisation (is_new_country, country_mismatch)
    - Statuts/échecs (failed_count, failed_ratio)

    Args:
        transaction: Transaction courante
        historical_data: Liste des transactions historiques (optionnel)
        windows: Liste des fenêtres temporelles (ex: ['5m', '1h', '24h', '7d'])

    Returns:
        Dictionnaire d'agrégats historiques

    TODO:
        - Calculer les agrégats par fenêtre temporelle
        - Profil wallet source (pour chaque fenêtre)
        - Relation source->dest
        - Dispersion/concentration
        - Localisation
        - Statuts/échecs
    """
    if windows is None:
        windows = ["5m", "1h", "24h", "7d", "30d"]

    aggregates = {}

    # TODO: Implémenter le calcul des agrégats
    # - Filtrer l'historique par fenêtre temporelle
    # - Calculer les agrégats pour chaque fenêtre
    # - Profil wallet source
    # - Relation source->dest
    # - Autres agrégats

    return aggregates
