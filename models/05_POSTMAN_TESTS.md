# 🧪 Cas de test Postman – ML Engine

Documentation complète des cas de test pour valider le ML Engine avec Postman.

---

## ⚠️ Format obligatoire : transaction enrichie uniquement

**Toute requête POST /score doit envoyer une transaction au format enrichi.**

- `transaction` doit contenir **`features.transactional`** et **`features.historical`**.
- Pour un **nouveau compte** (sans historique), envoyez quand même `transactional` et `historical` avec des valeurs à 0 / -1.0 / 1.
- Une requête sans `features` ou sans `transactional`/`historical` renvoie **400 Bad Request** (`TRANSACTION_FORMAT_REQUIRED`).

Références : **EXEMPLES_JSON_HISTORIQUE.md**, **JSON_COMPLET_50_FEATURES.md**.

---

## 🔗 URL du service

Remplacer par l’URL réelle de ton déploiement Cloud Run si besoin.

```
https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app
```

---

## 📋 Configuration Postman commune

- **Headers** : `Content-Type: application/json`
- **Body** : onglet **Body** → **raw** → **JSON**

---

# Cas de test

---

## Cas 1 : Health check (GET /health)

Vérifier que le service et les modèles sont disponibles.

| Champ   | Valeur |
|---------|--------|
| **Method** | `GET` |
| **URL**    | `https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/health` |
| **Body**   | Aucun |

### Réponse attendue (200)

```json
{
  "status": "healthy",
  "model_version": "1.0.0-test",
  "supervised_loaded": true,
  "unsupervised_loaded": true
}
```

**Interprétation** : service opérationnel, modèles chargés.

---

## Cas 2 : Transaction normale → APPROVE

Transaction avec historique cohérent, bénéficiaire connu. Décision attendue : **APPROVE**.

| Champ   | Valeur |
|---------|--------|
| **Method** | `POST` |
| **URL**    | `https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score` |
| **Body**   | Voir ci‑dessous |

### Body (JSON)

```json
{
  "transaction": {
    "transaction_id": "test_normal_hist_001",
    "amount": 75.50,
    "currency": "PYC",
    "source_wallet_id": "wallet_user_123",
    "destination_wallet_id": "wallet_merchant_456",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "features": {
      "transactional": {
        "amount": 75.50,
        "log_amount": 4.32,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1,
        "transaction_type_TRANSFER": 1
      },
      "historical": {
        "src_tx_count_out_5m": 0,
        "src_tx_count_out_1h": 2,
        "src_tx_count_out_24h": 8,
        "src_tx_count_out_7d": 45,
        "src_tx_amount_sum_out_1h": 150.0,
        "src_tx_amount_mean_out_7d": 65.0,
        "src_tx_amount_max_out_7d": 120.0,
        "src_unique_destinations_24h": 3,
        "is_new_destination_30d": 0,
        "src_to_dst_tx_count_30d": 5,
        "days_since_last_src_to_dst": 2.5,
        "src_destination_concentration_7d": 0.15,
        "src_destination_entropy_7d": 2.8,
        "is_new_country_30d": 0,
        "country_mismatch": 0,
        "src_failed_count_24h": 0,
        "src_failed_ratio_7d": 0.0
      }
    }
  },
  "context": {
    "source_wallet": { "balance": 500.0, "status": "active" },
    "user": { "status": "active", "risk_level": "low" }
  }
}
```

### Réponse attendue (200)

```json
{
  "risk_score": 0.15,
  "decision": "APPROVE",
  "reasons": [],
  "model_version": "1.0.0-test"
}
```

**Interprétation** : historique normal, bénéficiaire connu → score faible → APPROVE.

---

## Cas 3 : Transaction suspecte → REVIEW

Vélocité élevée, nouveau bénéficiaire. Décision attendue : **REVIEW**.

| Champ   | Valeur |
|---------|--------|
| **Method** | `POST` |
| **URL**    | `https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score` |
| **Body**   | Voir ci‑dessous |

### Body (JSON)

