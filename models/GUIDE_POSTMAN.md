# 🧪 Guide Postman : Tester le ML Engine

Guide complet pour tester le ML Engine avec Postman.

---

## 🔗 URL du Service

```
https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app
```

---

## 📋 Configuration Postman

### 1. Créer une Nouvelle Requête

- **Method** : `POST`
- **URL** : `https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score`
- **Headers** :
  - `Content-Type: application/json`

### 2. Body (JSON)

Sélectionnez **"Body"** → **"raw"** → **"JSON"**

---

## 🎯 Exemple 1 : Transaction Normale

### Requête

**URL** : `POST https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score`

**Body** :
```json
{
  "transaction": {
    "transaction_id": "test_normal_001",
    "amount": 50.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_normal_001",
    "destination_wallet_id": "wallet_dest_001",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris",
    "description": "Paiement normal"
  },
  "context": {
    "source_wallet": {
      "balance": 1000.0,
      "status": "active"
    },
    "user": {
      "status": "active",
      "risk_level": "low"
    }
  }
}
```

### Réponse Attendue

```json
{
  "risk_score": 0.2345,
  "decision": "APPROVE",
  "reasons": [],
  "model_version": "1.0.0-test"
}
```

**Interprétation** :
- ✅ `decision: "APPROVE"` → Transaction normale, approuvée
- ✅ `risk_score: 0.2345` → Score faible (< 0.6461)
- ✅ `reasons: []` → Aucune règle déclenchée

---

## ⚠️ Exemple 2 : Transaction Suspecte (REVIEW)

### Requête

**URL** : `POST https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score`

**Body** :
```json
{
  "transaction": {
    "transaction_id": "test_suspect_001",
    "amount": 250.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_suspect_001",
    "destination_wallet_id": "wallet_new_001",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris",
    "description": "Transaction suspecte"
  },
  "context": {
    "source_wallet": {
      "balance": 500.0,
      "status": "active"
    },
    "user": {
      "status": "active",
      "risk_level": "medium"
    }
  }
}
```

### Réponse Attendue

```json
{
  "risk_score": 0.6823,
  "decision": "REVIEW",
  "reasons": ["RULE_AMOUNT_ANOMALY"],
  "model_version": "1.0.0-test"
}
```

**Interprétation** :
- ⚠️ `decision: "REVIEW"` → Transaction suspecte, nécessite revue humaine
- ⚠️ `risk_score: 0.6823` → Score entre 0.6461 et 0.7410
- ⚠️ `reasons: ["RULE_AMOUNT_ANOMALY"]` → Règle déclenchée

---

## 🚫 Exemple 3 : Transaction Bloquée (BLOCK)

### Requête

**URL** : `POST https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score`

**Body** :
```json
{
  "transaction": {
    "transaction_id": "test_blocked_001",
    "amount": 350.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_blocked_001",
    "destination_wallet_id": "wallet_dest_001",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris",
    "description": "Transaction bloquée"
  },
  "context": {
    "source_wallet": {
      "balance": 100.0,
      "status": "active"
    },
    "user": {
      "status": "active",
      "risk_level": "low"
    }
  }
}
```

### Réponse Attendue

```json
{
  "risk_score": 1.0,
  "decision": "BLOCK",
  "reasons": ["RULE_MAX_AMOUNT"],
  "model_version": "1.0.0-test"
}
```

**Interprétation** :
- 🚫 `decision: "BLOCK"` → Transaction bloquée automatiquement
- 🚫 `risk_score: 1.0` → Score maximum (règle hard block)
- 🚫 `reasons: ["RULE_MAX_AMOUNT"]` → Montant > 300 (règle R1)

---

## 🔍 Exemple 4 : Health Check

### Requête

**URL** : `GET https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/health`

**Method** : `GET` (pas de body nécessaire)

### Réponse Attendue

```json
{
  "status": "healthy",
  "model_version": "1.0.0-test",
  "supervised_loaded": true,
  "unsupervised_loaded": true
}
```

