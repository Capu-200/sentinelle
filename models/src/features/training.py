"""
Fonctions utilitaires pour le Feature Engineering en entraînement.

Ce module contient des fonctions pour calculer les features sur des datasets complets
pour l'entraînement (nécessite le calcul des features historiques depuis l'historique).
"""

from __future__ import annotations

import multiprocessing as mp
from functools import partial
from typing import Any, Dict, List

import pandas as pd

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from .aggregator import compute_historical_aggregates
from .extractor import extract_transaction_features
from .pipeline import FeaturePipeline


def _compute_features_single(
    args: tuple,
    windows: List[str],
) -> Dict[str, Any]:
    """
    Fonction helper pour calculer les features d'une seule transaction.
    
    Utilisée par multiprocessing.
    
    Args:
        args: Tuple (idx, transaction_dict, historical_df_dict)
        windows: Liste des fenêtres temporelles
    
    Returns:
        Dictionnaire de features
    """
    idx, transaction_dict, historical_df_dict = args
    
    # Reconstruire le DataFrame historique depuis le dict
    if historical_df_dict and len(historical_df_dict) > 0:
        historical_df = pd.DataFrame(historical_df_dict)
        historical_df["created_at"] = pd.to_datetime(historical_df["created_at"], utc=True)
    else:
        historical_df = None
    
    # Calculer les features transactionnelles
    tx_features = extract_transaction_features(transaction_dict)
    
    # Calculer les features historiques
    historical_features = compute_historical_aggregates(
        transaction=transaction_dict,
        historical_data=historical_df,
        windows=windows,
    )
    
    # Combiner toutes les features
    all_features = {**tx_features, **historical_features}
    
    # Gérer les nulls
    pipeline = FeaturePipeline()
    all_features = pipeline._handle_null_features(all_features)
    
    return all_features


