"""
FastAPI Application - Fraud Detection Backend.
"""
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from dotenv import load_dotenv

load_dotenv()

import httpx
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, Session, select

from app.database import engine, get_db
from .auth import get_current_user, require_active_user
from .config import get_settings
from .models import AIDecision, Transaction, User, Wallet, WalletLedger, Contact
from .worker_ia import build_enriched_payload, score_with_retry
from .services.rule_engine import evaluate_transaction
from .services.transactions import save_ai_decision, apply_decision_to_transaction
from .database import SessionLocal
from .routers import auth, dashboard, contacts
from .schemas import TransactionResponseLite
from .services.statuses import map_kyc_status_to_public

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [api] %(message)s",
)
logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Payon Fraud Detection API",
    description="API backend pour la détection de fraude bancaire",
    version="1.0.0",
    lifespan=lifespan,
)

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

ML_ENGINE_HEALTH_URL = settings.ml_engine_health_url
# Configuration ML Engine
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app")  # Cloud Run URL



class TransactionCreateRequest(BaseModel):
    transaction_id: Optional[str] = None
    amount: float
    currency: str = "EUR"
    source_wallet_id: str
    destination_wallet_id: Optional[str] = None
    transaction_type: str = "TRANSFER"
    direction: str = "OUTGOING"
    country: Optional[str] = "FR"
    city: Optional[str] = None
    description: Optional[str] = None
    recipient_email: Optional[str] = None


class TransactionCreateResponse(BaseModel):
    transaction_id: str
    status: str
    message: str
    risk_score: Optional[float] = 0.0
    decision: Optional[str] = "PENDING"
    reasons: Optional[List[str]] = []
    model_version: Optional[str] = "unknown"


def process_transaction_background(transaction_id: str, payload: dict):
    """Processes the transaction asynchronously without Kafka (Cloud Run friendly)."""
    logger.info("Background processing started for tx=%s", transaction_id)
    db = SessionLocal()
    try:
        enriched = build_enriched_payload(payload)
        
        # 1. ML Scoring
        try:
            result = score_with_retry(enriched)
            ml_risk_score = float(result.get("risk_score", 0.0))
            ml_reasons = result.get("reasons", [])
            ml_decision = result.get("decision", "APPROVE")
            ml_model_version = result.get("model_version", "unknown")
        except Exception as exc:
            logger.exception("ML scoring failed for tx=%s", transaction_id)
            ml_risk_score = 0.5
            ml_reasons = [f"WORKER_ERROR: {exc}"]
            ml_decision = "REVIEW"
            ml_model_version = "fallback"

        # 2. Rule Engine
        evaluation = evaluate_transaction(
            tx_context=payload,
            ml_risk_score=ml_risk_score,
            ml_reasons=ml_reasons,
            db=db,
        )
        final_decision = evaluation.decision
        final_score = evaluation.combined_score
        all_reasons = evaluation.all_reasons
        
        decision_payload = {
            "transaction_id": transaction_id,
            "fraud_score": final_score,
            "decision": final_decision,
            "reasons": all_reasons,
            "model_version": ml_model_version,
            "features_snapshot": enriched["transaction"]["features"],
        }
        
        # 3. Apply changes
        tx = db.get(Transaction, transaction_id)
        if tx:
            save_ai_decision(db, transaction_id, decision_payload)
            apply_decision_to_transaction(db, tx, decision_payload)
            db.commit()
            logger.info("Background processing complete for tx=%s. Final decision: %s", transaction_id, final_decision)
        else:
            logger.error("Transaction %s not found in DB during background processing.", transaction_id)
    except Exception as exc:
        logger.exception("Background processing failed for tx=%s", transaction_id)
        db.rollback()
    finally:
        db.close()


class DecisionDebugResponse(BaseModel):
    transaction_id: str
    fraud_score: Optional[float]
    decision: Optional[str]
    reasons: list[str]
    model_version: Optional[str]
    created_at: datetime


class TransactionDebugResponse(BaseModel):
    transaction: dict
    decision: Optional[DecisionDebugResponse]


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Payon Fraud Detection API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    ml_engine_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(ML_ENGINE_HEALTH_URL)
            ml_engine_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        ml_engine_status = "unreachable"
    return {"status": "healthy", "ml_engine": ml_engine_status}


def _resolve_destination_wallet(db: Session, recipient_email: Optional[str]) -> Optional[str]:
    if not recipient_email:
        return None
    stmt_user = select(User).where(User.email == recipient_email.lower())
    dest_user = db.execute(stmt_user).scalars().first()
    if not dest_user:
        return None
    stmt_wallet = select(Wallet).where(Wallet.user_id == dest_user.user_id)
    dest_wallet = db.execute(stmt_wallet).scalars().first()
    return dest_wallet.wallet_id if dest_wallet else None


