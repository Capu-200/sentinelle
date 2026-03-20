# 🔧 Guide Backend - Implémentation des Nouvelles Fonctionnalités

## 📌 Vue d'ensemble

Ce guide détaille les modifications backend nécessaires pour supporter l'enrichissement des virements.

---

## 1️⃣ Modification du Modèle Transaction

### Base de données (SQL)

```sql
-- Ajout des colonnes à la table transactions
ALTER TABLE transactions
ADD COLUMN source_country VARCHAR(2),           -- Code ISO pays source (ex: "FR")
ADD COLUMN destination_country VARCHAR(2),      -- Code ISO pays destination (ex: "ES")
ADD COLUMN comment TEXT,                        -- Commentaire utilisateur
ADD COLUMN recipient_iban VARCHAR(34);          -- IBAN du destinataire (optionnel)

-- Index pour optimiser les recherches par corridor
CREATE INDEX idx_transactions_corridor 
ON transactions(source_country, destination_country);

-- Index pour les recherches dans les commentaires
CREATE INDEX idx_transactions_comment 
ON transactions USING gin(to_tsvector('french', comment));
```

### Modèle Python (Pydantic/SQLAlchemy)

```python
from sqlalchemy import Column, String, Text
from pydantic import BaseModel, Field
from typing import Optional

# SQLAlchemy Model
class Transaction(Base):
    __tablename__ = "transactions"
    
    # ... colonnes existantes ...
    
    source_country = Column(String(2), nullable=True)
    destination_country = Column(String(2), nullable=True)
    comment = Column(Text, nullable=True)
    recipient_iban = Column(String(34), nullable=True)

# Pydantic Schema (Request)
class TransactionCreate(BaseModel):
    amount: float
    currency: str = "PYC"
    source_wallet_id: str
    recipient_email: str
    comment: Optional[str] = Field(None, max_length=500)
    country: str = "FR"
    # ... autres champs ...

# Pydantic Schema (Response)
class TransactionResponse(BaseModel):
    transaction_id: str
    amount: float
    status: str
    source_country: Optional[str] = None
    destination_country: Optional[str] = None
    comment: Optional[str] = None
    recipient_iban: Optional[str] = None
    # ... autres champs ...
```

---

## 2️⃣ Endpoint POST /transactions (Modification)

### Avant
```python
@router.post("/transactions")
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    # Création de la transaction
    new_transaction = Transaction(
        amount=transaction.amount,
        currency=transaction.currency,
        # ...
    )
    db.add(new_transaction)
    db.commit()
    return new_transaction
```

### Après
```python
@router.post("/transactions")
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    # Déterminer le pays de destination (depuis IBAN ou email)
    destination_country = await get_recipient_country(
        transaction.recipient_email,
        transaction.recipient_iban
    )
    
    # Création de la transaction ENRICHIE
    new_transaction = Transaction(
        amount=transaction.amount,
        currency=transaction.currency,
        source_country=transaction.country,           # ← NOUVEAU
        destination_country=destination_country,      # ← NOUVEAU
        comment=transaction.comment,                  # ← NOUVEAU
        recipient_iban=transaction.recipient_iban,    # ← NOUVEAU
        # ... autres champs ...
    )
    
    db.add(new_transaction)
    db.commit()
    
    # Envoyer à Kafka pour analyse ML (si nécessaire)
    await send_to_kafka(new_transaction)
    
    return new_transaction
```

### Helper Function
```python
async def get_recipient_country(email: str, iban: Optional[str] = None) -> Optional[str]:
    """
    Détermine le pays du destinataire depuis l'IBAN ou le profil utilisateur
    """
    if iban:
        # Les 2 premiers caractères d'un IBAN = code pays
        return iban[:2].upper()
    
    # Sinon, chercher dans la base de données
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user.country
    
    return None
```

---

## 3️⃣ Nouveau Endpoint PATCH /transactions/{id}/comment

### Implémentation

```python
from pydantic import BaseModel, Field, validator

class CommentUpdate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=500)
    
    @validator('comment')
    def validate_comment(cls, v):
        if not v or not v.strip():
            raise ValueError("Le commentaire ne peut pas être vide")
        return v.strip()

@router.patch("/transactions/{transaction_id}/comment")
async def update_transaction_comment(
    transaction_id: str,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour le commentaire d'une transaction.
    ⚠️ NE DÉCLENCHE PAS l'analyse ML - simple mise à jour de métadonnées.
    """
    
    # Vérifier que la transaction existe
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")
    
    # Vérifier que l'utilisateur est propriétaire de la transaction
    if transaction.initiator_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    # Mise à jour du commentaire (PAS D'ANALYSE ML)
    transaction.comment = comment_data.comment
    transaction.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(transaction)
    
    return {
        "transaction_id": transaction.transaction_id,
        "comment": transaction.comment,
        "updated_at": transaction.updated_at
    }
```

### Sécurité

```python
# Rate limiting pour éviter les abus
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.patch("/transactions/{transaction_id}/comment")
@limiter.limit("10/minute")  # Max 10 modifications par minute
async def update_transaction_comment(...):
    # ... code ...
```

---

## 4️⃣ Endpoint GET /transactions (Modification)

### Avant
```python
@router.get("/transactions")
async def get_transactions(
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transactions = db.query(Transaction).filter(
        Transaction.initiator_user_id == current_user.user_id
    ).limit(limit).all()
    
    return transactions
```

