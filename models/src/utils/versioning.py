"""
Gestion du versioning des modèles et features.

Gère la sauvegarde et le chargement des artefacts versionnés.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def get_model_version(artifacts_dir: Path) -> str:
    """
    Récupère la version du modèle depuis le dossier d'artefacts.

    Args:
        artifacts_dir: Dossier contenant les artefacts

    Returns:
        Version du modèle (ex: "1.0.0")
    """
    # Chercher le dossier latest ou le dernier dossier versionné
    latest_path = artifacts_dir / "latest"
    if latest_path.exists() and latest_path.is_symlink():
        return latest_path.readlink().name

    # Sinon, chercher le dernier dossier versionné
    version_dirs = [d for d in artifacts_dir.iterdir() if d.is_dir() and d.name.startswith("v")]
    if version_dirs:
        return sorted(version_dirs, key=lambda x: x.name)[-1].name

    return "1.0.0"


def save_artifacts(
    artifacts_dir: Path,
    version: str,
    artifacts: Dict[str, Any],
) -> None:
    """
    Sauvegarde les artefacts d'une version.

    Args:
        artifacts_dir: Dossier racine des artefacts
        version: Version (ex: "1.0.0")
        artifacts: Dictionnaire des artefacts à sauvegarder
    """
    version_dir = artifacts_dir / f"v{version}"
    version_dir.mkdir(parents=True, exist_ok=True)

    # Sauvegarder chaque artefact
    for name, data in artifacts.items():
        if isinstance(data, dict):
            # JSON
            path = version_dir / f"{name}.json"
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        else:
            # Autre (pickle, etc.) - à gérer selon le type
            path = version_dir / name
            # TODO: Gérer différents types (pickle, etc.)

    # Mettre à jour le symlink latest
    latest_path = artifacts_dir / "latest"
    if latest_path.exists():
        latest_path.unlink()
    latest_path.symlink_to(f"v{version}")
