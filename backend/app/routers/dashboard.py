from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel # Added for DashboardData definition

from ..database import get_db
from ..models import User, Wallet, Transaction, Contact # Added Contact
from ..auth import get_current_user
from ..schemas import UserProfileResponse, WalletResponse, TransactionResponseLite # Removed DashboardData, as it's redefined below

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

# Redefined DashboardData as per instruction
class DashboardData(BaseModel):
    user: dict
    wallet: Optional[dict]
    recent_transactions: List[TransactionResponseLite]
    contacts: List[dict] # Added field

@router.get("/", response_model=DashboardData)
async def get_dashboard_summary( # Added async
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

    # Fallback if wallets relationship is not loaded
    if not user_wallet_ids and wallet:
       user_wallet_ids = [wallet.wallet_id]

    tx_stmt = (
        select(Transaction)
        .where(
            (Transaction.initiator_user_id == current_user.user_id) |
            (Transaction.source_wallet_id.in_(user_wallet_ids)) | # Updated to use user_wallet_ids
            (Transaction.destination_wallet_id.in_(user_wallet_ids)) # Updated to use user_wallet_ids
        )
        .order_by(Transaction.created_at.desc())
        .limit(5)
    )
    transactions = db.execute(tx_stmt).scalars().all()
    
    tx_list = []
    for tx in transactions:
        # Determine direction relative to current user
        is_incoming = tx.destination_wallet_id in user_wallet_ids # Changed logic
        direction = "INCOMING" if is_incoming else "OUTGOING" # Changed logic
        
        # Determine Recipient/Sender Name
        display_name = "Inconnu"
        if direction == "OUTGOING":
             display_name = tx.description or (tx.destination_wallet_id if tx.destination_wallet_id else "Virement externe")
        else:
             display_name = f"Virement reçu" # Could be improved with Sender Name lookup

        tx_list.append(
            TransactionResponseLite(
                transaction_id=tx.transaction_id,
                amount=float(tx.amount),
                currency=tx.currency,
                transaction_type=tx.transaction_type,
                direction=direction,
                status=tx.kyc_status,
                recipient_name=display_name, # Updated to use display_name
                created_at=tx.created_at
            )
        )

    # 3. Fetch Contacts
    contacts_stmt = select(Contact).where(Contact.user_id == current_user.user_id).order_by(Contact.name)
    contacts = db.execute(contacts_stmt).scalars().all()
    contacts_data = [
        {
            "name": c.name,
            "email": c.email,
            "iban": c.iban,
            "is_internal": c.linked_user_id is not None
        }
        for c in contacts
    ]

    # 4. Construct Response
    return { # Changed to dict as per new DashboardData schema
        "user": { # Changed to dict as per new DashboardData schema
            "display_name": current_user.display_name or current_user.full_name,
            "email": current_user.email,
            "risk_level": current_user.risk_level or "LOW",
            "trust_score": current_user.trust_score or 100
        },
        "wallet": wallet_data,
        "recent_transactions": tx_list,
        "contacts": contacts_data # Added contacts
    }