```json
{
  "transaction": {
    "transaction_id": "test_suspect_hist_001",
    "amount": 250.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_suspect_001",
    "destination_wallet_id": "wallet_new_999",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "features": {
      "transactional": {
        "amount": 250.0,
        "log_amount": 5.52,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1,
        "transaction_type_TRANSFER": 1
      },
      "historical": {
        "src_tx_count_out_5m": 5,
        "src_tx_count_out_1h": 25,
        "src_tx_count_out_24h": 120,
        "src_tx_count_out_7d": 350,
        "src_tx_amount_sum_out_1h": 5000.0,
        "src_tx_amount_mean_out_7d": 50.0,
        "src_tx_amount_max_out_7d": 100.0,
        "src_unique_destinations_24h": 50,
        "is_new_destination_30d": 1,
        "src_to_dst_tx_count_30d": 0,
        "days_since_last_src_to_dst": -1.0,
        "src_destination_concentration_7d": 0.02,
        "src_destination_entropy_7d": 5.2,
        "is_new_country_30d": 0,
        "country_mismatch": 0,
        "src_failed_count_24h": 5,
        "src_failed_ratio_7d": 0.15
      }
    }
  },
  "context": {
    "source_wallet": { "balance": 500.0, "status": "active" },
    "user": { "status": "active", "risk_level": "medium" }
  }
}
```

### Réponse attendue (200)

```json
{
  "risk_score": 0.72,
  "decision": "REVIEW",
  "reasons": ["RULE_HIGH_VELOCITY"],
  "model_version": "1.0.0-test"
}
```

**Interprétation** : vélocité élevée, nouveau bénéficiaire → REVIEW.

---

## Cas 4 : Transaction bloquée par règle → BLOCK

Montant > 300 → règle R1 (MAX_AMOUNT). Décision attendue : **BLOCK** sans passage ML.

| Champ   | Valeur |
|---------|--------|
| **Method** | `POST` |
| **URL**    | `https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score` |
| **Body**   | Voir ci‑dessous |

### Body (JSON)

```json
{
  "transaction": {
    "transaction_id": "test_blocked_hist_001",
    "amount": 350.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_blocked_001",
    "destination_wallet_id": "wallet_dest_001",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "features": {
      "transactional": {
        "amount": 350.0,
        "log_amount": 5.86,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1,
        "transaction_type_TRANSFER": 1
      },
      "historical": {
        "src_tx_count_out_5m": 10,
        "src_tx_count_out_1h": 50,
        "src_tx_count_out_24h": 200,
        "src_tx_count_out_7d": 800,
        "src_tx_amount_sum_out_1h": 15000.0,
        "src_tx_amount_mean_out_7d": 30.0,
        "src_tx_amount_max_out_7d": 80.0,
        "src_unique_destinations_24h": 100,
        "is_new_destination_30d": 1,
        "src_to_dst_tx_count_30d": 0,
        "days_since_last_src_to_dst": -1.0,
        "src_destination_concentration_7d": 0.01,
        "src_destination_entropy_7d": 6.5,
        "is_new_country_30d": 1,
        "country_mismatch": 1,
        "src_failed_count_24h": 20,
        "src_failed_ratio_7d": 0.25
      }
    }
  },
  "context": {
    "source_wallet": { "balance": 100.0, "status": "active" },
    "user": { "status": "active", "risk_level": "high" }
  }
}
```

### Réponse attendue (200)

```json
{
  "risk_score": 1.0,
  "decision": "BLOCK",
  "reasons": ["RULE_MAX_AMOUNT"],
  "model_version": "1.0.0-test"
}
```

**Interprétation** : montant > 300 → BLOCK immédiat, score = 1.0.

---

## Cas 5 : Nouveau compte (new user) → APPROVE ou REVIEW

Historique vide, valeurs “nouveau compte”. Décision attendue : **APPROVE** (ou REVIEW selon le modèle).

| Champ   | Valeur |
|---------|--------|
| **Method** | `POST` |
| **URL**    | `https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score` |
| **Body**   | Voir ci‑dessous |

### Body (JSON)

