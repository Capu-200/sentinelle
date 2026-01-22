"""
Moteur de règles métier.

Ce module évalue les règles R1-R4 et calcule le rule_score.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class RuleResult:
    """Résultat de l'évaluation d'une règle."""

    rule_id: str
    triggered: bool
    reason: str | None = None
    contribution: float = 0.0
    hard_block: bool = False


@dataclass
class RulesOutput:
    """Sortie du moteur de règles."""

    rule_score: float
    reasons: List[str]
    hard_block: bool


class RulesEngine:
    """
    Moteur d'évaluation des règles métier.

    Règles supportées :
    - R1: KYC light (montant max)
    - R2: Pays interdit/sanctionné
    - R3: Vélocité anormale
    - R4: Nouveau destinataire + montant inhabituel
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialise le moteur de règles.

        Args:
            config_path: Chemin vers le fichier de configuration des règles
        """
        self.config = None
        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: Path) -> None:
        """Charge la configuration des règles depuis un fichier YAML."""
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

    def evaluate(
        self,
        transaction: Dict[str, Any],
        features: Dict[str, Any] | None = None,
    ) -> RulesOutput:
        """
        Évalue toutes les règles pour une transaction.

        Args:
            transaction: Transaction à évaluer
            features: Features calculées (pour R3, R4)

        Returns:
            Résultat de l'évaluation des règles
        """
        results = []

        # R1: KYC light (montant max)
        r1_result = self._evaluate_r1(transaction)
        results.append(r1_result)

        # R2: Pays interdit/sanctionné
        r2_result = self._evaluate_r2(transaction)
        results.append(r2_result)

        # R3: Vélocité anormale
        if features:
            r3_result = self._evaluate_r3(transaction, features)
            results.append(r3_result)

        # R4: Nouveau destinataire + montant inhabituel
        if features:
            r4_result = self._evaluate_r4(transaction, features)
            results.append(r4_result)

        # Calculer le rule_score et collecter les reasons
        rule_score = min(1.0, sum(r.contribution for r in results))
        reasons = [r.reason for r in results if r.triggered and r.reason]
        hard_block = any(r.hard_block for r in results)

        return RulesOutput(
            rule_score=rule_score,
            reasons=reasons,
            hard_block=hard_block,
        )

    def _evaluate_r1(self, transaction: Dict[str, Any]) -> RuleResult:
        """R1: KYC light - montant max."""
        amount = transaction.get("amount", 0)
        threshold = 300  # TODO: Charger depuis config

        triggered = amount > threshold
        return RuleResult(
            rule_id="R1",
            triggered=triggered,
            reason="amount_over_kyc_limit" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r2(self, transaction: Dict[str, Any]) -> RuleResult:
        """R2: Pays interdit/sanctionné."""
        country = transaction.get("country")
        sanctioned_countries = ["KP"]  # TODO: Charger depuis config

        if not country:
            return RuleResult(rule_id="R2", triggered=False)

        triggered = country in sanctioned_countries
        return RuleResult(
            rule_id="R2",
            triggered=triggered,
            reason="sanctioned_country" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r3(
        self, transaction: Dict[str, Any], features: Dict[str, Any]
    ) -> RuleResult:
        """R3: Vélocité anormale."""
        # TODO: Implémenter avec les features historiques
        tx_count_1m = features.get("src_tx_count_out_1m", 0)
        tx_count_1h = features.get("src_tx_count_out_1h", 0)

        triggered = tx_count_1m > 5 or tx_count_1h > 30
        return RuleResult(
            rule_id="R3",
            triggered=triggered,
            reason="high_velocity" if triggered else None,
            contribution=0.6 if triggered else 0.0,
            hard_block=False,
        )

    def _evaluate_r4(
        self, transaction: Dict[str, Any], features: Dict[str, Any]
    ) -> RuleResult:
        """R4: Nouveau destinataire + montant inhabituel."""
        # TODO: Implémenter avec les features historiques
        is_new_dest = features.get("is_new_destination_30d", False)
        amount = transaction.get("amount", 0)
        p95_amount = features.get("p95_amount_source_30d", 0)

        triggered = is_new_dest and amount > p95_amount
        return RuleResult(
            rule_id="R4",
            triggered=triggered,
            reason="new_destination_wallet" if triggered else None,
            contribution=0.6 if triggered else 0.0,
            hard_block=False,
        )