### Après
```python
@router.get("/transactions")
async def get_transactions(
    limit: int = 100,
    corridor: Optional[str] = None,  # ← NOUVEAU: Filtrer par corridor (ex: "FR-ES")
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(
        Transaction.initiator_user_id == current_user.user_id
    )
    
    # Filtrage par corridor (optionnel)
    if corridor:
        source, dest = corridor.split("-")
        query = query.filter(
            Transaction.source_country == source,
            Transaction.destination_country == dest
        )
    
    transactions = query.limit(limit).all()
    
    # Enrichir la réponse avec les informations pays
    return [
        {
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "status": t.status,
            "source_country": t.source_country,           # ← NOUVEAU
            "destination_country": t.destination_country, # ← NOUVEAU
            "comment": t.comment,                         # ← NOUVEAU
            "recipient_iban": t.recipient_iban,           # ← NOUVEAU
            # ... autres champs ...
        }
        for t in transactions
    ]
```

---

## 5️⃣ Tests

### Test Unitaire (pytest)

```python
import pytest
from fastapi.testclient import TestClient

def test_create_transaction_with_comment(client: TestClient, auth_headers):
    """Test création de transaction avec commentaire"""
    response = client.post(
        "/transactions",
        json={
            "amount": 50,
            "currency": "PYC",
            "source_wallet_id": "wallet_123",
            "recipient_email": "test@example.com",
            "comment": "Remboursement dîner",  # ← NOUVEAU
            "country": "FR"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["comment"] == "Remboursement dîner"
    assert data["source_country"] == "FR"

def test_update_comment(client: TestClient, auth_headers):
    """Test mise à jour du commentaire"""
    # Créer une transaction
    create_response = client.post("/transactions", json={...})
    transaction_id = create_response.json()["transaction_id"]
    
    # Mettre à jour le commentaire
    update_response = client.patch(
        f"/transactions/{transaction_id}/comment",
        json={"comment": "Nouveau commentaire"},
        headers=auth_headers
    )
    
    assert update_response.status_code == 200
    assert update_response.json()["comment"] == "Nouveau commentaire"

def test_update_comment_validation(client: TestClient, auth_headers):
    """Test validation du commentaire"""
    response = client.patch(
        "/transactions/tx_123/comment",
        json={"comment": ""},  # Commentaire vide
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error
```

---

## 6️⃣ Migration de Données

### Script de Migration

```python
"""
Migration: Enrichir les transactions existantes
"""

from sqlalchemy.orm import Session
from models import Transaction, User

def migrate_existing_transactions(db: Session):
    """
    Ajoute les informations de pays aux transactions existantes
    """
    transactions = db.query(Transaction).filter(
        Transaction.source_country.is_(None)
    ).all()
    
    for transaction in transactions:
        # Déterminer le pays source depuis le wallet
        source_wallet = db.query(Wallet).filter(
            Wallet.wallet_id == transaction.source_wallet_id
        ).first()
        
        if source_wallet:
            user = db.query(User).filter(
                User.user_id == source_wallet.user_id
            ).first()
            transaction.source_country = user.country if user else "FR"
        
        # Déterminer le pays destination
        if transaction.recipient_iban:
            transaction.destination_country = transaction.recipient_iban[:2]
        else:
            recipient = db.query(User).filter(
                User.email == transaction.recipient_email
            ).first()
            transaction.destination_country = recipient.country if recipient else None
    
    db.commit()
    print(f"✅ {len(transactions)} transactions migrées")

if __name__ == "__main__":
    from database import SessionLocal
    db = SessionLocal()
    migrate_existing_transactions(db)
    db.close()
```

---

## 7️⃣ Checklist d'Implémentation

### Base de données
- [ ] Ajouter les colonnes `source_country`, `destination_country`, `comment`, `recipient_iban`
- [ ] Créer les index pour optimiser les requêtes
- [ ] Migrer les données existantes

### API
- [ ] Modifier `POST /transactions` pour accepter `comment`
- [ ] Implémenter `PATCH /transactions/{id}/comment`
- [ ] Enrichir `GET /transactions` avec les nouveaux champs
- [ ] Ajouter le filtrage par corridor (optionnel)

### Sécurité
- [ ] Vérifier l'ownership des transactions avant modification
- [ ] Ajouter rate limiting sur l'endpoint PATCH
- [ ] Valider la longueur du commentaire (max 500 chars)

### Tests
- [ ] Tests unitaires pour création avec commentaire
- [ ] Tests unitaires pour mise à jour de commentaire
- [ ] Tests de validation (commentaire vide, trop long)
- [ ] Tests d'autorisation (modification par non-propriétaire)

### Documentation
- [ ] Mettre à jour la documentation OpenAPI/Swagger
- [ ] Documenter les nouveaux champs dans le README
- [ ] Ajouter des exemples de requêtes

---

## 📊 Exemple de Réponse API Finale

```json
{
    "transaction_id": "tx_abc123",
    "amount": 150.00,
    "currency": "PYC",
    "status": "VALIDATED",
    "direction": "OUTGOING",
    "source_wallet_id": "wallet_456",
    "recipient_email": "marie@example.com",
    "recipient_name": "Marie Dubois",
    "source_country": "FR",
    "destination_country": "ES",
    "comment": "Remboursement restaurant Madrid",
    "recipient_iban": "ES9121000418450200051332",
    "created_at": "2026-01-28T14:30:00Z",
    "updated_at": "2026-01-28T14:30:00Z"
}
```

---

**Date** : 29 janvier 2026  
**Version** : 1.0.0
