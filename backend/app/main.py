"""
FastAPI Application - Fraud Detection Backend
"""
import os
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import httpx
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



from pydantic import BaseModel
from sqlalchemy import text
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, select, Session

from app.database import get_db, engine
from .routers import auth, dashboard, contacts
from .auth import get_current_user
from decimal import Decimal
from .models import User, Transaction, Wallet, WalletLedger, Contact # Added Contact
from .schemas import TransactionResponseLite 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title="Payon Fraud Detection API",
    description="API backend pour la détection de fraude bancaire",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "https://sentinelle.vercel.app",
        "https://sentinelle-git-main-capu-200s-projects.vercel.app",
        "https://sentinelle-4fl700lr2-capu-200s-projects.vercel.app" # Your specific deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(contacts.router)

# Configuration ML Engine
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app")  # Cloud Run URL


# ========== MODÈLES PYDANTIC ==========

class TransactionRequest(BaseModel):
    """Requête de transaction."""
    transaction_id: Optional[str] = None
    amount: float
    currency: str
    source_wallet_id: str
    destination_wallet_id: Optional[str] = None
    transaction_type: str
    direction: str
    created_at: Optional[str] = None
    # Autres champs optionnels
    provider: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    initiator_user_id: Optional[str] = None # Added for linking to user
    recipient_email: Optional[str] = None # Added for resolving destination wallet


class TransactionResponse(BaseModel):
    """Réponse de transaction avec scoring."""
    transaction_id: str
    risk_score: float
    decision: str
    reasons: list[str]
    model_version: str


# ========== FONCTIONS UTILITAIRES ==========

async def enrich_transaction_with_historical_features(
    transaction: dict,
    db_session
) -> dict:
    """
    Enrichit une transaction avec les features historiques depuis la DB.
    
    Pour l'instant, version simplifiée. À compléter avec les vraies requêtes SQL.
    """
    source_wallet_id = transaction.get("source_wallet_id")
    created_at = transaction.get("created_at", datetime.utcnow().isoformat())
    
    # Features historiques basiques (à compléter avec les vraies requêtes)
    historical_features = {
        # Exemples - à remplacer par de vraies requêtes SQL
        "avg_amount_30d": None,
        "tx_last_10min": 0,
        "is_new_beneficiary": False,
        "user_country_history": [],
        "blocked_tx_last_24h": 0,
        # Features ML (à compléter)
        "src_tx_count_out_1h": 0,
        "src_tx_amount_mean_out_7d": None,
        "is_new_destination_30d": False,
    }
    
    # Features transactionnelles basiques
    # Features transactionnelles complètes (alignées sur la doc ML Engine)
    current_dt = datetime.fromisoformat(transaction.get("created_at") or datetime.utcnow().isoformat())
    amount_val = float(transaction.get("amount", 0))
    
    transactional_features = {
        "amount": amount_val,
        "log_amount": __import__("math").log(1 + amount_val),
        "currency_is_pyc": 1 if transaction.get("currency") == "PYC" else 0, # Force integer 1/0
        "direction_outgoing": 1 if str(transaction.get("direction")).upper() == "OUTGOING" else 0,
        "hour_of_day": current_dt.hour,
        "day_of_week": current_dt.weekday(), # 0=Monday
        "transaction_type_TRANSFER": 1 # Hardcoded for now as we only do transfers
    }
    
    # Récupérer le solde réel du wallet source
    source_wallet_balance = None
    if source_wallet_id:
        wallet = db_session.get(Wallet, source_wallet_id)
        if wallet:
            source_wallet_balance = float(wallet.balance)

    # Construire la transaction enrichie (Structure Root attendue par ML Engine V2)
    # Injecter les features DANS l'objet transaction (Format requis par ML Engine)
    transaction["features"] = {
        "transactional": transactional_features,
        "historical": historical_features,
    }

    # Construire la transaction enrichie (Structure Root attendue par ML Engine V2)
    enriched = {
        "schema_version": "1.0.0",
        "transaction": transaction,
        "context": {
            "source_wallet": {
                "balance": source_wallet_balance, 
                "status": "ACTIVE"
            },
            "user": {"status": "ACTIVE", "risk_level": "LOW"},
            "destination_wallet": {"status": "ACTIVE"},
        }
    }
    
    return enriched


