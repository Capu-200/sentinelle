# Payon API Documentation

Cette documentation détaille les endpoints disponibles sur l'API Backend de Payon.

**Base URL (Vercel Prod):** `https://sentinelle-api-backend-8773685706613.europe-west1.run.app`
**Base URL (Local):** `http://127.0.0.1:8000`

---

## 1. Authentication (`/auth`)

### Register
**POST** `/auth/register`
Crée un nouvel utilisateur et un wallet par défaut (solde initial 1000€).

- **Body (JSON):**
  ```json
  {
    "full_name": "Jean Dupont",
    "email": "jean.dupont@example.com",
    "password": "secret_password"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```

### Login
**POST** `/auth/login`
Authentifie un utilisateur et retourne un token JWT.

- **Body (JSON):**
  ```json
  {
    "email": "jean.dupont@example.com",
    "password": "secret_password"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```

---

## 2. Dashboard (`/dashboard`)

### Get Dashboard Summary
**GET** `/dashboard/`
Retourne toutes les données nécessaires pour la page d'accueil (User info, Wallet, Dernières transactions, Contacts).

- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):**
  ```json
  {
    "user": {
      "display_name": "Jean",
      "email": "jean.dupont@example.com",
      "risk_level": "LOW",
      "trust_score": 100
    },
    "wallet": {
      "wallet_id": "aa11-bb22...",
      "balance": 1000.0,
      "currency": "EUR",
      "kyc_status": "VERIFIED"
    },
    "recent_transactions": [
      {
        "transaction_id": "tx-123",
        "amount": 50.0,
        "currency": "EUR",
        "transaction_type": "TRANSFER",
        "direction": "OUTGOING",
        "status": "VALIDATED",
        "recipient_name": "Alice",
        "created_at": "2024-01-28T12:00:00"
      }
    ],
    "contacts": [
      {
        "name": "Alice",
        "email": "alice@example.com",
        "is_internal": true
      }
    ]
  }
  ```

---

## 3. Transactions (`/transactions`)

### Create Transaction (Transfer)
**POST** `/transactions`
Règles :
- Vérifie le solde.
- Interroge le **ML Engine** pour détection de fraude.
- Si `VALIDATED` -> Exécute le mouvement financier (Débit/Crédit).
- Si `REJECTED` -> Bloque la transaction.

- **Headers:** `Authorization: Bearer <token>`
- **Body (JSON):**
  ```json
  {
    "amount": 100.0,
    "currency": "EUR",
    "source_wallet_id": "wallet-uuid",
    "transaction_type": "TRANSFER",
    "direction": "OUTGOING",
    "recipient_email": "alice@example.com", // Optionnel, pour résolution auto du wallet destination
    "destination_wallet_id": "dest-wallet-uuid", // Optionnel si email fourni
    "description": "Remboursement resto"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "transaction_id": "new-tx-uuid",
    "risk_score": 0.05,
    "decision": "APPROVE", // ou "BLOCK" / "REVIEW"
    "reasons": [],
    "model_version": "v2.1"
  }
  ```

### List Transactions
**GET** `/transactions`
Historique complet des transactions de l'utilisateur.

- **Query Params:**
  - `limit`: int (default 50)
  - `skip`: int (default 0)
- **Response (200 OK):** List of Transaction objects.

---

## 4. Contacts (`/contacts`)

### List Contacts
**GET** `/contacts/`
- **Response:** Liste des favoris.

### Add Contact
**POST** `/contacts/`
- **Body:** `{ "name": "Bob", "email": "bob@example.com" }` or `{ "name": "Garage", "iban": "FR76..." }`
- **Logic:** Tente de lier automatiquement à un utilisateur interne si l'email correspond.

### Delete Contact
**DELETE** `/contacts/{contact_id}`

---

## 5. System

### Health Check
**GET** `/health`
- **Response:** `{ "status": "healthy", "ml_engine": "healthy" }`
