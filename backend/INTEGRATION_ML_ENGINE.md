# 🔗 Intégration ML Engine dans le Backend

## ✅ Ce qui a été fait

### 1. Route POST `/transactions`
- ✅ Reçoit une transaction
- ✅ Enrichit avec features historiques (version simplifiée pour l'instant)
- ✅ Appelle le ML Engine (Cloud Run)
- ✅ Sauvegarde dans `ai_decisions`
- ✅ Retourne le résultat

### 2. Fonctions ajoutées
- ✅ `enrich_transaction_with_historical_features()` : Enrichit la transaction
- ✅ `call_ml_engine()` : Appelle le ML Engine via HTTP
- ✅ `save_ai_decision()` : Sauvegarde dans la DB

### 3. Dépendances
- ✅ `httpx` ajouté à `requirements.txt`
- ✅ `pydantic` ajouté (déjà utilisé par FastAPI)

---

## 🔧 Configuration

### Variable d'environnement

```bash
# URL du ML Engine (Cloud Run)
export ML_ENGINE_URL="https://sentinelle-ml-engine-xxx.run.app"
```

Ou dans le fichier `.env` :
```
ML_ENGINE_URL=https://sentinelle-ml-engine-xxx.run.app
```

---

## 📋 Workflow

```
1. Client → POST /transactions
   ↓
2. Backend enrichit la transaction
   - Features historiques (à compléter avec vraies requêtes SQL)
   - Features transactionnelles
   ↓
3. Backend appelle ML Engine
   - POST https://ml-engine.run.app/score
   - Body: {transaction: enriched, context: {...}}
   ↓
4. ML Engine retourne
   - {risk_score, decision, reasons, model_version}
   ↓
5. Backend sauvegarde dans ai_decisions
   ↓
6. Backend retourne la réponse au client
```

---

## 🚧 À compléter

### 1. Features historiques réelles

Actuellement, `enrich_transaction_with_historical_features()` retourne des valeurs par défaut. Il faut ajouter les vraies requêtes SQL :

```python
# Exemple pour avg_amount_30d
result = db.execute(text("""
    SELECT AVG(amount) as avg_amount_30d
    FROM transactions
    WHERE source_wallet_id = :wallet_id
      AND created_at >= :created_at - INTERVAL '30 days'
      AND created_at < :created_at
"""), {
    "wallet_id": source_wallet_id,
    "created_at": created_at
})
avg_amount_30d = result.scalar() or None
```

### 2. Context enrichi

Récupérer les vraies données depuis la DB :
- `source_wallet.balance` depuis `wallets`
- `user.risk_level` depuis `users`
- `destination_wallet.status` depuis `wallets`
- etc.

### 3. Gestion d'erreurs

- Retry logic pour l'appel ML Engine
- Fallback si ML Engine indisponible
- Validation des données

---

## 🧪 Test

### 1. Démarrer le Backend localement

```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Tester la route

```bash
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_001",
    "destination_wallet_id": "wallet_002",
    "transaction_type": "TRANSFER",
    "direction": "outgoing"
  }'
```

### 3. Vérifier la santé

```bash
curl http://localhost:8000/health
```

---

## 📝 Notes

- L'enrichissement est simplifié pour l'instant
- Les vraies requêtes SQL doivent être ajoutées
- Le ML Engine doit être déployé et accessible
- La variable `ML_ENGINE_URL` doit être configurée

---

**Prochaine étape** : Compléter les requêtes SQL pour les features historiques réelles.

