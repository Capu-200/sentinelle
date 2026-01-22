"""
Extraction des agrégats historiques depuis une transaction enrichie.

Ce module extrait les features historiques pré-calculées depuis la structure
de transaction enrichie (format backend). Les features sont calculées côté
backend, le ML Engine ne fait que les extraire.

Gestion du cas 0 transaction historique : toutes les features peuvent être null.
"""

from __future__ import annotations

from typing import Any, Dict


def extract_historical_features(enriched_transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait les features historiques depuis une transaction enrichie.

    Les features historiques sont pré-calculées côté backend et incluses dans
    `enriched_transaction["features"]["historical"]`.

    Gestion des valeurs manquantes :
    - `null` = pas d'historique disponible (nouveau compte, 0 transaction)
    - `0` / `false` / `[]` = historique disponible mais valeur nulle

    Args:
        enriched_transaction: Transaction enrichie avec structure complète
            {
                "features": {
                    "historical": {
                        "avg_amount_30d": ...,
                        "tx_last_10min": ...,
                        ...
                    }
                }
            }

    Returns:
        Dictionnaire de features historiques (peut contenir des null)

    Raises:
        KeyError: Si la structure enrichie n'est pas valide
    """
    # Extraire les features historiques
    features = enriched_transaction.get("features", {})
    historical_features = features.get("historical", {})

    # Si pas de section historical, retourner dict vide
    if not historical_features:
        return {}

    # Retourner toutes les features historiques (y compris les null)
    # Le ML Engine gérera les null avec des valeurs par défaut
    return historical_features.copy()


def compute_historical_aggregates(
    transaction: Dict[str, Any],
    historical_data: Any = None,
    windows: Any = None,
) -> Dict[str, Any]:
    """
    DEPRECATED: Utiliser extract_historical_features() pour les transactions enrichies.

    Cette fonction est conservée pour compatibilité avec l'ancien format.
    Elle retourne un dict vide car les features sont maintenant pré-calculées.

    Args:
        transaction: Transaction (ancien format)
        historical_data: Ignoré (features pré-calculées maintenant)
        windows: Ignoré

    Returns:
        Dictionnaire vide (features doivent venir de la transaction enrichie)
    """
    # Retourner dict vide - les features doivent venir de la transaction enrichie
    return {}
