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
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError, text
from sqlmodel import SQLModel, Session, select

from app.database import engine, get_db
from .auth import get_current_user, require_active_user
from .config import get_settings
from .kafka_producer import publish_transaction_request
from .models import AIDecision, Transaction, User, Wallet, WalletLedger, Contact
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
        publish_transaction_request(event_payload)
    except RuntimeError:
        logger.exception("Kafka publish failed for tx=%s", transaction_id)
        db.rollback()
        raise HTTPException(status_code=503, detail="Kafka indisponible")

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("DB commit failed after Kafka publish for tx=%s", transaction_id)
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'enregistrement de la transaction. Merci de réessayer.",
        )
    db.refresh(new_tx)
    logger.info("Transaction %s enqueued for scoring", transaction_id)
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
    """Return the current user's transactions enriched with direction highlights."""
    wallet_ids_stmt = select(Wallet.wallet_id).where(Wallet.user_id == current_user.user_id)
    user_wallet_ids = db.execute(wallet_ids_stmt).scalars().all()

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

    results: List[TransactionResponseLite] = []
    for tx in transactions:
        is_incoming = tx.destination_wallet_id in user_wallet_ids and (
            not tx.source_wallet_id or tx.source_wallet_id not in user_wallet_ids
        )
        direction = "INCOMING" if is_incoming else tx.direction

        source_country = None
        if tx.initiator_user_id:
            initiator = db.get(User, tx.initiator_user_id)
            if initiator:
                source_country = initiator.country_home

        destination_country = None
        recipient_email = None
        if tx.destination_wallet_id:
            dest_wallet = db.get(Wallet, tx.destination_wallet_id)
            if dest_wallet and dest_wallet.user_id:
                dest_user = db.get(User, dest_wallet.user_id)
                if dest_user:
                    destination_country = dest_user.country_home
                    recipient_email = dest_user.email

        recipient_name = tx.description or recipient_email or "Destinataire Inconnu"

        results.append(
            TransactionResponseLite(
                transaction_id=tx.transaction_id,
                amount=float(tx.amount),
                currency=tx.currency,
                transaction_type=tx.transaction_type,
                direction=direction,
                status=map_kyc_status_to_public(tx.kyc_status),
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                created_at=tx.created_at,
                source_country=source_country,
                destination_country=destination_country,
                comment=tx.description,
            )
        )

    return results


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
