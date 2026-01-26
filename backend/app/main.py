"""
FastAPI Application - Fraud Detection Backend
"""
import os
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from contextlib import asynccontextmanager
from sqlmodel import SQLModel

from app.database import get_db, engine
from .routers import auth
from .models import User

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
        raise HTTPException(
            status_code=503,
            detail=f"ML Engine unavailable: {str(e)}"
        )


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
    db_session.commit()


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


@app.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionRequest,
    db = Depends(get_db)
):
    """
    Crée une transaction et la score via le ML Engine.
    
    Workflow:
    1. Enrichit la transaction avec features historiques (DB)
    2. Appelle le ML Engine (Cloud Run)
    3. Sauvegarde la décision dans ai_decisions
    4. Retourne le résultat
    """
    # Générer transaction_id si non fourni
    transaction_id = transaction.transaction_id or str(uuid.uuid4())
    
    # Convertir en dict
    transaction_dict = transaction.dict()
    transaction_dict["transaction_id"] = transaction_id
    transaction_dict["created_at"] = transaction_dict.get("created_at") or datetime.utcnow().isoformat()
    
    # 1. Enrichir la transaction (features historiques depuis DB)
    enriched_transaction = await enrich_transaction_with_historical_features(
        transaction_dict,
        db
    )
    
    # 2. Appeler le ML Engine
    scoring_result = await call_ml_engine(enriched_transaction)
    
    # 3. Sauvegarder dans DB
    try:
        await save_ai_decision(transaction_id, scoring_result, db)
    except Exception as e:
        # Log l'erreur mais ne bloque pas la réponse
        print(f"Erreur lors de la sauvegarde: {e}")
    
    # 4. Retourner la réponse
    return TransactionResponse(
        transaction_id=transaction_id,
        risk_score=scoring_result.get("risk_score", 0.0),
        decision=scoring_result.get("decision", "APPROVE"),
        reasons=scoring_result.get("reasons", []),
        model_version=scoring_result.get("model_version", "unknown"),
    )