**Interprétation** :
- ✅ Service opérationnel
- ✅ Modèles chargés correctement

---

## 📝 Structure Complète de la Transaction

### Champs Requis

```json
{
  "transaction": {
    "transaction_id": "string",      // Requis
    "amount": 0.0,                    // Requis (float)
    "currency": "string",             // Requis (ex: "PYC")
    "source_wallet_id": "string",     // Requis
    "destination_wallet_id": "string", // Optionnel
    "transaction_type": "string",      // Requis (ex: "TRANSFER")
    "direction": "string",            // Requis ("outgoing" ou "incoming")
    "created_at": "string",           // Optionnel (ISO format)
    "country": "string",              // Optionnel (ex: "FR")
    "city": "string",                 // Optionnel
    "description": "string"           // Optionnel
  },
  "context": {                        // Optionnel
    "source_wallet": {
      "balance": 0.0,
      "status": "string"
    },
    "user": {
      "status": "string",
      "risk_level": "string"
    }
  }
}
```

---

## 🎯 Exemple Complet (Copier-Coller)

### Transaction Normale (APPROVE)

```json
{
  "transaction": {
    "transaction_id": "postman_test_001",
    "amount": 75.50,
    "currency": "PYC",
    "source_wallet_id": "wallet_user_123",
    "destination_wallet_id": "wallet_merchant_456",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris",
    "description": "Achat en ligne"
  },
  "context": {
    "source_wallet": {
      "balance": 500.0,
      "status": "active"
    },
    "user": {
      "status": "active",
      "risk_level": "low"
    }
  }
}
```

**Copiez-collez ce JSON dans Postman pour tester !**

---

## ✅ Checklist Postman

Avant d'envoyer la requête :

- [ ] ✅ Method : `POST`
- [ ] ✅ URL : `https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score`
- [ ] ✅ Headers : `Content-Type: application/json`
- [ ] ✅ Body : `raw` → `JSON`
- [ ] ✅ JSON valide (vérifiez avec un validateur JSON)

---

## 🐛 Dépannage

### Erreur 404 Not Found

**Cause** : URL incorrecte ou endpoint inexistant

**Solution** :
- Vérifiez l'URL : `/score` (pas `/api/score`)
- Vérifiez que le service est déployé :
  ```bash
  curl https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/health
  ```

---

### Erreur 422 Unprocessable Entity

**Cause** : Format JSON invalide ou champs manquants

**Solution** :
- Vérifiez que le JSON est valide
- Vérifiez que tous les champs requis sont présents :
  - `transaction_id`
  - `amount`
  - `currency`
  - `source_wallet_id`
  - `transaction_type`
  - `direction`

---

### Erreur 500 Internal Server Error

**Cause** : Erreur côté serveur (modèles non chargés, etc.)

**Solution** :
1. Vérifiez les logs du service :
   ```bash
   gcloud run services logs read sentinelle-ml-engine \
     --region=europe-west1 \
     --project=sentinelle-485209 \
     --limit=50
   ```
2. Vérifiez le health check :
   ```bash
   curl https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/health
   ```

---

### Timeout

**Cause** : Le service prend trop de temps à répondre

**Solution** :
- Augmentez le timeout dans Postman (Settings → General → Request timeout)
- Vérifiez que le service a assez de ressources (CPU/RAM)

---

## 📊 Interprétation des Réponses

### Décisions Possibles

| Decision | Signification | Action |
|----------|---------------|--------|
| `APPROVE` | Transaction normale | ✅ Approuver automatiquement |
| `REVIEW` | Transaction suspecte | ⚠️ Envoyer en revue humaine |
| `BLOCK` | Transaction très suspecte | 🚫 Bloquer automatiquement |

### Seuils (Version 1.0.0-test)

- **BLOCK** : `risk_score ≥ 0.7410`
- **REVIEW** : `0.6461 ≤ risk_score < 0.7410`
- **APPROVE** : `risk_score < 0.6461`

---

## 🎉 C'est Prêt !

Copiez l'exemple ci-dessus dans Postman et testez ! 🚀