@app.post(
    "/transactions",
    response_model=TransactionCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_transaction(
    transaction_req: TransactionCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
):
    transaction_id = transaction_req.transaction_id or str(uuid.uuid4())
    current_time = datetime.utcnow()

    source_wallet = db.get(Wallet, transaction_req.source_wallet_id)
    if not source_wallet:
        raise HTTPException(status_code=404, detail="Wallet source introuvable")
    if source_wallet.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Wallet source non autorisé")

    destination_wallet_id = None
    if transaction_req.destination_wallet_id:
        destination_wallet = db.get(Wallet, transaction_req.destination_wallet_id)
        if not destination_wallet:
            raise HTTPException(status_code=404, detail="Wallet destination introuvable")
        destination_wallet_id = destination_wallet.wallet_id
    elif transaction_req.recipient_email:
        destination_wallet_id = _resolve_destination_wallet(db, transaction_req.recipient_email)

    new_tx = Transaction(
        transaction_id=transaction_id,
        amount=Decimal(str(transaction_req.amount)),
        currency=transaction_req.currency,
        source_wallet_id=transaction_req.source_wallet_id,
        destination_wallet_id=destination_wallet_id,
        transaction_type=transaction_req.transaction_type,
        direction=transaction_req.direction,
        country=transaction_req.country,
        city=transaction_req.city,
        description=transaction_req.description,
        initiator_user_id=current_user.user_id,
        created_at=current_time,
        kyc_status="PENDING",
    )
    db.add(new_tx)
    db.flush()

    event_payload = {
        "transaction_id": transaction_id,
        "initiator_user_id": new_tx.initiator_user_id,
        "source_wallet_id": new_tx.source_wallet_id,
        "destination_wallet_id": new_tx.destination_wallet_id,
        "amount": float(new_tx.amount),
        "currency": new_tx.currency,
        "transaction_type": new_tx.transaction_type,
        "direction": new_tx.direction,
        "country": new_tx.country,
        "city": new_tx.city,
        "description": new_tx.description,
        "created_at": current_time.isoformat() + "Z",
        "context": {
            "source_wallet": {
                "balance": float(source_wallet.balance),
                "status": source_wallet.kyc_status,
            },
            "user": {
                "status": "active" if current_user.is_active else "inactive",
                "risk_level": current_user.risk_level or "LOW",
            },
        },
    }

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("DB commit failed for tx=%s", transaction_id)
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement de la transaction. Merci de réessayer.",
        )
    db.refresh(new_tx)
    
    # Process asynchronously using FastAPI BackgroundTasks instead of Kafka
    background_tasks.add_task(process_transaction_background, transaction_id, event_payload)
    
    logger.info("Transaction %s enqueued for background processing", transaction_id)
    return TransactionCreateResponse(
        transaction_id=transaction_id,
        status=map_kyc_status_to_public(new_tx.kyc_status),
        message="Transaction envoyee pour analyse IA",
    )


