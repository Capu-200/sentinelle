from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from ..database import get_db
from ..models import User, Wallet, Transaction
from ..auth import get_current_user
from ..schemas import DashboardData, UserProfileResponse, WalletResponse, TransactionResponseLite

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

@router.get("/", response_model=DashboardData)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Get Wallet
    # Assuming user has at least one wallet. If not, return None or create one?
    # Auth register creates one, so it should exist.
    wallet_stmt = select(Wallet).where(Wallet.user_id == current_user.user_id)
    wallet = db.execute(wallet_stmt).scalars().first()
    
    wallet_data = None
    if wallet:
        wallet_data = WalletResponse(
            wallet_id=wallet.wallet_id,
            balance=float(wallet.balance),
            currency=wallet.currency,
            kyc_status=wallet.kyc_status
        )
    
    # 2. Get Recent Transactions
    # We want transactions where user is initiator OR user owns the wallet
    # Simplified: fetch where initiator_user_id is current_user.user_id
    tx_stmt = (
        select(Transaction)
        .where(Transaction.initiator_user_id == current_user.user_id)
        .order_by(Transaction.created_at.desc())
        .limit(5)
    )
    transactions = db.execute(tx_stmt).scalars().all()
    
    tx_list = []
    for tx in transactions:
        tx_list.append(
            TransactionResponseLite(
                transaction_id=tx.transaction_id,
                amount=float(tx.amount),
                currency=tx.currency,
                transaction_type=tx.transaction_type,
                direction=tx.direction,
                status=tx.kyc_status, # or mapped status
                recipient_name=tx.description or "Unknown Data", # In real app, join with destination User
                created_at=tx.created_at
            )
        )

    # 3. Construct Response
    return DashboardData(
        user=UserProfileResponse(
            user_id=current_user.user_id,
            email=current_user.email,
            full_name=current_user.full_name,
            display_name=current_user.display_name,
            risk_level=current_user.risk_level or "LOW",
            trust_score=current_user.trust_score or 100
        ),
        wallet=wallet_data,
        recent_transactions=tx_list
    )