async def call_ml_engine(enriched_transaction: dict) -> dict:
    """
    Appelle le ML Engine pour scorer la transaction.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send the enriched structure directly as root payload
            payload = enriched_transaction
            
            tx_id = enriched_transaction.get("transaction", {}).get("transaction_id", "unknown")
            logger.info(f"ML_ENGINE_REQ: Transaction {tx_id} - Sending payload to {ML_ENGINE_URL}")
            # logger.debug(f"Payload: {payload}") # Uncomment for full payload debug
            
            response = await client.post(
                f"{ML_ENGINE_URL}/score",
                json=payload,
            )
            
            if response.status_code != 200:
                logger.error(f"ML_ENGINE_ERROR: Status {response.status_code} - Body: {response.text}")
                
            response.raise_for_status()
            result = response.json()
            
            decision = result.get("decision", "UNKNOWN")
            reasons = result.get("reasons", [])
            logger.info(f"ML_ENGINE_RESP: Transaction {tx_id} - Decision: {decision} - Reasons: {reasons}")
            
            return result
    except httpx.HTTPError as e:
        # Fallback for demo/dev if ML Engine is down -> FAIL CLOSED (BLOCK)
        logger.critical(f"ML_ENGINE_FAILURE: Network Error: {e}. Defaulting to BLOCK.")
        return {
            "risk_score": 1.0,
            "decision": "BLOCK",
            "reasons": ["ML_ENGINE_UNAVAILABLE"],
            "model_version": "fallback"
        }
    except Exception as e:
        logger.critical(f"ML_ENGINE_FAILURE: Unexpected Error: {e}. Defaulting to BLOCK.")
        return {
            "risk_score": 1.0,
            "decision": "BLOCK",
            "reasons": ["ML_ENGINE_UNAVAILABLE"],
            "model_version": "fallback"
        }



async def save_ai_decision(
    transaction_id: str,
    scoring_result: dict,
    db_session
) -> None:
    """
    Sauvegarde la décision AI dans la table ai_decisions.
    """
    decision_id = str(uuid.uuid4())
    
    db_session.execute(
            text("""
                INSERT INTO ai_decisions (
                    decision_id,
                    transaction_id,
                    fraud_score,
                    decision,
                    reasons,
                    model_version,
                    latency_ms,
                    threshold_used,
                    features_snapshot,
                    created_at
                ) VALUES (
                    :decision_id,
                    :transaction_id,
                    :fraud_score,
                    :decision,
                    :reasons,
                    :model_version,
                    :latency_ms,
                    :threshold_used,
                    :features_snapshot,
                    :created_at
                )
            """),
            {
                "decision_id": decision_id,
                "transaction_id": transaction_id,
                "fraud_score": scoring_result.get("risk_score", 0.0),
                "decision": scoring_result.get("decision", "APPROVE"),
                "reasons": ", ".join(scoring_result.get("reasons", [])),
                "model_version": scoring_result.get("model_version", "unknown"),
                "latency_ms": None,  # À calculer si disponible
                "threshold_used": None,  # À récupérer si disponible
                "features_snapshot": None,  # JSONB - à ajouter si nécessaire
                "created_at": datetime.utcnow(),
            }
        )
    # Note: commit is handled by caller or dependency injection usually, 
    # but here we are in a route handler, so we can commit.
    # However, if save_transaction also commits, we should be careful.



# ========== LOGIQUE LEDGER ==========

def execute_balance_movement(
    db: Session,
    wallet_id: str,
    amount: float,
    transaction_id: str,
    entry_type: str, # DEBIT or CREDIT
) -> float:
    """Met à jour le solde d'un wallet et crée une entrée ledger."""
    wallet = db.get(Wallet, wallet_id)
    if not wallet:
        raise ValueError(f"Wallet {wallet_id} introuvable")
    
    amount_decimal = Decimal(str(amount))
    
    if entry_type == "DEBIT":
        if wallet.balance < amount_decimal:
            raise ValueError("Solde insuffisant")
        wallet.balance -= amount_decimal
    elif entry_type == "CREDIT":
        wallet.balance += amount_decimal
    
    wallet.updated_at = datetime.utcnow()
    wallet.last_transaction_at = datetime.utcnow()
    db.add(wallet)
    
    # Créer entrée Ledger
    ledger_entry = WalletLedger(
        ledger_id=str(uuid.uuid4()),
        wallet_id=wallet_id,
        transaction_id=transaction_id,
        entry_type=entry_type,
        amount=amount_decimal,
        balance_after=wallet.balance,
        executed_at=datetime.utcnow()
    )
    db.add(ledger_entry)
    
    return float(wallet.balance)


