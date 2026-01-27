# 🧪 Guide Postman : Tester le ML Engine

Guide complet pour tester le ML Engine avec Postman.

---

## ⚠️ Format obligatoire : transaction enrichie uniquement

**Toute requête POST /score doit envoyer une transaction au format enrichi.**

- `transaction` doit contenir **`features.transactional`** et **`features.historical`**.
- Pour un **nouveau compte** (sans historique), envoyez quand même `transactional` et `historical` avec des valeurs à 0 / -1.0 / 1 (voir `EXEMPLES_JSON_HISTORIQUE.md`).
- Une requête sans `features` ou sans `transactional`/`historical` renvoie **400 Bad Request**.

Les exemples complets (normale, suspecte, blocage, new user) sont dans **`EXEMPLES_JSON_HISTORIQUE.md`**.

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

## 🎯 Exemple 1 : New user (format enrichi minimal)

Transaction sans historique : `transactional` + `historical` avec valeurs "nouveau compte" (0, -1.0, 1).

**URL** : `POST https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score`

**Body** : voir **EXEMPLES_JSON_HISTORIQUE.md** § « Nouveau compte (new user) ».

Exemple minimal (copier-coller) :

```json
{
  "transaction": {
    "transaction_id": "test_new_001",
    "amount": 50.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_new_001",
    "destination_wallet_id": "wallet_dest_001",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "features": {
      "transactional": {
        "amount": 50.0,
        "log_amount": 3.93,
        "currency_is_pyc": true,
        "direction_outgoing": 1,
        "hour_of_day": 14,
        "day_of_week": 1,
        "transaction_type_TRANSFER": 1
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
  },
  "context": {
    "source_wallet": { "balance": 1000.0, "status": "active" },
    "user": { "status": "active", "risk_level": "low" }
  }
}
```

### Réponse attendue

`decision: "APPROVE"` (ou `REVIEW` selon le modèle), `risk_score` numérique.

---

## 📂 Exemples complets (normale, suspecte, blocage)

Tous les scénarios au format enrichi (normale avec historique, suspecte, BLOCK, new user) sont dans **EXEMPLES_JSON_HISTORIQUE.md**. Utilisez ces JSON tels quels dans Postman.

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

## 📝 Structure de la requête (format enrichi uniquement)

La requête doit contenir :

- **`transaction`** : champs métier + **`features.transactional`** et **`features.historical`** (obligatoires).
- **`context`** : optionnel (`source_wallet`, `user`, etc.).

Les noms exacts des champs dans `transactional` et `historical` sont définis dans **EXEMPLES_JSON_HISTORIQUE.md** et **JSON_COMPLET_50_FEATURES.md**.

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

### Erreur 400 Bad Request (TRANSACTION_FORMAT_REQUIRED)

**Cause** : La transaction n’a pas le format enrichi attendu.

**Solution** :
- La transaction doit contenir **`features.transactional`** et **`features.historical`**.
- Utilisez les exemples de **EXEMPLES_JSON_HISTORIQUE.md** (new user, normale, suspecte, blocage).

### Erreur 422 Unprocessable Entity

**Cause** : Format JSON invalide ou champs manquants.

**Solution** :
- Vérifiez que le JSON est valide.
- Vérifiez la structure : `transaction`, `transaction.features.transactional`, `transaction.features.historical`.

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

