"""
Calcul du score global de risque.

Combine les signaux des règles, du modèle supervisé et du modèle non supervisé.
"""

from __future__ import annotations

from typing import Any, Dict

import yaml
from pathlib import Path


class GlobalScorer:
    """
    Calcule le score global de risque.

    Formule : risk_score = w_rule × rule_score + w_sup × s_sup + w_unsup × s_unsup
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialise le scorer global.

        Args:
            config_path: Chemin vers le fichier de configuration des poids
        """
        # Poids par défaut
        self.weights = {
            "rule_score": 0.2,
            "supervised": 0.6,
            "unsupervised": 0.2,
        }

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: Path) -> None:
        """Charge la configuration des poids depuis un fichier YAML."""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            if "weights" in config:
                self.weights.update(config["weights"])

    def compute_score(
        self,
        rule_score: float,
        supervised_score: float,
        unsupervised_score: float,
    ) -> float:
        """
        Calcule le score global de risque.

        Args:
            rule_score: Score des règles [0,1]
            supervised_score: Score du modèle supervisé [0,1]
            unsupervised_score: Score du modèle non supervisé [0,1]

        Returns:
            Score global de risque [0,1]
        """
        risk_score = (
            self.weights["rule_score"] * rule_score
            + self.weights["supervised"] * supervised_score
            + self.weights["unsupervised"] * unsupervised_score
        )

        # Clamper entre 0 et 1
        return max(0.0, min(1.0, risk_score))
