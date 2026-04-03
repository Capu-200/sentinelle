from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..auth import require_active_user
from ..database import get_db
from ..auth import require_active_user, get_current_user
from ..schemas import (
    ContactSummary,
    DashboardData,
    TransactionResponseLite,
    UserProfileResponse,
    WalletResponse,
)
from ..services.statuses import map_kyc_status_to_public
from ..models import User, Wallet, Transaction, Contact, AIDecision

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardData)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Get Wallet
    # Assuming user has at least one wallet. If not, return None or create one?
    # Auth register creates one, so it should exist.
    stmt = select(Wallet).where(Wallet.user_id == current_user.user_id) # Changed wallet_stmt to stmt
    wallet = db.execute(stmt).scalars().first()
    
    wallet_data = None
    if wallet:
        wallet_data = { # Changed to dict as per new DashboardData schema
            "wallet_id": wallet.wallet_id,
            "balance": float(wallet.balance),
            "currency": wallet.currency,
            "kyc_status": wallet.kyc_status
        }
    
    # 2. Get Recent Transactions (Last 5)
    # Fetch where user is initiator OR user owns source/destination wallet
    user_wallet_ids = [w.wallet_id for w in current_user.wallets] if current_user.wallets else []

    wallet_data = (
        WalletResponse(
            wallet_id=wallet.wallet_id,
            balance=float(wallet.balance),
            currency=wallet.currency,
            kyc_status=wallet.kyc_status,
        )
        if wallet
        else None
    )

    tx_stmt = (
        select(Transaction)
        .where(
            (Transaction.initiator_user_id == current_user.user_id)
            | (Transaction.source_wallet_id.in_(user_wallet_ids))
            | (Transaction.destination_wallet_id.in_(user_wallet_ids))
        )
        .order_by(Transaction.created_at.desc())
        .limit(5)
    )
    transactions = db.execute(tx_stmt).scalars().all()

    tx_list: List[TransactionResponseLite] = []
    for tx in transactions:
        is_incoming = tx.destination_wallet_id in user_wallet_ids and (
            not tx.source_wallet_id or tx.source_wallet_id not in user_wallet_ids
        )
        direction = "INCOMING" if is_incoming else "OUTGOING"
        display_name = tx.description or (
            "Virement recu" if is_incoming else "Virement externe"
        )

        # Récupérer les raisons de décision IA
        reasons_list = None
        decision_stmt = select(AIDecision).where(AIDecision.transaction_id == tx.transaction_id).order_by(AIDecision.created_at.desc())
        decision = db.execute(decision_stmt).scalars().first()
        if decision and decision.reasons:
            reasons_list = [r.strip() for r in decision.reasons.split(",") if r.strip()]

        tx_list.append(
            TransactionResponseLite(
                transaction_id=tx.transaction_id,
                amount=float(tx.amount),
                currency=tx.currency,
                transaction_type=tx.transaction_type,
                direction=direction,
                status=map_kyc_status_to_public(tx.kyc_status),
                recipient_name=display_name,
                created_at=tx.created_at,
                reasons=reasons_list
            )
        )

    contacts_stmt = (
        select(Contact)
        .where(Contact.user_id == current_user.user_id)
        .order_by(Contact.name)
    )
    contacts = db.execute(contacts_stmt).scalars().all()
    contacts_data = [
        ContactSummary(
            name=c.name,
            email=c.email,
            iban=c.iban,
            is_internal=c.linked_user_id is not None,
        )
        for c in contacts
    ]

    user_profile = UserProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        display_name=current_user.display_name or current_user.full_name,
        risk_level=current_user.risk_level or "LOW",
        trust_score=current_user.trust_score or 100,
    )

    return DashboardData(
        user=user_profile,
        wallet=wallet_data,
        recent_transactions=tx_list,
        contacts=contacts_data,
    )

