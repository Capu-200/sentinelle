"""
Rule Engine Orchestrator.

Runs all restriction rules against a transaction, computes a weighted score,
combines it with the ML risk_score, and produces the final decision.
Also updates the user's trust_score and risk_level when rules are triggered.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Session

from ..models import User
from .restriction_rules import ALL_RULES, RuleResult

logger = logging.getLogger("rule-engine")

# ---------------------------------------------------------------------------
# Risk level multipliers
# ---------------------------------------------------------------------------
RISK_MULTIPLIERS = {
    "LOW": 1.0,
    "MEDIUM": 1.3,
    "HIGH": 1.6,
    "CRITICAL": 2.0,
}

# Decision thresholds on combined score
THRESHOLD_APPROVE = 0.3
THRESHOLD_REVIEW = 0.6  # >= this → BLOCK

# Trust score penalty per triggered rule
TRUST_PENALTY_PER_RULE = 5

# Risk level escalation thresholds (based on trust_score)
RISK_ESCALATION = [
    (80, "LOW"),
    (60, "MEDIUM"),
    (35, "HIGH"),
    (0, "CRITICAL"),
]


@dataclass
class EvaluationResult:
    """Outcome of the full rule + ML evaluation."""
    rule_score: float = 0.0
    ml_score: float = 0.0
    combined_score: float = 0.0
    decision: str = "APPROVE"
    triggered_rules: List[RuleResult] = field(default_factory=list)
    all_reasons: List[str] = field(default_factory=list)
    trust_score_after: int = 100
    risk_level_after: str = "LOW"


def _compute_trust_multiplier(trust_score: int) -> float:
    """Lower trust → higher multiplier.  trust=100 → 1.0, trust=0 → 2.0"""
    return max(1.0, (200 - trust_score) / 100.0)


def _resolve_risk_level(trust_score: int) -> str:
    for threshold, level in RISK_ESCALATION:
        if trust_score >= threshold:
            return level
    return "CRITICAL"


def evaluate_transaction(
    tx_context: Dict[str, Any],
    ml_risk_score: float,
    ml_reasons: List[str],
    db: Session,
) -> EvaluationResult:
    """
    Run all restriction rules on the transaction, combine with ML score,
    update user profile, and return the final evaluation.

    Parameters
    ----------
    tx_context : dict
        Transaction data including initiator_user_id, amount, source_wallet_id,
        destination_wallet_id, country, created_at, etc.
    ml_risk_score : float
        Risk score from the ML Engine (0.0–1.0).
    ml_reasons : list[str]
        Reason codes from the ML Engine.
    db : Session
        Active database session.
    """
    result = EvaluationResult(ml_score=ml_risk_score)

    # Fetch user profile for weighting
    user_id = tx_context.get("initiator_user_id")
    user: Optional[User] = None
    if user_id:
        user = db.get(User, user_id)

    current_trust = int(user.trust_score or 100) if user else 100
    current_risk = (user.risk_level or "LOW").upper() if user else "LOW"

    # Run each rule
    raw_rule_score = 0.0
    for rule_fn in ALL_RULES:
        try:
            rule_result = rule_fn(tx_context, db)
            if rule_result.triggered:
                result.triggered_rules.append(rule_result)
                raw_rule_score += rule_result.score_delta
                result.all_reasons.append(rule_result.reason_code)
                logger.info(
                    "RULE TRIGGERED tx=%s rule=%s delta=%.2f detail=%s",
                    tx_context.get("transaction_id"),
                    rule_result.reason_code,
                    rule_result.score_delta,
                    rule_result.detail,
                )
        except Exception:
            logger.exception(
                "Rule %s failed for tx=%s",
                rule_fn.__name__,
                tx_context.get("transaction_id"),
            )

    # Apply weighting
    risk_mult = RISK_MULTIPLIERS.get(current_risk, 1.0)
    trust_mult = _compute_trust_multiplier(current_trust)
    weighted_rule_score = min(1.0, raw_rule_score * risk_mult * trust_mult)

    result.rule_score = round(weighted_rule_score, 4)

    # Combine: max(ml, rule) biased approach — take the worse signal
    result.combined_score = round(
        max(ml_risk_score, weighted_rule_score) * 0.6
        + min(ml_risk_score, weighted_rule_score) * 0.4,
        4,
    )

    # Add ML reasons
    result.all_reasons.extend(ml_reasons)

    # Decision
    if result.combined_score >= THRESHOLD_REVIEW:
        result.decision = "BLOCK"
    elif result.combined_score >= THRESHOLD_APPROVE:
        result.decision = "REVIEW"
    else:
        result.decision = "APPROVE"

    # Update user trust_score and risk_level
    if user and result.triggered_rules:
        penalty = len(result.triggered_rules) * TRUST_PENALTY_PER_RULE
        new_trust = max(0, current_trust - penalty)
        new_risk = _resolve_risk_level(new_trust)

        user.trust_score = new_trust
        user.risk_level = new_risk
        user.last_risk_update_at = datetime.utcnow()
        db.add(user)

        result.trust_score_after = new_trust
        result.risk_level_after = new_risk

        logger.info(
            "USER PROFILE UPDATED user=%s trust=%d→%d risk=%s→%s",
            user_id,
            current_trust,
            new_trust,
            current_risk,
            new_risk,
        )
    else:
        result.trust_score_after = current_trust
        result.risk_level_after = current_risk

    logger.info(
        "EVALUATION COMPLETE tx=%s rule_score=%.4f ml_score=%.4f combined=%.4f decision=%s reasons=%s",
        tx_context.get("transaction_id"),
        result.rule_score,
        result.ml_score,
        result.combined_score,
        result.decision,
        result.all_reasons,
    )

    return result
