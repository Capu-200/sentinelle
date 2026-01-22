"""
Gestion de la configuration.

Charge et valide les fichiers de configuration (YAML/JSON).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Charge un fichier de configuration.

    Args:
        config_path: Chemin vers le fichier de configuration

    Returns:
        Dictionnaire de configuration

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        yaml.YAMLError: Si le fichier YAML est invalide
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Fichier de configuration non trouvé : {config_path}")

    with open(config_path, "r") as f:
        if config_path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        elif config_path.suffix == ".json":
            import json

            return json.load(f)
        else:
            raise ValueError(f"Format de configuration non supporté : {config_path.suffix}")
