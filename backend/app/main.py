"""
FastAPI Application - Fraud Detection Backend
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.kafka_producer import publish_transaction_request
from pydantic import BaseModel
from datetime import datetime
import uuid

app = FastAPI(
    title="Sentinelle Fraud Detection API",
    description="API backend pour la détection de fraude bancaire",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Sentinelle Fraud Detection API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

class TransactionCreate(BaseModel):
    source_wallet_id: str
    destination_wallet_id: str
    amount: float
    currency: str = "PAY"
    description: str | None = None


@app.post("/transactions")
async def create_transaction(tx: TransactionCreate):
    tx_id = str(uuid.uuid4())

    payload = {
        "transaction_id": tx_id,
        "source_wallet_id": tx.source_wallet_id,
        "destination_wallet_id": tx.destination_wallet_id,
        "amount": tx.amount,
        "currency": tx.currency,
        "description": tx.description,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    # ✅ Envoi dans Kafka (topic: transaction.requests)
    publish_transaction_request(payload)

    return {
        "transaction_id": tx_id,
        "status": "PENDING",
        "message": "Transaction envoyée pour analyse IA",
    }# TODO: Ajouter les routes pour users, accounts, transactions, predictions, etc.