def compute_features_for_dataset(
    transactions_df: pd.DataFrame,
    windows: List[str] | None = None,
    verbose: bool = True,
    n_jobs: int | None = None,
    chunk_size: int = 1000,
) -> pd.DataFrame:
    """
    Calcule les features pour un dataset complet (pour l'entraînement).

    Pour chaque transaction, calcule :
    - Features transactionnelles (depuis la transaction)
    - Features historiques (depuis toutes les transactions AVANT cette transaction)

    Args:
        transactions_df: DataFrame des transactions (doit être trié par created_at)
        windows: Liste des fenêtres temporelles (défaut: ["5m", "1h", "24h", "7d", "30d"])
        verbose: Afficher la progression
        n_jobs: Nombre de processus parallèles (défaut: nombre de cores - 1)
        chunk_size: Taille des chunks pour la parallélisation (défaut: 1000)

    Returns:
        DataFrame avec les features calculées
    """
    if windows is None:
        windows = ["5m", "1h", "24h", "7d", "30d"]
    
    # Déterminer le nombre de jobs
    if n_jobs is None:
        n_jobs = max(1, mp.cpu_count() - 1)  # Laisser 1 core libre
    
    # S'assurer que le DataFrame est trié par created_at
    if "created_at" in transactions_df.columns:
        transactions_df = transactions_df.sort_values("created_at").reset_index(drop=True)
    
    # Convertir created_at en datetime si nécessaire
    if transactions_df["created_at"].dtype != "datetime64[ns, UTC]":
        transactions_df["created_at"] = pd.to_datetime(transactions_df["created_at"], utc=True)
    
    # Optimisation : Ne pas préparer tous les args en mémoire (trop lourd pour 4.5M)
    # On va préparer les args à la volée par chunks
    if verbose:
        print(f"🔧 Dataset: {len(transactions_df)} transactions")
        print(f"   Utilisation de {n_jobs} processus parallèles")
        print(f"   Mode: Parallélisation par chunks de {chunk_size} transactions")
    
    # Calculer les features en parallèle
    if n_jobs > 1 and len(transactions_df) > chunk_size:
        # Parallélisation par chunks - préparation à la volée pour éviter la surcharge mémoire
        if verbose:
            print(f"🚀 Calcul des features en parallèle ({n_jobs} processus)...")
        
        features_list = []
        n_chunks = (len(transactions_df) + chunk_size - 1) // chunk_size
        
        import time
        start_time = time.time()
        total_processed = 0
        
        # Créer un iterator avec tqdm si disponible
        if verbose and HAS_TQDM:
            chunk_iterator = tqdm(range(n_chunks), desc="Calcul des features", unit="chunk")
        else:
            chunk_iterator = range(n_chunks)
        
        for chunk_idx in chunk_iterator:
            start_idx = chunk_idx * chunk_size
            end_idx = min((chunk_idx + 1) * chunk_size, len(transactions_df))
            
            # Log de démarrage du chunk
            if verbose:
                print(f"   📦 Démarrage chunk {chunk_idx + 1}/{n_chunks} (transactions {start_idx:,}-{end_idx:,})...", flush=True)
            
            # Préparer les args pour ce chunk uniquement (à la volée)
            chunk_args = []
            prep_start = time.time()
            for idx in range(start_idx, end_idx):
                transaction = transactions_df.iloc[idx]
                transaction_dict = transaction.to_dict()
                
                # OPTIMISATION: Limiter l'historique à une fenêtre temporelle (30 jours max)
                # Au lieu de charger TOUT l'historique, on ne prend que les 30 derniers jours
                # Cela réduit drastiquement la mémoire et le temps de calcul
                tx_created_at = pd.to_datetime(transaction_dict.get("created_at"), utc=True)
                
                if pd.notna(tx_created_at):
                    # Filtrer par date : seulement les transactions dans les 30 derniers jours
                    cutoff_date = tx_created_at - pd.Timedelta(days=30)
                    historical_df = transactions_df[
                        (transactions_df.index < idx) & 
                        (pd.to_datetime(transactions_df["created_at"], utc=True) >= cutoff_date)
                    ].copy()
                else:
                    # Pas de timestamp → historique vide
                    historical_df = transactions_df.iloc[:0].copy()
                
                # Convertir en dict pour la sérialisation (multiprocessing)
                if len(historical_df) > 0:
                    historical_df_dict = historical_df.to_dict("records")
                else:
                    historical_df_dict = None
                
                chunk_args.append((idx, transaction_dict, historical_df_dict))
            
            prep_time = time.time() - prep_start
            if verbose:
                print(f"   ✅ Préparation terminée en {prep_time:.1f}s ({len(chunk_args)} transactions)", flush=True)
            
            chunk_start_time = time.time()
            
            # Calculer les features pour ce chunk en parallèle
            if verbose:
                print(f"   🔄 Calcul des features en cours...", flush=True)
            
            with mp.Pool(processes=n_jobs) as pool:
                chunk_features = pool.map(
                    partial(_compute_features_single, windows=windows),
                    chunk_args,
                )
            
            chunk_time = time.time() - chunk_start_time
            chunk_speed = len(chunk_args) / chunk_time if chunk_time > 0 else 0
            
            total_processed += len(chunk_args)
            elapsed = time.time() - start_time
            avg_speed = total_processed / elapsed if elapsed > 0 else 0
            progress = (total_processed / len(transactions_df)) * 100
            eta = (len(transactions_df) - total_processed) / avg_speed if avg_speed > 0 else 0
            
            # Mettre à jour la description de tqdm avec les performances
            if verbose and HAS_TQDM:
                chunk_iterator.set_postfix({
                    'speed': f'{avg_speed:.0f} it/s',
                    'progress': f'{progress:.1f}%',
                    'eta': f'{eta/60:.1f}min'
                })
            elif verbose:
                print(f"   ✅ Chunk {chunk_idx + 1}/{n_chunks} terminé | "
                      f"Chunk speed: {chunk_speed:.0f} it/s | "
                      f"Avg speed: {avg_speed:.0f} it/s | "
                      f"Progress: {progress:.1f}% ({total_processed:,}/{len(transactions_df):,}) | "
                      f"ETA: {eta/60:.1f}min | "
                      f"Temps écoulé: {elapsed/60:.1f}min", flush=True)
            
            features_list.extend(chunk_features)
    else:
        # Mode séquentiel (petit dataset ou n_jobs=1)
        if verbose:
            print(f"🔧 Calcul des features (mode séquentiel)...")
        
        import time
        start_time = time.time()
        
        if verbose and HAS_TQDM:
            iterator = tqdm(args_list, desc="Calcul des features", unit="it")
            features_list = [
                _compute_features_single(args, windows) for args in iterator
            ]
        else:
            features_list = []
            for idx, args in enumerate(args_list):
                features_list.append(_compute_features_single(args, windows))
                
                if verbose and (idx + 1) % 100 == 0:
                    elapsed = time.time() - start_time
                    speed = (idx + 1) / elapsed if elapsed > 0 else 0
                    progress = ((idx + 1) / len(args_list)) * 100
                    eta = (len(args_list) - (idx + 1)) / speed if speed > 0 else 0
                    print(f"   Progress: {idx + 1}/{len(args_list)} ({progress:.1f}%) | "
                          f"Speed: {speed:.0f} it/s | "
                          f"ETA: {eta/60:.1f}min")
    
    # Convertir en DataFrame
    features_df = pd.DataFrame(features_list)
    
    return features_df


def compute_features_batch(
    transactions_df: pd.DataFrame,
    batch_size: int = 1000,
    windows: List[str] | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Calcule les features par batch (plus efficace pour gros datasets).

    Args:
        transactions_df: DataFrame des transactions (doit être trié par created_at)
        batch_size: Taille des batches
        windows: Liste des fenêtres temporelles
        verbose: Afficher la progression

    Returns:
        DataFrame avec les features calculées
    """
    if windows is None:
        windows = ["5m", "1h", "24h", "7d", "30d"]
    
    # S'assurer que le DataFrame est trié
    if "created_at" in transactions_df.columns:
        transactions_df = transactions_df.sort_values("created_at").reset_index(drop=True)
    
    # Convertir created_at en datetime si nécessaire
    if transactions_df["created_at"].dtype != "datetime64[ns, UTC]":
        transactions_df["created_at"] = pd.to_datetime(transactions_df["created_at"], utc=True)
    
    all_features = []
    n_batches = (len(transactions_df) + batch_size - 1) // batch_size
    
    for batch_idx in range(n_batches):
        start_idx = batch_idx * batch_size
        end_idx = min((batch_idx + 1) * batch_size, len(transactions_df))
        
        batch_df = transactions_df.iloc[start_idx:end_idx].copy()
        
        if verbose:
            print(f"   Batch {batch_idx + 1}/{n_batches} ({start_idx}-{end_idx})")
        
        # Calculer les features pour ce batch
        batch_features = compute_features_for_dataset(
            batch_df,
            windows=windows,
            verbose=False,  # Pas de tqdm pour les batches
        )
        
        all_features.append(batch_features)
    
    # Concaténer tous les batches
    features_df = pd.concat(all_features, ignore_index=True)
    
    return features_df

