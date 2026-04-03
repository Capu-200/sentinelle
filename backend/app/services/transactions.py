"""
Shared transaction utilities (ledger updates, AI decision persistence).
"""
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import select
from sqlmodel import Session

from ..models import (
    AIDecision,
    Transaction,
    Wallet,
    WalletLedger,
)

logger = logging.getLogger("transaction-service")


class LedgerExecutionError(Exception):
    """Raised when ledger movements cannot be completed."""



def execute_balance_movement(
    db: Session,
    wallet_id: str,
    amount: float,
    transaction_id: str,
    entry_type: str,
) -> float:
    """Update wallet balance and insert a ledger entry."""
    wallet = db.get(Wallet, wallet_id)
    if not wallet:
        raise ValueError(f"Wallet {wallet_id} introuvable")

    amount_decimal = Decimal(str(amount))

    if entry_type.upper() == "DEBIT":
        if wallet.balance < amount_decimal:
            raise ValueError("Solde insuffisant")
        wallet.balance -= amount_decimal
    elif entry_type.upper() == "CREDIT":
        wallet.balance += amount_decimal
    else:
        raise ValueError(f"entry_type inconnu: {entry_type}")

    wallet.updated_at = datetime.utcnow()
    wallet.last_transaction_at = datetime.utcnow()
    db.add(wallet)

    ledger_entry = WalletLedger(
        ledger_id=str(uuid.uuid4()),
        wallet_id=wallet_id,
        transaction_id=transaction_id,
        entry_type=entry_type.upper(),
        amount=amount_decimal,
        balance_after=wallet.balance,
        executed_at=datetime.utcnow(),
    )
    db.add(ledger_entry)

    logger.info(
        "Ledger %s wallet=%s amount=%s new_balance=%s",
        entry_type,
        wallet_id,
        amount,
        float(wallet.balance),
    )

    return float(wallet.balance)


def normalize_reasons(reasons: Any) -> List[str]:
    if not reasons:
        return []
    if isinstance(reasons, list):
        return [str(r) for r in reasons]
    if isinstance(reasons, str):
        return [r.strip() for r in reasons.split(",") if r.strip()]
    return [str(reasons)]


def save_ai_decision(
    db: Session,
    transaction_id: str,
    decision_payload: Dict[str, Any],
) -> AIDecision:
    """Insert or update an AI decision row."""
    reasons = normalize_reasons(decision_payload.get("reasons"))
    decision_id = decision_payload.get("decision_id") or str(uuid.uuid4())

    stmt = select(AIDecision).where(AIDecision.transaction_id == transaction_id)
    existing = db.execute(stmt).scalars().first()

    if existing:
        decision_row = existing
    else:
        decision_row = AIDecision(decision_id=decision_id, transaction_id=transaction_id)

    fraud_score = decision_payload.get("fraud_score")
    if fraud_score is None:
        fraud_score = 0.0
    decision_row.fraud_score = Decimal(str(fraud_score))
    decision_row.decision = decision_payload.get("decision", "REVIEW")
    reasons_str = ", ".join(reasons)
    decision_row.reasons = reasons_str[:97] + "..." if len(reasons_str) > 100 else reasons_str
    decision_row.model_version = decision_payload.get("model_version", "unknown")
    decision_row.features_snapshot = decision_payload.get("features_snapshot")
    decision_row.created_at = datetime.utcnow()

    db.add(decision_row)

    logger.info(
        "Saved AI decision tx=%s decision=%s score=%.4f",
        transaction_id,
        decision_row.decision,
        float(decision_row.fraud_score or 0.0),
    )

    return decision_row


def apply_decision_to_transaction(
    db: Session,
    transaction: Transaction,
    decision_payload: Dict[str, Any],
) -> None:
    """Update transaction status based on ML decision, execute ledger if needed."""
    decision = (decision_payload.get("decision") or "REVIEW").upper()
    amount = float(transaction.amount)

    if decision == "APPROVE":
        if transaction.kyc_status == "VALIDATED":
            logger.info(
                "Transaction %s already validated, skipping ledger",
                transaction.transaction_id,
            )
        else:
            try:
                if transaction.direction == "OUTGOING":
                    execute_balance_movement(
                        db,
                        wallet_id=transaction.source_wallet_id,
                        amount=amount,
                        transaction_id=transaction.transaction_id,
                        entry_type="DEBIT",
                    )
                if transaction.destination_wallet_id:
                    execute_balance_movement(
                        db,
                        wallet_id=transaction.destination_wallet_id,
                        amount=amount,
                        transaction_id=transaction.transaction_id,
                        entry_type="CREDIT",
                    )
                transaction.kyc_status = "VALIDATED"
            except ValueError as exc:
                logger.error(
                    "Ledger execution failed for tx=%s reason=%s",
                    transaction.transaction_id,
                    exc,
                )
                raise LedgerExecutionError(str(exc)) from exc
    elif decision == "REVIEW":
        transaction.kyc_status = "REVIEW"
    else:
        transaction.kyc_status = "REJECTED"

    db.add(transaction)
    logger.info(
        "Transaction %s status updated to %s",
        transaction.transaction_id,
        transaction.kyc_status,
    )
