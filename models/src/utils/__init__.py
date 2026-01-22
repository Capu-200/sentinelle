"""
Utilitaires partagés.

Ce module contient les fonctions utilitaires pour la configuration
et le versioning.
"""

from .config import load_config
from .versioning import get_model_version, save_artifacts

__all__ = ["load_config", "get_model_version", "save_artifacts"]
