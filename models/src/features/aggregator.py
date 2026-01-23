"""
Extraction des agrégats historiques depuis une transaction enrichie.

Ce module extrait les features historiques pré-calculées depuis la structure
de transaction enrichie (format backend). Les features sont calculées côté
backend, le ML Engine ne fait que les extraire.

Gestion du cas 0 transaction historique : toutes les features peuvent être null.

Pour l'entraînement, compute_historical_aggregates() calcule les features
depuis l'historique brut (nécessaire car pas de format enrichi).
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd


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
    historical_data: List[Dict[str, Any]] | pd.DataFrame | None = None,
    windows: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Calcule les agrégats historiques depuis l'historique brut.

    Cette fonction est utilisée POUR L'ENTRAÎNEMENT uniquement.
    En production, utilisez extract_historical_features() avec le format enrichi.

    Args:
        transaction: Transaction courante (doit avoir created_at, source_wallet_id, etc.)
        historical_data: Liste de transactions historiques (DataFrame ou liste de dicts)
        windows: Liste des fenêtres temporelles (ex: ["5m", "1h", "24h", "7d", "30d"])

    Returns:
        Dictionnaire de features historiques calculées
    """
    if historical_data is None:
        historical_data = []
    
    if windows is None:
        windows = ["5m", "1h", "24h", "7d", "30d"]
    
    # Extraire les infos de la transaction courante
    tx_created_at = _parse_datetime(transaction.get("created_at"))
    source_wallet_id = transaction.get("source_wallet_id")
    destination_wallet_id = transaction.get("destination_wallet_id")
    tx_country = transaction.get("country")
    
    if tx_created_at is None:
        # Pas de timestamp → retourner features vides
        return _get_empty_historical_features(windows)
    
    # Convertir l'historique en DataFrame si nécessaire
    if isinstance(historical_data, list):
        if len(historical_data) == 0:
            return _get_empty_historical_features(windows)
        hist_df = pd.DataFrame(historical_data)
    elif isinstance(historical_data, pd.DataFrame):
        hist_df = historical_data.copy()
    else:
        return _get_empty_historical_features(windows)
    
    # Filtrer : uniquement les transactions AVANT la transaction courante (event-time)
    hist_df["created_at"] = pd.to_datetime(hist_df["created_at"], utc=True)
    hist_df = hist_df[hist_df["created_at"] < tx_created_at].copy()
    
    if len(hist_df) == 0:
        return _get_empty_historical_features(windows)
    
    features = {}
    
    # ========== PROFIL WALLET SOURCE ==========
    # Filtrer les transactions du wallet source (outgoing uniquement)
    src_hist = hist_df[
        (hist_df["source_wallet_id"] == source_wallet_id) &
        (hist_df["direction"] == "outgoing")
    ].copy()
    
    for window in windows:
        window_delta = _parse_window(window)
        window_start = tx_created_at - window_delta
        
        # Transactions dans la fenêtre
        window_txs = src_hist[src_hist["created_at"] >= window_start]
        
        # Features de base
        features[f"src_tx_count_out_{window}"] = len(window_txs)
        
        if len(window_txs) > 0:
            amounts = window_txs["amount"].fillna(0)
            features[f"src_tx_amount_sum_out_{window}"] = float(amounts.sum())
            features[f"src_tx_amount_mean_out_{window}"] = float(amounts.mean())
            features[f"src_tx_amount_max_out_{window}"] = float(amounts.max())
            features[f"src_unique_destinations_{window}"] = int(window_txs["destination_wallet_id"].nunique())
        else:
            features[f"src_tx_amount_sum_out_{window}"] = 0.0
            features[f"src_tx_amount_mean_out_{window}"] = 0.0
            features[f"src_tx_amount_max_out_{window}"] = 0.0
            features[f"src_unique_destinations_{window}"] = 0
    
    # ========== RELATION SOURCE → DESTINATION ==========
    if destination_wallet_id:
        # Transactions entre source et destination
        src_dst_hist = hist_df[
            (hist_df["source_wallet_id"] == source_wallet_id) &
            (hist_df["destination_wallet_id"] == destination_wallet_id)
        ].copy()
        
        # is_new_destination pour différentes fenêtres
        for window in ["24h", "7d", "30d"]:
            window_delta = _parse_window(window)
            window_start = tx_created_at - window_delta
            window_txs = src_dst_hist[src_dst_hist["created_at"] >= window_start]
            features[f"is_new_destination_{window}"] = 1 if len(window_txs) == 0 else 0
        
        # Nombre de transactions source→dest dans les 30 derniers jours
        window_30d = tx_created_at - timedelta(days=30)
        src_dst_30d = src_dst_hist[src_dst_hist["created_at"] >= window_30d]
        features["src_to_dst_tx_count_30d"] = len(src_dst_30d)
        
        # Jours depuis la dernière transaction source→dest
        if len(src_dst_hist) > 0:
            last_tx_date = src_dst_hist["created_at"].max()
            days_diff = (tx_created_at - last_tx_date).total_seconds() / 86400
            features["days_since_last_src_to_dst"] = float(days_diff)
        else:
            features["days_since_last_src_to_dst"] = None  # Pas d'historique
    else:
        # Pas de destination → valeurs par défaut
        for window in ["24h", "7d", "30d"]:
            features[f"is_new_destination_{window}"] = 1  # Nouveau par défaut
        features["src_to_dst_tx_count_30d"] = 0
        features["days_since_last_src_to_dst"] = None
    
    # ========== DISPERSION DES DESTINATAIRES (7 jours) ==========
    window_7d = tx_created_at - timedelta(days=7)
    src_7d = src_hist[src_hist["created_at"] >= window_7d]
    
    if len(src_7d) > 0:
        # Concentration : part du top-1 destinataire
        dest_counts = src_7d["destination_wallet_id"].value_counts()
        top_dest_ratio = dest_counts.iloc[0] / len(src_7d) if len(dest_counts) > 0 else 0.0
        features["src_destination_concentration_7d"] = float(top_dest_ratio)
        
        # Entropie (mesure de dispersion)
        dest_probs = dest_counts / len(src_7d)
        entropy = -sum(p * math.log2(p) for p in dest_probs if p > 0)
        features["src_destination_entropy_7d"] = float(entropy)
    else:
        features["src_destination_concentration_7d"] = 0.0
        features["src_destination_entropy_7d"] = 0.0
    
    # ========== LOCALISATION ==========
    if tx_country:
        # Pays utilisés par le wallet source dans les 30 derniers jours
        window_30d = tx_created_at - timedelta(days=30)
        src_30d = src_hist[src_hist["created_at"] >= window_30d]
        
        if len(src_30d) > 0:
            countries_used = set(src_30d["country"].dropna().unique())
            features["is_new_country_30d"] = 1 if tx_country not in countries_used else 0
            
            # Country mismatch : pays différent du pays le plus fréquent
            if len(src_30d) > 0:
                most_common_country = src_30d["country"].mode().iloc[0] if len(src_30d["country"].mode()) > 0 else None
                features["country_mismatch"] = 1 if most_common_country and tx_country != most_common_country else 0
            else:
                features["country_mismatch"] = 0
        else:
            features["is_new_country_30d"] = 1  # Nouveau pays par défaut
            features["country_mismatch"] = 0
    else:
        features["is_new_country_30d"] = 0
        features["country_mismatch"] = 0
    
    # ========== STATUTS & ÉCHECS ==========
    # Transactions échouées/annulées (si le champ existe)
    if "status" in hist_df.columns or "reason_code" in hist_df.columns:
        src_24h = src_hist[src_hist["created_at"] >= (tx_created_at - timedelta(hours=24))]
        
        # Compter les échecs (status FAILED/CANCELED ou reason_code non null)
        if "status" in src_24h.columns:
            failed_24h = src_24h[src_24h["status"].isin(["FAILED", "CANCELED"])]
        elif "reason_code" in src_24h.columns:
            failed_24h = src_24h[src_24h["reason_code"].notna()]
        else:
            failed_24h = pd.DataFrame()
        
        features["src_failed_count_24h"] = len(failed_24h)
        
        # Ratio d'échecs sur 7 jours
        src_7d = src_hist[src_hist["created_at"] >= (tx_created_at - timedelta(days=7))]
        if len(src_7d) > 0:
            if "status" in src_7d.columns:
                failed_7d = src_7d[src_7d["status"].isin(["FAILED", "CANCELED"])]
            elif "reason_code" in src_7d.columns:
                failed_7d = src_7d[src_7d["reason_code"].notna()]
            else:
                failed_7d = pd.DataFrame()
            features["src_failed_ratio_7d"] = float(len(failed_7d) / len(src_7d)) if len(src_7d) > 0 else 0.0
        else:
            features["src_failed_ratio_7d"] = 0.0
    else:
        features["src_failed_count_24h"] = 0
        features["src_failed_ratio_7d"] = 0.0
    
    return features


