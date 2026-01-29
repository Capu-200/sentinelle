from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from decimal import Decimal

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Dashboard & Model Schemas ---

class WalletResponse(BaseModel):
    wallet_id: str
    balance: float
    currency: str
    kyc_status: str

class TransactionResponseLite(BaseModel):
    transaction_id: str
    amount: float
    currency: str
    transaction_type: str
    direction: str
    status: str
    recipient_name: Optional[str] = "Unknown"
    recipient_email: Optional[str] = None
    created_at: datetime
    source_country: Optional[str] = None
    destination_country: Optional[str] = None
    comment: Optional[str] = None

class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    display_name: Optional[str]
    risk_level: str
    trust_score: int

class DashboardData(BaseModel):
    user: UserProfileResponse
    wallet: Optional[WalletResponse]
    recent_transactions: List[TransactionResponseLite]
