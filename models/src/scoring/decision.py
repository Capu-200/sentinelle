"""
Logique de décision finale (BLOCK/REVIEW/APPROVE).

Applique les seuils sur le score global et gère les hard blocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import yaml
from pathlib import Path


@dataclass
class Decision:
    """Décision finale de scoring."""

    risk_score: float
    decision: str  # APPROVE, REVIEW, BLOCK
    reasons: List[str]
    model_version: str


class DecisionEngine:
    """
    Moteur de décision finale.

    Applique les seuils sur le score global et gère les hard blocks.
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialise le moteur de décision.

        Args:
            config_path: Chemin vers le fichier de configuration des seuils
        """
        # Seuils par défaut
        self.thresholds = {
            "block": 0.99,  # Top 0.1% (quantile 0.999)
            "review": 0.99,  # Top 1% (quantile 0.99)
        }

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: Path) -> None:
        """Charge la configuration des seuils depuis un fichier YAML."""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            if "thresholds" in config:
                self.thresholds.update(config["thresholds"])

    def decide(
        self,
        risk_score: float,
        reasons: List[str],
        hard_block: bool,
        model_version: str,
    ) -> Decision:
        """
        Prend la décision finale.

        Args:
            risk_score: Score global de risque [0,1]
            reasons: Liste des raisons (règles déclenchées)
            hard_block: True si hard block (règles R1/R2)
            model_version: Version du modèle

        Returns:
            Décision finale
        """
        # Hard block force BLOCK
        if hard_block:
            return Decision(
                risk_score=risk_score,
                decision="BLOCK",
                reasons=reasons,
                model_version=model_version,
            )

        # Appliquer les seuils
        if risk_score >= self.thresholds["block"]:
            decision = "BLOCK"
        elif risk_score >= self.thresholds["review"]:
            decision = "REVIEW"
        else:
            decision = "APPROVE"

        return Decision(
            risk_score=risk_score,
            decision=decision,
            reasons=reasons,
            model_version=model_version,
        )