@app.get("/transactions", response_model=List[TransactionResponseLite])
async def get_transactions(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    skip: int = 0,
):
    """
    Récupère l'historique des transactions de l'utilisateur connecté.
    (Initiateur OU Destinataire)
    Enrichi avec les informations de pays source et destination.
    """
    user_wallets_stmt = select(Wallet.wallet_id).where(Wallet.user_id == current_user.user_id)
    user_wallet_ids = db.execute(user_wallets_stmt).scalars().all()
    if not user_wallet_ids:
        user_wallet_ids = []

    stmt = (
        select(Transaction)
        .where(
            (Transaction.initiator_user_id == current_user.user_id)
            | (Transaction.source_wallet_id.in_(user_wallet_ids))
            | (Transaction.destination_wallet_id.in_(user_wallet_ids))
        )
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    transactions = db.execute(stmt).scalars().all()


    result = []
    for tx in transactions:
        # Déterminer la direction relative à l'utilisateur actuel
        is_incoming = tx.destination_wallet_id in user_wallet_ids and tx.source_wallet_id not in user_wallet_ids
        direction = "INCOMING" if is_incoming else tx.direction
        
        # Récupérer le pays source (initiateur)
        source_country = "FR" # Fallback par défaut si info manquante
        if tx.initiator_user_id:
            initiator_stmt = select(User).where(User.user_id == tx.initiator_user_id)
            initiator = db.execute(initiator_stmt).scalars().first()
            if initiator and initiator.country_home:
                source_country = initiator.country_home
        
        # Récupérer le pays destination (destinataire)
        destination_country = None
        recipient_email = None
        if tx.destination_wallet_id:
            # Trouver l'utilisateur propriétaire du wallet de destination
            dest_wallet_stmt = select(Wallet).where(Wallet.wallet_id == tx.destination_wallet_id)
            dest_wallet = db.execute(dest_wallet_stmt).scalars().first()
            if dest_wallet and dest_wallet.user_id:
                dest_user_stmt = select(User).where(User.user_id == dest_wallet.user_id)
                dest_user = db.execute(dest_user_stmt).scalars().first()
                if dest_user:
                    destination_country = dest_user.country_home
                    recipient_email = dest_user.email
        
        # Nom du destinataire (Logique améliorée pour éviter doublon commentaire)
        # Priorité: 1. Description (sauf si c'est un commentaire long) 2. Email 3. Inconnu
        # Si description == comment, on évite de l'utiliser comme Nom
        
        recipient_name = "Destinataire Inconnu"
        if recipient_email:
             recipient_name = recipient_email
        elif tx.description and len(tx.description) < 30: # Use description as name only if short-ish
             recipient_name = tx.description
        
        # Récupérer les raisons (fraud rules)
        reasons_list = None
        decision_stmt = select(AIDecision).where(AIDecision.transaction_id == tx.transaction_id).order_by(AIDecision.created_at.desc())
        decision = db.execute(decision_stmt).scalars().first()
        if decision and decision.reasons:
            reasons_list = [r.strip() for r in decision.reasons.split(",") if r.strip()]

        result.append(
            TransactionResponseLite(
                transaction_id=tx.transaction_id,
                amount=float(tx.amount),
                currency=tx.currency,
                transaction_type=tx.transaction_type,
                direction=direction,
                status=tx.kyc_status,
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                created_at=tx.created_at,
                source_country=source_country,
                destination_country=destination_country,
                comment=tx.description,
                reasons=reasons_list
            )
        )
    
    return result


@app.get("/debug/transactions/{transaction_id}", response_model=TransactionDebugResponse)
async def debug_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_user),
):
    transaction = db.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    decision_stmt = (
        select(AIDecision)
        .where(AIDecision.transaction_id == transaction_id)
        .order_by(AIDecision.created_at.desc())
    )
    decision = db.execute(decision_stmt).scalars().first()

    decision_payload = None
    if decision:
        reasons = decision.reasons.split(",") if decision.reasons else []
        decision_payload = DecisionDebugResponse(
            transaction_id=transaction_id,
            fraud_score=float(decision.fraud_score or 0.0),
            decision=decision.decision,
            reasons=[r.strip() for r in reasons if r.strip()],
            model_version=decision.model_version,
            created_at=decision.created_at,
        )

    transaction_payload = {
        "transaction_id": transaction.transaction_id,
        "amount": float(transaction.amount),
        "currency": transaction.currency,
        "status": transaction.kyc_status,
        "status_public": map_kyc_status_to_public(transaction.kyc_status),
        "source_wallet_id": transaction.source_wallet_id,
        "destination_wallet_id": transaction.destination_wallet_id,
        "description": transaction.description,
        "created_at": transaction.created_at,
    }

    return TransactionDebugResponse(transaction=transaction_payload, decision=decision_payload)


@app.get("/debug/ai-decisions", response_model=list[DecisionDebugResponse])
async def list_decisions(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_active_user),
):
    stmt = select(AIDecision).order_by(AIDecision.created_at.desc()).limit(limit)
    decisions = db.execute(stmt).scalars().all()
    result: list[DecisionDebugResponse] = []
    for row in decisions:
        reasons = row.reasons.split(",") if row.reasons else []
        result.append(
            DecisionDebugResponse(
                transaction_id=row.transaction_id or "",
                fraud_score=float(row.fraud_score or 0.0),
                decision=row.decision,
                reasons=[r.strip() for r in reasons if r.strip()],
                model_version=row.model_version,
                created_at=row.created_at,
            )
        )
    return result


class CommentUpdate(BaseModel):
    comment: str

@app.patch("/transactions/{transaction_id}/comment")
async def update_transaction_comment(
    transaction_id: str,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour le commentaire d'une transaction.
    Accessible uniquement par l'initiateur ou le bénéficiaire (si wallet interne).
    """
    # 1. Récupérer la transaction
    tx = db.get(Transaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    
    # 2. Vérifier l'autorisation (Ownership)
    stmt = select(Wallet.wallet_id).where(Wallet.user_id == current_user.user_id)
    user_wallet_ids = db.execute(stmt).scalars().all()

    is_initiator = tx.initiator_user_id == current_user.user_id
    is_source_owner = tx.source_wallet_id in (user_wallet_ids or [])
    is_dest_owner = tx.destination_wallet_id in (user_wallet_ids or [])
    
    if not (is_initiator or is_source_owner or is_dest_owner):
        raise HTTPException(status_code=403, detail="Non autorisé à modifier cette transaction")

    # 3. Validation (Longueur)
    if len(comment_data.comment) > 500:
        raise HTTPException(status_code=400, detail="Commentaire trop long (max 500 caractères)")

    # 4. Mise à jour
    tx.description = comment_data.comment
    db.add(tx)
    db.commit()
    
    return {"status": "success", "message": "Commentaire mis à jour"}