# ========== ROUTES ==========

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Payon Fraud Detection API",
        "version": "1.0.0",
        "ml_engine_url": ML_ENGINE_URL,
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Vérifier la connexion au ML Engine
    ml_engine_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ML_ENGINE_URL}/health")
            if response.status_code == 200:
                ml_engine_status = "healthy"
            else:
                ml_engine_status = "unhealthy"
    except Exception:
        ml_engine_status = "unreachable"
    
    return {
        "status": "healthy",
        "ml_engine": ml_engine_status,
    }



@app.get("/transactions", response_model=list[TransactionResponseLite])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    skip: int = 0
):
    """
    Récupère l'historique des transactions de l'utilisateur connecté.
    (Initiateur OU Destinataire)
    """
    user_wallets_stmt = select(Wallet.wallet_id).where(Wallet.user_id == current_user.user_id)
    user_wallet_ids = db.execute(user_wallets_stmt).scalars().all()
    
    # Fail safe if user has no wallet yet
    if not user_wallet_ids:
        user_wallet_ids = []

    stmt = (
        select(Transaction)
        .where(
            (Transaction.initiator_user_id == current_user.user_id) |
            (Transaction.source_wallet_id.in_(user_wallet_ids)) |
            (Transaction.destination_wallet_id.in_(user_wallet_ids))
        )
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    transactions = db.execute(stmt).scalars().all()
    
    return [
        TransactionResponseLite(
            transaction_id=tx.transaction_id,
            amount=float(tx.amount),
            currency=tx.currency,
            transaction_type=tx.transaction_type,
            direction="INCOMING" if tx.destination_wallet_id in user_wallet_ids and tx.source_wallet_id not in user_wallet_ids else tx.direction,
            status=tx.kyc_status,
            recipient_name=tx.description or "Destinataire Inconnu",
            created_at=tx.created_at
        ) for tx in transactions
    ]


@app.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction_req: TransactionRequest,
    db: Session = Depends(get_db)
):
    """
    Crée une transaction et la score via le ML Engine.
    Met à jour les soldes si APPROVE.
    """
    transaction_id = transaction_req.transaction_id or str(uuid.uuid4())
    current_time = datetime.utcnow()
    
    # 0. Résolution du Wallet de Destination (si email fourni)
    destination_wallet_id = transaction_req.destination_wallet_id
    if not destination_wallet_id and transaction_req.recipient_email:
        # Chercher l'utilisateur par email (Normalisé)
        dest_email = transaction_req.recipient_email.lower()
        dest_user_stmt = select(User).where(User.email == dest_email)
        dest_user = db.execute(dest_user_stmt).scalars().first()
        
        if dest_user:
            # Chercher son wallet (le premier pour l'instant)
            dest_wallet_stmt = select(Wallet).where(Wallet.user_id == dest_user.user_id)
            dest_wallet = db.execute(dest_wallet_stmt).scalars().first()
            if dest_wallet:
                destination_wallet_id = dest_wallet.wallet_id

    # Self-transfer check
    if destination_wallet_id and destination_wallet_id == transaction_req.source_wallet_id:
        raise HTTPException(status_code=400, detail="Virement impossible vers le même compte.")



    # 1. Vérification Solde (Pre-check)
    if transaction_req.direction == "OUTGOING":
        source_wallet = db.get(Wallet, transaction_req.source_wallet_id)
        if not source_wallet:
             raise HTTPException(status_code=404, detail="Wallet source introuvable")
        if source_wallet.balance < Decimal(str(transaction_req.amount)):
             raise HTTPException(status_code=400, detail="Solde insuffisant")

    # 2. Sauvegarder la Transaction (PENDING)
    new_tx = Transaction(
        transaction_id=transaction_id,
        amount=Decimal(str(transaction_req.amount)),
        currency=transaction_req.currency,
        source_wallet_id=transaction_req.source_wallet_id,
        destination_wallet_id=destination_wallet_id, # Utilisation de l'ID résolu
        transaction_type=transaction_req.transaction_type,
        direction=transaction_req.direction,
        country=transaction_req.country,
        city=transaction_req.city,
        description=transaction_req.description,
        initiator_user_id=transaction_req.initiator_user_id,
        created_at=current_time,
        kyc_status="PENDING"
    )
    db.add(new_tx)
    # On commit ici pour avoir l'ID transaction dispo pour les logs, 
    # mais attention si crash après -> transaction PENDING orpheline (acceptable)
    db.commit() 
    db.refresh(new_tx)
    
    # 3. Enrichissement & Scoring IA
    transaction_dict = transaction_req.dict()
    transaction_dict["transaction_id"] = transaction_id
    transaction_dict["created_at"] = transaction_dict.get("created_at") or current_time.isoformat()
    
    enriched_transaction = await enrich_transaction_with_historical_features(transaction_dict, db)
    scoring_result = await call_ml_engine(enriched_transaction)
    
    decision = scoring_result.get("decision", "APPROVE")
    new_tx.kyc_status = "VALIDATED" if decision == "APPROVE" else "REJECTED"
    if decision == "REVIEW":
        new_tx.kyc_status = "REVIEW"
    
    db.add(new_tx)
    
    # 4. Sauvegarde Décision IA
    try:
        await save_ai_decision(transaction_id, scoring_result, db)
    except Exception as e:
        print(f"Erreur save_ai_decision: {e}")

    # 5. Exécution Financière (Ledger) si VALIDATED
    if new_tx.kyc_status == "VALIDATED":
        try:
            # Débit Source
            if new_tx.direction == "OUTGOING":
                execute_balance_movement(
                    db, 
                    wallet_id=new_tx.source_wallet_id, 
                    amount=transaction_req.amount, 
                    transaction_id=transaction_id, 
                    entry_type="DEBIT"
                )
            
            # Crédit Destination (si wallet interne)
            if new_tx.destination_wallet_id:
                execute_balance_movement(
                    db,
                    wallet_id=new_tx.destination_wallet_id,
                    amount=transaction_req.amount,
                    transaction_id=transaction_id,
                    entry_type="CREDIT"
                )
                
        except ValueError as e:
            # Rollback transaction status if ledger fails
            new_tx.kyc_status = "FAILED"
            db.add(new_tx)
            raise HTTPException(status_code=400, detail=str(e))
    
    db.commit()
    
    return TransactionResponse(
        transaction_id=transaction_id,
        risk_score=scoring_result.get("risk_score", 0.0),
        decision=decision,
        reasons=scoring_result.get("reasons", []),
        model_version=scoring_result.get("model_version", "unknown"),
    )
