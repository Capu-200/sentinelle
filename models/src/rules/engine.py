"""
Moteur de règles métier.

Ce module évalue les règles R1-R15 et calcule le rule_score.

Règles implémentées :
- R1-R7: Règles bloquantes (BLOCK immédiat)
- R8-R10: Règles boost (BOOST_SCORE)
- R11-R15: Règles mixtes (BLOCK ou BOOST_SCORE selon conditions)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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
    decision: str  # ALLOW, BOOST_SCORE, BLOCK
    boost_factor: float  # Facteur de boost (défaut: 1.0)


class RulesEngine:
    """
    Moteur d'évaluation des règles métier.

    Règles supportées :
    - R1-R7: Règles bloquantes (BLOCK)
    - R8-R10: Règles boost (BOOST_SCORE)
    - R11-R15: Règles mixtes (BLOCK ou BOOST_SCORE selon conditions)
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
        context: Dict[str, Any] | None = None,
    ) -> RulesOutput:
        """
        Évalue toutes les règles pour une transaction.

        Args:
            transaction: Transaction à évaluer
            features: Features calculées (pour règles historiques)
            context: Contexte additionnel (wallet_info, user_profile, historique_store)

        Returns:
            Résultat de l'évaluation des règles
        """
        results = []

        # Règles bloquantes (évaluées en premier)
        r1_result = self._evaluate_r1(transaction)
        results.append(r1_result)

        r2_result = self._evaluate_r2(transaction, context)
        results.append(r2_result)

        r3_result = self._evaluate_r3(transaction, context)
        results.append(r3_result)

        r4_result = self._evaluate_r4(transaction)
        results.append(r4_result)

        r5_result = self._evaluate_r5(transaction)
        results.append(r5_result)

        r6_result = self._evaluate_r6(transaction)
        results.append(r6_result)

        r7_result = self._evaluate_r7(transaction, context)
        results.append(r7_result)

        # Si une règle bloquante est déclenchée, arrêter ici
        if any(r.hard_block for r in results):
            rule_score = min(1.0, sum(r.contribution for r in results))
            reasons = [r.reason for r in results if r.triggered and r.reason]
            return RulesOutput(
                rule_score=rule_score,
                reasons=reasons,
                hard_block=True,
                decision="BLOCK",
                boost_factor=1.0,
            )

        # Règles BOOST_SCORE (évaluées si pas de BLOCK)
        r8_result = self._evaluate_r8(transaction, features)
        results.append(r8_result)

        r9_result = self._evaluate_r9(transaction, features)
        results.append(r9_result)

        r10_result = self._evaluate_r10(transaction, context)
        results.append(r10_result)

        # Règles mixtes (peuvent être BLOCK ou BOOST_SCORE)
        r11_result = self._evaluate_r11(transaction, features)
        results.append(r11_result)

        r12_result = self._evaluate_r12(transaction, features)
        results.append(r12_result)

        r13_result = self._evaluate_r13(transaction)
        results.append(r13_result)

        r14_result = self._evaluate_r14(transaction, context)
        results.append(r14_result)

        r15_result = self._evaluate_r15(transaction, features, context)
        results.append(r15_result)

        # Vérifier si une règle mixte a déclenché un BLOCK
        hard_block = any(r.hard_block for r in results)

        # Calculer le rule_score et collecter les reasons
        rule_score = min(1.0, sum(r.contribution for r in results))
        reasons = [r.reason for r in results if r.triggered and r.reason]

        # Déterminer la décision et le boost_factor
        if hard_block:
            decision = "BLOCK"
            boost_factor = 1.0
        else:
            # Compter les règles BOOST_SCORE déclenchées
            boost_rules_count = sum(1 for r in results if r.triggered and not r.hard_block)
            if boost_rules_count > 0:
                decision = "BOOST_SCORE"
                # Calculer le boost_factor (+0.1 par règle, max 2.0)
                boost_factor = min(2.0, 1.0 + (boost_rules_count * 0.1))
            else:
                decision = "ALLOW"
                boost_factor = 1.0

        return RulesOutput(
            rule_score=rule_score,
            reasons=reasons,
            hard_block=hard_block,
            decision=decision,
            boost_factor=boost_factor,
        )

    # ========== Règles bloquantes (R1-R7) ==========

    def _evaluate_r1(self, transaction: Dict[str, Any]) -> RuleResult:
        """R1: Montant maximum absolu."""
        amount = transaction.get("amount", 0)
        threshold = 300  # PYC

        if amount <= 0:
            return RuleResult(rule_id="R1", triggered=False)

        triggered = amount > threshold
        return RuleResult(
            rule_id="R1",
            triggered=triggered,
            reason="RULE_MAX_AMOUNT" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r2(self, transaction: Dict[str, Any], context: Dict[str, Any] | None) -> RuleResult:
        """R2: Solde insuffisant."""
        amount = transaction.get("amount", 0)
        source_wallet_id = transaction.get("source_wallet_id")

        if not source_wallet_id or amount <= 0:
            return RuleResult(rule_id="R2", triggered=False)

        # Récupérer le balance depuis le context (mock pour phase dev)
        wallet_balance = None
        if context:
            wallet_info = context.get("wallet_info")
            if wallet_info:
                wallet_balance = wallet_info.get("balance")

        # Si pas de balance disponible, ignorer la règle
        if wallet_balance is None:
            return RuleResult(rule_id="R2", triggered=False)

        triggered = wallet_balance < amount
        return RuleResult(
            rule_id="R2",
            triggered=triggered,
            reason="RULE_INSUFFICIENT_FUNDS" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r3(self, transaction: Dict[str, Any], context: Dict[str, Any] | None) -> RuleResult:
        """R3: Wallet bloqué ou utilisateur suspendu."""
        source_wallet_id = transaction.get("source_wallet_id")
        initiator_user_id = transaction.get("initiator_user_id")

        if not source_wallet_id or not initiator_user_id:
            return RuleResult(rule_id="R3", triggered=False)

        # Récupérer les status depuis le context
        wallet_status = None
        user_status = None

        if context:
            wallet_info = context.get("wallet_info")
            user_profile = context.get("user_profile")

            if wallet_info:
                wallet_status = wallet_info.get("status")
            if user_profile:
                user_status = user_profile.get("status")

        # Si pas de status disponible, ignorer la règle
        if wallet_status is None and user_status is None:
            return RuleResult(rule_id="R3", triggered=False)

        # Vérifier si wallet ou user est bloqué
        wallet_blocked = wallet_status is not None and wallet_status != "active"
        user_blocked = user_status is not None and user_status != "active"

        triggered = wallet_blocked or user_blocked
        return RuleResult(
            rule_id="R3",
            triggered=triggered,
            reason="RULE_ACCOUNT_LOCKED" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r4(self, transaction: Dict[str, Any]) -> RuleResult:
        """R4: Auto-virement interdit."""
        source_wallet_id = transaction.get("source_wallet_id")
        destination_wallet_id = transaction.get("destination_wallet_id")

        if not source_wallet_id or not destination_wallet_id:
            return RuleResult(rule_id="R4", triggered=False)

        triggered = source_wallet_id == destination_wallet_id
        return RuleResult(
            rule_id="R4",
            triggered=triggered,
            reason="RULE_SELF_TRANSFER" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r5(self, transaction: Dict[str, Any]) -> RuleResult:
        """R5: Montant nul ou négatif."""
        amount = transaction.get("amount", 0)

        triggered = amount <= 0
        return RuleResult(
            rule_id="R5",
            triggered=triggered,
            reason="RULE_INVALID_AMOUNT" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r6(self, transaction: Dict[str, Any]) -> RuleResult:
        """R6: Pays interdit (blacklist)."""
        country = transaction.get("country")

        # Si pas de country, ignorer la règle
        if not country:
            return RuleResult(rule_id="R6", triggered=False)

        sanctioned_countries = ["KP"]  # Liste des pays interdits

        triggered = country in sanctioned_countries
        return RuleResult(
            rule_id="R6",
            triggered=triggered,
            reason="RULE_COUNTRY_BLOCKED" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r7(self, transaction: Dict[str, Any], context: Dict[str, Any] | None) -> RuleResult:
        """R7: Destination interdite."""
        destination_wallet_id = transaction.get("destination_wallet_id")

        if not destination_wallet_id:
            return RuleResult(rule_id="R7", triggered=False)

        # Récupérer le status du wallet destination depuis le context
        destination_status = None
        if context:
            destination_wallet_info = context.get("destination_wallet_info")
            if destination_wallet_info:
                destination_status = destination_wallet_info.get("status")

        # Si pas de status disponible, ignorer la règle
        if destination_status is None:
            return RuleResult(rule_id="R7", triggered=False)

        triggered = destination_status != "active"
        return RuleResult(
            rule_id="R7",
            triggered=triggered,
            reason="RULE_DESTINATION_LOCKED" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    # ========== Règles BOOST_SCORE (R8-R10) ==========

    def _evaluate_r8(self, transaction: Dict[str, Any], features: Dict[str, Any] | None) -> RuleResult:
        """R8: Montant inhabituel (hard seuil)."""
        amount = transaction.get("amount", 0)

        if amount <= 0:
            return RuleResult(rule_id="R8", triggered=False)

        if not features:
            return RuleResult(rule_id="R8", triggered=False)

        avg_amount_30d = features.get("avg_amount_30d")

        # Si pas de moyenne disponible (nouveau compte), ignorer la règle
        if avg_amount_30d is None or avg_amount_30d <= 0:
            return RuleResult(rule_id="R8", triggered=False)

        # Seuil 1: amount > avg_amount_30d * 10
        # Seuil 2: amount > avg_amount_30d * 5
        triggered = amount > avg_amount_30d * 10 or amount > avg_amount_30d * 5

        return RuleResult(
            rule_id="R8",
            triggered=triggered,
            reason="RULE_AMOUNT_ANOMALY" if triggered else None,
            contribution=0.6 if triggered else 0.0,
            hard_block=False,
        )

    def _evaluate_r9(self, transaction: Dict[str, Any], features: Dict[str, Any] | None) -> RuleResult:
        """R9: Rafale de transactions."""
        if not features:
            return RuleResult(rule_id="R9", triggered=False)

        # tx_last_10min : nombre de transactions dans les 10 dernières minutes
        tx_last_10min = features.get("tx_last_10min", 0)

        # Seuil 1: tx_last_10min >= 20
        # Seuil 2: tx_last_10min >= 10
        triggered = tx_last_10min >= 20 or tx_last_10min >= 10

        return RuleResult(
            rule_id="R9",
            triggered=triggered,
            reason="RULE_FREQ_SPIKE" if triggered else None,
            contribution=0.6 if triggered else 0.0,
            hard_block=False,
        )

    def _evaluate_r10(self, transaction: Dict[str, Any], context: Dict[str, Any] | None) -> RuleResult:
        """R10: Compte trop récent."""
        amount = transaction.get("amount", 0)
        created_at_str = transaction.get("created_at")

        if amount <= 0 or not created_at_str:
            return RuleResult(rule_id="R10", triggered=False)

        # Récupérer l'âge du compte depuis le context
        account_age_minutes = None
        if context:
            account_age_minutes = context.get("account_age_minutes")

        # Si pas d'âge disponible, ignorer la règle
        if account_age_minutes is None:
            return RuleResult(rule_id="R10", triggered=False)

        # Seuil 1: account_age_minutes < 5 ET amount > 100
        # Seuil 2: account_age_minutes < 60 ET amount > 50
        triggered = (account_age_minutes < 5 and amount > 100) or (
            account_age_minutes < 60 and amount > 50
        )

        return RuleResult(
            rule_id="R10",
            triggered=triggered,
            reason="RULE_NEW_ACCOUNT_ACTIVITY" if triggered else None,
            contribution=0.6 if triggered else 0.0,
            hard_block=False,
        )

    # ========== Règles mixtes (R11-R15) ==========

    def _evaluate_r11(self, transaction: Dict[str, Any], features: Dict[str, Any] | None) -> RuleResult:
        """R11: Nouveau bénéficiaire + montant élevé."""
        amount = transaction.get("amount", 0)

        if amount <= 0:
            return RuleResult(rule_id="R11", triggered=False)

        if not features:
            return RuleResult(rule_id="R11", triggered=False)

        is_new_beneficiary = features.get("is_new_beneficiary", False)

        if not is_new_beneficiary:
            return RuleResult(rule_id="R11", triggered=False)

        # Seuil 1: is_new_beneficiary = true ET amount > 200 → BLOCK
        # Seuil 2: is_new_beneficiary = true ET amount > 80 → BOOST_SCORE
        if amount > 200:
            return RuleResult(
                rule_id="R11",
                triggered=True,
                reason="RULE_NEW_BENEFICIARY",
                contribution=1.0,
                hard_block=True,
            )
        elif amount > 80:
            return RuleResult(
                rule_id="R11",
                triggered=True,
                reason="RULE_NEW_BENEFICIARY",
                contribution=0.6,
                hard_block=False,
            )

        return RuleResult(rule_id="R11", triggered=False)

    def _evaluate_r12(self, transaction: Dict[str, Any], features: Dict[str, Any] | None) -> RuleResult:
        """R12: Pays inhabituel (hard)."""
        country = transaction.get("country")
        amount = transaction.get("amount", 0)

        if not country or amount <= 0:
            return RuleResult(rule_id="R12", triggered=False)

        if not features:
            return RuleResult(rule_id="R12", triggered=False)

        user_country_history = features.get("user_country_history", [])

        # Si pas d'historique disponible, ignorer la règle
        if not user_country_history:
            return RuleResult(rule_id="R12", triggered=False)

        # country NOT IN user_country_history ET amount > 150 → BLOCK
        triggered = country not in user_country_history and amount > 150

        return RuleResult(
            rule_id="R12",
            triggered=triggered,
            reason="RULE_GEO_ANOMALY" if triggered else None,
            contribution=1.0 if triggered else 0.0,
            hard_block=triggered,
        )

    def _evaluate_r13(self, transaction: Dict[str, Any]) -> RuleResult:
        """R13: Horaire interdit."""
        amount = transaction.get("amount", 0)
        created_at_str = transaction.get("created_at")

        if amount <= 0 or not created_at_str:
            return RuleResult(rule_id="R13", triggered=False)

        # Parser le datetime et extraire l'heure (UTC)
        try:
            from dateutil import parser

            dt = parser.parse(created_at_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)

            hour = dt.hour
        except Exception:
            return RuleResult(rule_id="R13", triggered=False)

        # Horaire interdit: 01:00 - 05:00 (UTC)
        in_forbidden_hours = 1 <= hour < 5

        if not in_forbidden_hours:
            return RuleResult(rule_id="R13", triggered=False)

        # Seuil 1: hour BETWEEN 01:00 AND 05:00 ET amount > 120 → BLOCK
        # Seuil 2: hour BETWEEN 01:00 AND 05:00 ET amount > 60 → BOOST_SCORE
        if amount > 120:
            return RuleResult(
                rule_id="R13",
                triggered=True,
                reason="RULE_ODD_HOUR",
                contribution=1.0,
                hard_block=True,
            )
        elif amount > 60:
            return RuleResult(
                rule_id="R13",
                triggered=True,
                reason="RULE_ODD_HOUR",
                contribution=0.6,
                hard_block=False,
            )

        return RuleResult(rule_id="R13", triggered=False)

    def _evaluate_r14(self, transaction: Dict[str, Any], context: Dict[str, Any] | None) -> RuleResult:
        """R14: Profil à risque connu."""
        amount = transaction.get("amount", 0)
        initiator_user_id = transaction.get("initiator_user_id")

        if amount <= 0 or not initiator_user_id:
            return RuleResult(rule_id="R14", triggered=False)

        # Récupérer le risk_level depuis le context
        risk_level = None
        if context:
            user_profile = context.get("user_profile")
            if user_profile:
                risk_level = user_profile.get("risk_level")

        # Si pas de risk_level disponible, ignorer la règle
        if risk_level is None or risk_level != "high":
            return RuleResult(rule_id="R14", triggered=False)

        # Seuil 1: risk_level = 'high' ET amount > 50 → BOOST_SCORE
        # Seuil 2: risk_level = 'high' ET amount > 150 → BLOCK
        if amount > 150:
            return RuleResult(
                rule_id="R14",
                triggered=True,
                reason="RULE_HIGH_RISK_PROFILE",
                contribution=1.0,
                hard_block=True,
            )
        elif amount > 50:
            return RuleResult(
                rule_id="R14",
                triggered=True,
                reason="RULE_HIGH_RISK_PROFILE",
                contribution=0.6,
                hard_block=False,
            )

        return RuleResult(rule_id="R14", triggered=False)

    def _evaluate_r15(
        self,
        transaction: Dict[str, Any],
        features: Dict[str, Any] | None,
        context: Dict[str, Any] | None,
    ) -> RuleResult:
        """R15: Récidive récente."""
        if not features:
            return RuleResult(rule_id="R15", triggered=False)

        # blocked_tx_last_24h : nombre de transactions bloquées dans les 24h
        blocked_tx_last_24h = features.get("blocked_tx_last_24h", 0)

        # Seuil 1: blocked_tx_last_24h >= 3 → BLOCK
        # Seuil 2: blocked_tx_last_24h >= 1 → BOOST_SCORE
        if blocked_tx_last_24h >= 3:
            return RuleResult(
                rule_id="R15",
                triggered=True,
                reason="RULE_RECIDIVISM",
                contribution=1.0,
                hard_block=True,
            )
        elif blocked_tx_last_24h >= 1:
            return RuleResult(
                rule_id="R15",
                triggered=True,
                reason="RULE_RECIDIVISM",
                contribution=0.6,
                hard_block=False,
            )

        return RuleResult(rule_id="R15", triggered=False)
