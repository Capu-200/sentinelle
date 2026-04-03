"""
10 fraud detection restriction rules for Payon transactions.

Each rule function receives a context dict and a DB session, and returns
a RuleResult with (triggered, score_delta, reason_code, detail).
"""
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func, and_, or_
from sqlmodel import Session, select

from ..models import Transaction, User, Wallet, HumanReview

logger = logging.getLogger("restriction-rules")


@dataclass
class RuleResult:
    triggered: bool
    score_delta: float
    reason_code: str
    detail: str = ""


# ---------------------------------------------------------------------------
# Helper: parse datetime from ISO string or return utcnow
# ---------------------------------------------------------------------------

def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            pass
    return datetime.utcnow()


# ===========================
# RULE 1 — Unusual Amount
# ===========================

def rule_amount_anomaly(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags transactions whose amount is significantly higher than the user's
    historical average (> mean + 2*stddev, or > 95th percentile).
    """
    user_id = ctx.get("initiator_user_id")
    amount = float(ctx.get("amount", 0))
    if not user_id:
        return RuleResult(False, 0.0, "RULE_AMOUNT_ANOMALY")

    tx_id = ctx.get("transaction_id", "")
    cutoff = datetime.utcnow() - timedelta(days=30)
    stmt = (
        select(Transaction.amount)
        .where(
            Transaction.initiator_user_id == user_id,
            Transaction.created_at >= cutoff,
            Transaction.kyc_status != "REJECTED",
            Transaction.transaction_id != tx_id,
        )
    )
    rows = db.execute(stmt).scalars().all()
    amounts = [float(a) for a in rows]

    if len(amounts) < 3:
        # Not enough history to judge
        return RuleResult(False, 0.0, "RULE_AMOUNT_ANOMALY")

    mean = statistics.mean(amounts)
    stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0.0
    threshold = mean + 2 * stdev if stdev > 0 else mean * 3

    if amount > threshold and amount > mean * 2:
        return RuleResult(
            True, 0.25, "RULE_AMOUNT_ANOMALY",
            f"amount={amount:.2f} >> avg={mean:.2f} (threshold={threshold:.2f})",
        )
    return RuleResult(False, 0.0, "RULE_AMOUNT_ANOMALY")


# ===========================
# RULE 2 — Frequency Spike
# ===========================

def rule_freq_spike(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags users with an abnormal number of transactions in a short window.
    Thresholds: >10 tx in 1 hour  OR  >5 tx in 10 minutes.
    """
    user_id = ctx.get("initiator_user_id")
    if not user_id:
        return RuleResult(False, 0.0, "RULE_FREQ_SPIKE")

    tx_id = ctx.get("transaction_id", "")
    now = datetime.utcnow()

    # Count in last 10 minutes
    ten_min_ago = now - timedelta(minutes=10)
    count_10m = db.execute(
        select(func.count(Transaction.transaction_id)).where(
            Transaction.initiator_user_id == user_id,
            Transaction.created_at >= ten_min_ago,
            Transaction.transaction_id != tx_id,
        )
    ).scalar() or 0

    if count_10m >= 5:
        return RuleResult(
            True, 0.30, "RULE_FREQ_SPIKE",
            f"{count_10m} transactions in last 10 min",
        )

    # Count in last 1 hour
    one_hour_ago = now - timedelta(hours=1)
    count_1h = db.execute(
        select(func.count(Transaction.transaction_id)).where(
            Transaction.initiator_user_id == user_id,
            Transaction.created_at >= one_hour_ago,
            Transaction.transaction_id != tx_id,
        )
    ).scalar() or 0

    if count_1h >= 10:
        return RuleResult(
            True, 0.30, "RULE_FREQ_SPIKE",
            f"{count_1h} transactions in last 1 hour",
        )

    # Count in last 24 hours
    one_day_ago = now - timedelta(hours=24)
    count_24h = db.execute(
        select(func.count(Transaction.transaction_id)).where(
            Transaction.initiator_user_id == user_id,
            Transaction.created_at >= one_day_ago,
            Transaction.transaction_id != tx_id,
        )
    ).scalar() or 0

    if count_24h >= 25:
        return RuleResult(
            True, 0.30, "RULE_FREQ_SPIKE",
            f"{count_24h} transactions in last 24 hours",
        )

    return RuleResult(False, 0.0, "RULE_FREQ_SPIKE")


# ===========================
# RULE 3 — New Account + Immediate Transaction
# ===========================

def rule_new_account_activity(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags transactions from accounts created less than 10 minutes ago
    with amount > 50 PYC.
    """
    user_id = ctx.get("initiator_user_id")
    amount = float(ctx.get("amount", 0))
    if not user_id:
        return RuleResult(False, 0.0, "RULE_NEW_ACCOUNT_ACTIVITY")

    user = db.get(User, user_id)
    if not user:
        return RuleResult(False, 0.0, "RULE_NEW_ACCOUNT_ACTIVITY")

    account_age = datetime.utcnow() - user.created_at
    threshold_minutes = 10
    threshold_amount = 50.0

    if account_age < timedelta(minutes=threshold_minutes) and amount > threshold_amount:
        return RuleResult(
            True, 0.20, "RULE_NEW_ACCOUNT_ACTIVITY",
            f"account_age={account_age.total_seconds():.0f}s, amount={amount:.2f}",
        )
    return RuleResult(False, 0.0, "RULE_NEW_ACCOUNT_ACTIVITY")


# ===========================
# RULE 4 — New / Rare Beneficiary
# ===========================

def rule_new_beneficiary(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags first-ever payment to a destination wallet.
    """
    user_id = ctx.get("initiator_user_id")
    dest_wallet = ctx.get("destination_wallet_id")
    amount = float(ctx.get("amount", 0))

    if not user_id or not dest_wallet:
        return RuleResult(False, 0.0, "RULE_NEW_BENEFICIARY")

    tx_id = ctx.get("transaction_id", "")
    past_count = db.execute(
        select(func.count(Transaction.transaction_id)).where(
            Transaction.initiator_user_id == user_id,
            Transaction.destination_wallet_id == dest_wallet,
            Transaction.kyc_status != "REJECTED",
            Transaction.transaction_id != tx_id,
        )
    ).scalar() or 0

    if past_count == 0:
        return RuleResult(
            True, 0.10, "RULE_NEW_BENEFICIARY",
            f"first payment to wallet {dest_wallet[:8]}…, amount={amount:.2f}",
        )
    return RuleResult(False, 0.0, "RULE_NEW_BENEFICIARY")


# ===========================
# RULE 5 — Geo Anomaly
# ===========================

def rule_geo_anomaly(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags transactions from a country never used by the user before.
    """
    user_id = ctx.get("initiator_user_id")
    country = ctx.get("country")
    if not user_id or not country:
        return RuleResult(False, 0.0, "RULE_GEO_ANOMALY")

    tx_id = ctx.get("transaction_id", "")
    # Get user's historical countries
    stmt = (
        select(Transaction.country)
        .where(
            Transaction.initiator_user_id == user_id,
            Transaction.country.isnot(None),
            Transaction.transaction_id != tx_id,
        )
        .distinct()
    )
    history = {row for row in db.execute(stmt).scalars().all()}

    if history and country.upper() not in {c.upper() for c in history if c}:
        return RuleResult(
            True, 0.20, "RULE_GEO_ANOMALY",
            f"country={country} not in history={history}",
        )
    return RuleResult(False, 0.0, "RULE_GEO_ANOMALY")


# ===========================
# RULE 6 — Odd Hour
# ===========================

def rule_odd_hour(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags transactions between 01:00 and 05:00 (deep night).
    """
    created_at = _parse_dt(ctx.get("created_at"))
    hour = created_at.hour

    if 1 <= hour <= 5:
        return RuleResult(
            True, 0.10, "RULE_ODD_HOUR",
            f"transaction at {hour}:00 (deep night)",
        )
    return RuleResult(False, 0.0, "RULE_ODD_HOUR")


# ===========================
# RULE 7 — Smurfing / Structuring
# ===========================

def rule_structuring(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags many small payments in a short window that cumulatively exceed
    a threshold, suggesting structuring to avoid detection.
    Threshold: ≥5 tx of similar small amounts (< 15 PYC each) in 30 min
    with cumulative sum > 50 PYC.
    """
    user_id = ctx.get("initiator_user_id")
    if not user_id:
        return RuleResult(False, 0.0, "RULE_STRUCTURING")

    tx_id = ctx.get("transaction_id", "")
    window = datetime.utcnow() - timedelta(minutes=30)
    stmt = (
        select(Transaction.amount)
        .where(
            Transaction.initiator_user_id == user_id,
            Transaction.created_at >= window,
            Transaction.amount <= 15,  # small amounts
            Transaction.transaction_id != tx_id,
        )
    )
    small_amounts = [float(a) for a in db.execute(stmt).scalars().all()]

    if len(small_amounts) >= 5 and sum(small_amounts) > 50:
        return RuleResult(
            True, 0.30, "RULE_STRUCTURING",
            f"{len(small_amounts)} small tx totalling {sum(small_amounts):.2f} PYC in 30min",
        )
    return RuleResult(False, 0.0, "RULE_STRUCTURING")


# ===========================
# RULE 8 — Circular Flow (A→B→A)
# ===========================

def rule_circular_flow(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags if the destination wallet recently sent money back to the
    source wallet (reverse flow within 30 minutes).
    """
    source_wallet = ctx.get("source_wallet_id")
    dest_wallet = ctx.get("destination_wallet_id")
    if not source_wallet or not dest_wallet:
        return RuleResult(False, 0.0, "RULE_CIRCULAR_FLOW")

    tx_id = ctx.get("transaction_id", "")
    window = datetime.utcnow() - timedelta(minutes=30)
    reverse_count = db.execute(
        select(func.count(Transaction.transaction_id)).where(
            Transaction.source_wallet_id == dest_wallet,
            Transaction.destination_wallet_id == source_wallet,
            Transaction.created_at >= window,
            Transaction.kyc_status != "REJECTED",
            Transaction.transaction_id != tx_id,
        )
    ).scalar() or 0

    if reverse_count > 0:
        return RuleResult(
            True, 0.35, "RULE_CIRCULAR_FLOW",
            f"{reverse_count} reverse tx from dest→src in last 30min",
        )
    return RuleResult(False, 0.0, "RULE_CIRCULAR_FLOW")


# ===========================
# RULE 9 — Activity Burst
# ===========================

def rule_activity_burst(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags a user who was inactive for 30+ days but suddenly has ≥5
    transactions in the last hour.
    """
    user_id = ctx.get("initiator_user_id")
    if not user_id:
        return RuleResult(False, 0.0, "RULE_ACTIVITY_BURST")

    tx_id = ctx.get("transaction_id", "")
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    thirty_days_ago = now - timedelta(days=30)

    # Count in last hour
    recent_count = db.execute(
        select(func.count(Transaction.transaction_id)).where(
            Transaction.initiator_user_id == user_id,
            Transaction.created_at >= one_hour_ago,
            Transaction.transaction_id != tx_id,
        )
    ).scalar() or 0

    if recent_count < 5:
        return RuleResult(False, 0.0, "RULE_ACTIVITY_BURST")

    # Count in last 30 days (excluding last hour)
    older_count = db.execute(
        select(func.count(Transaction.transaction_id)).where(
            Transaction.initiator_user_id == user_id,
            Transaction.created_at >= thirty_days_ago,
            Transaction.created_at < one_hour_ago,
            Transaction.transaction_id != tx_id,
        )
    ).scalar() or 0

    if older_count <= 2:
        return RuleResult(
            True, 0.25, "RULE_ACTIVITY_BURST",
            f"{recent_count} tx in last hour but only {older_count} in prior 30 days",
        )
    return RuleResult(False, 0.0, "RULE_ACTIVITY_BURST")


# ===========================
# RULE 10 — Recidivism
# ===========================

def rule_recidivism(
    ctx: Dict[str, Any],
    db: Session,
) -> RuleResult:
    """
    Flags users who have had past transactions blocked or flagged as fraud.
    Checks both rejected transactions and human_reviews with label='fraud'.
    """
    user_id = ctx.get("initiator_user_id")
    if not user_id:
        return RuleResult(False, 0.0, "RULE_RECIDIVISM")

    tx_id = ctx.get("transaction_id", "")

    # Count rejected transactions in last 90 days
    cutoff = datetime.utcnow() - timedelta(days=90)
    rejected_count = db.execute(
        select(func.count(Transaction.transaction_id)).where(
            Transaction.initiator_user_id == user_id,
            Transaction.kyc_status == "REJECTED",
            Transaction.created_at >= cutoff,
            Transaction.transaction_id != tx_id,
        )
    ).scalar() or 0

    # Count fraud reviews
    fraud_review_count = 0
    try:
        # Get user's transaction IDs
        tx_ids_stmt = select(Transaction.transaction_id).where(
            Transaction.initiator_user_id == user_id,
            Transaction.transaction_id != tx_id,
        )
        tx_ids = db.execute(tx_ids_stmt).scalars().all()
        if tx_ids:
            fraud_review_count = db.execute(
                select(func.count(HumanReview.review_id)).where(
                    HumanReview.transaction_id.in_(tx_ids),
                    HumanReview.label == "fraud",
                )
            ).scalar() or 0
    except Exception:
        logger.warning("Could not query human_reviews for recidivism check")

    total_flags = rejected_count + fraud_review_count
    if total_flags >= 1:
        return RuleResult(
            True, 0.30, "RULE_RECIDIVISM",
            f"past flags: {rejected_count} rejected + {fraud_review_count} fraud reviews",
        )
    return RuleResult(False, 0.0, "RULE_RECIDIVISM")


# ---------------------------------------------------------------------------
# Registry: all rules in evaluation order
# ---------------------------------------------------------------------------

ALL_RULES = [
    rule_amount_anomaly,
    rule_freq_spike,
    rule_new_account_activity,
    rule_new_beneficiary,
    rule_geo_anomaly,
    rule_odd_hour,
    rule_structuring,
    rule_circular_flow,
    rule_activity_burst,
    rule_recidivism,
]
