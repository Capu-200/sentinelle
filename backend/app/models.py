from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from decimal import Decimal
from sqlalchemy import Column, JSON, Text # For JSON/Text fields

# Shared properties
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    is_active: bool = Field(default=True)
    risk_level: Optional[str] = Field(default="LOW")
    country_home: Optional[str] = Field(default="FR")
    trust_score: Optional[int] = Field(default=100)

class WalletBase(SQLModel):
    currency: str = Field(default="PYC")
    balance: Decimal = Field(default=0.0, max_digits=15, decimal_places=2)
    kyc_status: str = Field(default="PENDING")

class TransactionBase(SQLModel):
    amount: Decimal = Field(default=0.0, max_digits=15, decimal_places=2)
    currency: str = Field(default="PYC")
    status: str = Field(default="PENDING") # Maps to kyc_status or internal status
    created_at: datetime = Field(default_factory=datetime.utcnow)
    recipient_name: Optional[str] = None # Helper for display

# Database Models
class User(UserBase, table=True):
    __tablename__ = "users"
    
    # Matching Alembic: user_id VARCHAR(50) PRIMARY KEY
    user_id: Optional[str] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_risk_update_at: Optional[datetime] = None
    
    # Relationships
    wallets: List["Wallet"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="initiator_user")

class Wallet(WalletBase, table=True):
    __tablename__ = "wallets"
    
    wallet_id: Optional[str] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="users.user_id")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_transaction_at: Optional[datetime] = None
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="wallets")

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"
    
    transaction_id: Optional[str] = Field(default=None, primary_key=True)
    initiator_user_id: Optional[str] = Field(default=None, foreign_key="users.user_id")
    source_wallet_id: Optional[str] = Field(default=None, foreign_key="wallets.wallet_id")
    destination_wallet_id: Optional[str] = Field(default=None, foreign_key="wallets.wallet_id")
    
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    currency: str
    transaction_type: str = Field(default="TRANSFER")
    direction: str = Field(default="OUTGOING") 
    country: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    kyc_status: str = Field(default="PENDING") 
    
    initiator_user: Optional[User] = Relationship(back_populates="transactions")
    # For now we won't strictly enforce relationship to ai_decisions in Object Model to avoid complexity if not used

# These tables must exist for the backend logic to work, even if we don't use them via ORM
class AIDecision(SQLModel, table=True):
    __tablename__ = "ai_decisions"
    
    decision_id: Optional[str] = Field(default=None, primary_key=True)
    transaction_id: Optional[str] = Field(default=None, foreign_key="transactions.transaction_id")
    fraud_score: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=4)
    decision: Optional[str] = None
    reasons: Optional[str] = None
    model_version: Optional[str] = None
    latency_ms: Optional[int] = None
    threshold_used: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=4)
    features_snapshot: Optional[dict] = Field(default=None, sa_column=Column(JSON)) # Using JSON column
    created_at: datetime = Field(default_factory=datetime.utcnow)

class WalletLedger(SQLModel, table=True):
    __tablename__ = "wallet_ledger"
    
    ledger_id: Optional[str] = Field(default=None, primary_key=True)
    wallet_id: Optional[str] = Field(default=None, foreign_key="wallets.wallet_id")
    transaction_id: Optional[str] = Field(default=None, foreign_key="transactions.transaction_id")
    entry_type: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, max_digits=15, decimal_places=2)
    balance_after: Optional[Decimal] = Field(default=None, max_digits=15, decimal_places=2)
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HumanReview(SQLModel, table=True):
    __tablename__ = "human_reviews"
    
    review_id: Optional[str] = Field(default=None, primary_key=True)
    transaction_id: Optional[str] = Field(default=None, foreign_key="transactions.transaction_id")
    analyst_id: Optional[str] = None
    action: Optional[str] = None
    label: Optional[str] = None
    comment: Optional[str] = None # TEXT
    final_status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Contact(SQLModel, table=True):
    __tablename__ = "contacts"
    
    contact_id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.user_id") # Owner of the contact
    
    name: str
    email: Optional[str] = None
    iban: Optional[str] = None
    
    linked_user_id: Optional[str] = Field(default=None, foreign_key="users.user_id") # If internal user
    created_at: datetime = Field(default_factory=datetime.utcnow)
