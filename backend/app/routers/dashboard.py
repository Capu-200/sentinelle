from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..auth import require_active_user
from ..database import get_db
from ..models import Contact, Transaction, User, Wallet
from ..schemas import (
    ContactSummary,
    DashboardData,
    TransactionResponseLite,
    UserProfileResponse,
    WalletResponse,
)
from ..services.statuses import map_kyc_status_to_public

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardData)
async def get_dashboard_summary(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
) -> DashboardData:
    wallets_stmt = select(Wallet).where(Wallet.user_id == current_user.user_id)
    wallets = db.execute(wallets_stmt).scalars().all()
    wallet = wallets[0] if wallets else None
    user_wallet_ids = [w.wallet_id for w in wallets]

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

