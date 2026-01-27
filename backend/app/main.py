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
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, select, Session

from app.database import get_db, engine
from .routers import auth, dashboard
from .auth import get_current_user
from decimal import Decimal
from .models import User, Transaction, Wallet, WalletLedger
from .schemas import TransactionResponseLite 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title="Sentinelle Fraud Detection API",
    description="API backend pour la détection de fraude bancaire",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)

# Configuration ML Engine
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "http://localhost:8080")  # À configurer avec l'URL Cloud Run


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
    transactional_features = {
        "amount": transaction.get("amount", 0),
        "log_amount": __import__("math").log(1 + transaction.get("amount", 0)),
        "currency_is_pyc": transaction.get("currency") == "PYC",
        "direction_outgoing": 1 if transaction.get("direction") == "outgoing" else 0,
    }
    
    # Construire la transaction enrichie
    enriched = {
        "schema_version": "1.0.0",
        "transaction": transaction,
        "context": {
            # À compléter avec les vraies données depuis DB
            "source_wallet": {"balance": None, "status": None},
            "user": {"status": None, "risk_level": None},
            "destination_wallet": {"status": None},
        },
        "features": {
            "transactional": transactional_features,
            "historical": historical_features,
        },
    }
    
    return enriched


async def call_ml_engine(enriched_transaction: dict) -> dict:
    """
    Appelle le ML Engine pour scorer la transaction.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ML_ENGINE_URL}/score",
                json={
                    "transaction": enriched_transaction,
                    "context": enriched_transaction.get("context", {}),
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        # Fallback for demo/dev if ML Engine is down
        print(f"ML Engine Error: {e}. Using fallback mock.")
        return {
            "risk_score": 0.05,
            "decision": "APPROVE",
            "reasons": ["fallback_mock"],
            "model_version": "v0-mock"
        }
    except Exception as e:
        print(f"Connection Error: {e}. Using fallback mock.")
        return {
            "risk_score": 0.05,
            "decision": "APPROVE",
            "reasons": ["fallback_mock"],
            "model_version": "v0-mock"
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
        "message": "Sentinelle Fraud Detection API",
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
    """
    stmt = (
        select(Transaction)
        .where(
            (Transaction.initiator_user_id == current_user.user_id) |
            (Transaction.source_wallet_id.in_(select(Wallet.wallet_id).where(Wallet.user_id == current_user.user_id)))
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
            direction=tx.direction,
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
        destination_wallet_id=transaction_req.destination_wallet_id,
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