```json
{
  "transaction": {
    "transaction_id": "test_new_account_001",
    "amount": 100.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_new_001",
    "destination_wallet_id": "wallet_dest_001",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "features": {
      "transactional": {
        "amount": 100.0,
        "log_amount": 4.61,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1
      },
      "historical": {
        "src_tx_count_out_5m": 0,
        "src_tx_count_out_1h": 0,
        "src_tx_count_out_24h": 0,
        "src_tx_count_out_7d": 0,
        "src_tx_amount_sum_out_1h": 0.0,
        "src_tx_amount_mean_out_7d": 0.0,
        "src_tx_amount_max_out_7d": 0.0,
        "src_unique_destinations_24h": 0,
        "is_new_destination_30d": 1,
        "src_to_dst_tx_count_30d": 0,
        "days_since_last_src_to_dst": -1.0,
        "src_destination_concentration_7d": 0.0,
        "src_destination_entropy_7d": 0.0,
        "is_new_country_30d": 1,
        "country_mismatch": 0,
        "src_failed_count_24h": 0,
        "src_failed_ratio_7d": 0.0
      }
    }
  }
}
```

### Réponse attendue (200)

```json
{
  "risk_score": 0.35,
  "decision": "APPROVE",
  "reasons": [],
  "model_version": "1.0.0-test"
}
```

**Interprétation** : nouveau compte, score modéré → en général APPROVE.

---

## Cas 6 : Format manquant → 400 Bad Request

Transaction sans `features.transactional` / `features.historical`. Réponse attendue : **400** avec `TRANSACTION_FORMAT_REQUIRED`.

| Champ   | Valeur |
|---------|--------|
| **Method** | `POST` |
| **URL**    | `https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score` |
| **Body**   | Voir ci‑dessous |

### Body (JSON) – volontairement invalide

```json
{
  "transaction": {
    "transaction_id": "test_format_ko_001",
    "amount": 50.0,
    "currency": "PYC",
    "source_wallet_id": "w1",
    "destination_wallet_id": "w2",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR"
  }
}
```

Ici, **`features` est absent** → le service doit refuser la requête.

### Réponse attendue (400)

```json
{
  "detail": {
    "code": "TRANSACTION_FORMAT_REQUIRED",
    "message": "Format enrichi obligatoire. La transaction doit contenir 'features.transactional' et 'features.historical'. Voir EXEMPLES_JSON_HISTORIQUE.md."
  }
}
```

**Interprétation** : validation du format côté API.

---

# Référence : décisions et seuils

| Decision | Signification | Action |
|----------|---------------|--------|
| `APPROVE` | Transaction normale | ✅ Approuver |
| `REVIEW`  | Transaction suspecte | ⚠️ Revue humaine |
| `BLOCK`   | Très suspect ou règle | 🚫 Bloquer |

**Seuils (ex. v1.0.0-test)** :
- **BLOCK** : `risk_score ≥ 0.7410`
- **REVIEW** : `0.6461 ≤ risk_score < 0.7410`
- **APPROVE** : `risk_score < 0.6461`

Les valeurs réelles dépendent du modèle déployé (voir `artifacts/vX.X.X/thresholds.json`).

---

# Dépannage

### 404 Not Found

- Vérifier l’URL : `/score` (pas `/api/score`).
- Vérifier que le service est déployé : `GET .../health`.

### 400 Bad Request (TRANSACTION_FORMAT_REQUIRED)

- La transaction doit contenir **`features.transactional`** et **`features.historical`**.
- Utiliser les exemples de **EXEMPLES_JSON_HISTORIQUE.md**.

### 422 Unprocessable Entity

- Vérifier que le JSON est valide et que la structure est bien `transaction` + `transaction.features.transactional` + `transaction.features.historical`.

### 500 Internal Server Error

- Consulter les logs Cloud Run :
  ```bash
  gcloud run services logs read sentinelle-ml-engine --region=europe-west1 --project=sentinelle-485209 --limit=50
  ```
- Tester le health check : `GET .../health`.

### Timeout

- Augmenter le timeout dans Postman (Settings → Request timeout).
- Vérifier les ressources CPU/RAM du service Cloud Run.

---

# Checklist Postman

Avant d’envoyer une requête POST /score :

- [ ] Method : `POST`
- [ ] URL : `.../score`
- [ ] Header : `Content-Type: application/json`
- [ ] Body : raw → JSON
- [ ] `transaction.features.transactional` présent
- [ ] `transaction.features.historical` présent

Pour plus de détails sur les champs et scénarios : **EXEMPLES_JSON_HISTORIQUE.md**, **JSON_COMPLET_50_FEATURES.md**.
