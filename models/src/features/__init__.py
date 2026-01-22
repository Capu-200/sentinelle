"""
Module de feature engineering.

Ce module gère l'extraction et le calcul des features pour les transactions.
"""

from .extractor import extract_transaction_features
from .aggregator import compute_historical_aggregates
from .pipeline import FeaturePipeline

__all__ = [
    "extract_transaction_features",
    "compute_historical_aggregates",
    "FeaturePipeline",
]