def _parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse une date string en datetime UTC."""
    if dt_str is None:
        return None
    
    try:
        from dateutil import parser
        from dateutil.tz import UTC
        
        dt = parser.parse(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt
    except Exception:
        return None


def _parse_window(window: str) -> timedelta:
    """Parse une fenêtre temporelle (ex: "5m", "1h", "24h", "7d", "30d")."""
    if window.endswith("m"):
        minutes = int(window[:-1])
        return timedelta(minutes=minutes)
    elif window.endswith("h"):
        hours = int(window[:-1])
        return timedelta(hours=hours)
    elif window.endswith("d"):
        days = int(window[:-1])
        return timedelta(days=days)
    else:
        raise ValueError(f"Fenêtre invalide: {window}")


def _get_empty_historical_features(windows: List[str]) -> Dict[str, Any]:
    """Retourne un dictionnaire de features historiques vides."""
    features = {}
    
    # Profil wallet source
    for window in windows:
        features[f"src_tx_count_out_{window}"] = 0
        features[f"src_tx_amount_sum_out_{window}"] = 0.0
        features[f"src_tx_amount_mean_out_{window}"] = 0.0
        features[f"src_tx_amount_max_out_{window}"] = 0.0
        features[f"src_unique_destinations_{window}"] = 0
    
    # Relation
    for window in ["24h", "7d", "30d"]:
        features[f"is_new_destination_{window}"] = 1  # Nouveau par défaut
    features["src_to_dst_tx_count_30d"] = 0
    features["days_since_last_src_to_dst"] = None
    
    # Dispersion
    features["src_destination_concentration_7d"] = 0.0
    features["src_destination_entropy_7d"] = 0.0
    
    # Localisation
    features["is_new_country_30d"] = 0
    features["country_mismatch"] = 0
    
    # Statuts
    features["src_failed_count_24h"] = 0
    features["src_failed_ratio_7d"] = 0.0
    
    return features
