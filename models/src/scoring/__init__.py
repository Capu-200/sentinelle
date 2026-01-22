"""
Module de scoring global et décision.

Ce module combine les signaux (règles, supervisé, non supervisé)
et prend la décision finale.
"""

from .decision import DecisionEngine
from .scorer import GlobalScorer

__all__ = ["GlobalScorer", "DecisionEngine"]
