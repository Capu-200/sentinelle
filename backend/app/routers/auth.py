from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from ..database import get_db
from ..models import User, Wallet
from ..schemas import UserCreate, UserLogin, Token
from ..auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import uuid

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Normalize email
    normalized_email = user.email.lower()
    
    # Check if user exists
    statement = select(User).where(User.email == normalized_email)
    existing_user = db.execute(statement).scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    
    new_user = User(
        user_id=user_id,
        email=normalized_email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        display_name=user.full_name.split(" ")[0] if user.full_name else "User",
        risk_level="LOW",
        trust_score=100
    )
    db.add(new_user)
    
    # Create default wallet
    wallet_id = str(uuid.uuid4())
    new_wallet = Wallet(
        wallet_id=wallet_id,
        user_id=user_id,
        currency="EUR",
        balance=1000.00, # Welcome bonus / Initial balance check
        kyc_status="VERIFIED"
    )
    db.add(new_wallet)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    db.refresh(new_user)
    
    # Generate token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    normalized_email = user_credentials.email.lower()
    statement = select(User).where(User.email == normalized_email)
    user = db.execute(statement).scalars().first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
