# 🚀 Guide : Déployer et Tester le ML Engine

Guide étape par étape pour déployer vos modèles sur Google Cloud Run et tester avec Postman.

---

## ✅ Vérification Préalable

### 1. Vous avez déjà :
- ✅ Modèles entraînés (`artifacts/v1.0.0-test/`)
- ✅ API ML Engine prête (`api/main.py`) avec **règles + scoring**
- ✅ Scripts de déploiement

### 2. Ce qui est inclus dans l'API :
- ✅ **Règles métier** (R1-R15) - évaluation déterministe
- ✅ **Scoring ML** (supervisé + non supervisé)
- ✅ **Score global** (combinaison règles + ML)
- ✅ **Décision finale** (BLOCK/REVIEW/APPROVE)

**→ Tout est déjà prêt ! Pas besoin de déployer séparément les règles et le scoring.**

---

## 📋 Étapes de Déploiement

### Étape 1 : Uploader les Modèles vers Cloud Storage

**Objectif** : Mettre les modèles `.pkl` dans Cloud Storage pour que Cloud Run puisse les charger.

```bash
cd models

# Uploader la version 1.0.0-test
./scripts/upload-artifacts.sh "1.0.0-test"
```

**Ce que ça fait** :
- ✅ Vérifie que les artefacts existent localement
- ✅ Crée le bucket Cloud Storage si nécessaire
- ✅ Upload les fichiers vers `gs://sentinelle-485209-ml-data/artifacts/v1.0.0-test/`

**Vérification** :
```bash
gsutil ls -r gs://sentinelle-485209-ml-data/artifacts/v1.0.0-test/
```

Vous devriez voir :
- `supervised_model.pkl`
- `unsupervised_model.pkl`
- `thresholds.json`
- `feature_schema.json`

---

### Étape 2 : Déployer le ML Engine sur Cloud Run

**Objectif** : Déployer l'API de scoring sur Cloud Run pour qu'elle soit accessible via HTTP.

```bash
cd models

./scripts/deploy-ml-engine.sh \
  "sentinelle-485209" \
  "sentinelle-ml-engine" \
  "europe-west1" \
  "1.0.0-test"
```

**Ce que ça fait** :
1. ✅ Active les APIs Google Cloud nécessaires
2. ✅ Construit l'image Docker (avec `Dockerfile.api`)
3. ✅ Déploie sur Cloud Run
4. ✅ Configure les variables d'environnement :
   - `MODEL_VERSION=1.0.0-test`
   - `ARTIFACTS_DIR=/app/artifacts`
   - `BUCKET_NAME=sentinelle-485209-ml-data`
5. ✅ Télécharge automatiquement les modèles depuis GCS au démarrage

**Temps** : ~5-10 minutes (première fois)

**À la fin, vous obtiendrez** :
```
✅ Déploiement terminé!
   URL: https://sentinelle-ml-engine-xxx.run.app
   Health check: https://sentinelle-ml-engine-xxx.run.app/health
   Score endpoint: https://sentinelle-ml-engine-xxx.run.app/score
```

**⚠️ Important** : Notez l'URL, vous en aurez besoin pour Postman !

---

### Étape 3 : Vérifier que le Service Fonctionne

**Health Check** :
```bash
curl https://sentinelle-ml-engine-xxx.run.app/health
```

**Réponse attendue** :
```json
{
  "status": "healthy",
  "model_version": "1.0.0-test",
  "supervised_loaded": true,
  "unsupervised_loaded": true
}
```

Si `supervised_loaded` ou `unsupervised_loaded` est `false`, vérifiez les logs :
```bash
gcloud run services logs read sentinelle-ml-engine \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --limit=50
```

---

## 🧪 Étape 4 : Tester avec Postman

### Configuration Postman

1. **Créer une nouvelle requête POST**
   - URL : `https://sentinelle-ml-engine-xxx.run.app/score`
   - Method : `POST`
   - Headers :
     - `Content-Type: application/json`

2. **Body (JSON)** :

```json
{
  "transaction": {
    "transaction_id": "test_tx_001",
    "amount": 150.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_001",
    "destination_wallet_id": "wallet_002",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR",
    "city": "Paris"
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

3. **Envoyer la requête**

### Réponse Attendue

```json
{
  "risk_score": 0.2345,
  "decision": "APPROVE",
  "reasons": [],
  "model_version": "1.0.0-test"
}
```

**Décisions possibles** :
- `APPROVE` : Transaction normale
- `REVIEW` : Transaction suspecte (nécessite revue humaine)
- `BLOCK` : Transaction très suspecte (bloquée)

---

## 🎯 Exemples de Tests

### Test 1 : Transaction Normale
```json
{
  "transaction": {
    "transaction_id": "test_normal",
    "amount": 50.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_normal",
    "destination_wallet_id": "wallet_dest",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR"
  }
}
```
**Attendu** : `decision: "APPROVE"`, `risk_score` faible (< 0.5)

---

### Test 2 : Transaction Suspecte (Montant Élevé)
```json
{
  "transaction": {
    "transaction_id": "test_suspect",
    "amount": 250.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_suspect",
    "destination_wallet_id": "wallet_new",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR"
  }
}
```
**Attendu** : `decision: "REVIEW"` ou `"BLOCK"`, `risk_score` élevé (> 0.5)

---

### Test 3 : Transaction Bloquée par Règle (Montant > 300)
```json
{
  "transaction": {
    "transaction_id": "test_blocked",
    "amount": 350.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_blocked",
    "destination_wallet_id": "wallet_dest",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2024-01-15T14:30:00Z",
    "country": "FR"
  }
}
```
**Attendu** : `decision: "BLOCK"`, `reasons: ["RULE_MAX_AMOUNT"]`

---

## 🔍 Vérification des Logs

Si quelque chose ne fonctionne pas, vérifiez les logs :

```bash
# Logs en temps réel
gcloud run services logs tail sentinelle-ml-engine \
  --region=europe-west1 \
  --project=sentinelle-485209

# Derniers logs
gcloud run services logs read sentinelle-ml-engine \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --limit=100
```

---

## 🐛 Dépannage

### Problème 1 : `supervised_loaded: false`

**Cause** : Les modèles n'ont pas été téléchargés depuis GCS.

**Solution** :
1. Vérifier que les artefacts sont dans GCS :
   ```bash
   gsutil ls -r gs://sentinelle-485209-ml-data/artifacts/v1.0.0-test/
   ```
2. Vérifier les logs du service pour voir l'erreur
3. Redéployer si nécessaire

---

### Problème 2 : `502 Bad Gateway`

**Cause** : Le service ne démarre pas correctement.

**Solution** :
1. Vérifier les logs (voir ci-dessus)
2. Vérifier que `Dockerfile.api` existe
3. Vérifier que toutes les dépendances sont dans `requirements.txt`

---

### Problème 3 : `400 Bad Request`

**Cause** : Format de la requête incorrect.

**Solution** :
1. Vérifier que le JSON est valide
2. Vérifier que tous les champs requis sont présents :
   - `transaction_id`
   - `amount`
   - `currency`
   - `source_wallet_id`
   - `transaction_type`
   - `direction`

---

## ✅ Checklist Finale

Avant de tester avec Postman :

- [ ] ✅ Modèles uploadés vers GCS (`gsutil ls gs://...`)
- [ ] ✅ ML Engine déployé sur Cloud Run
- [ ] ✅ Health check retourne `"status": "healthy"`
- [ ] ✅ `supervised_loaded: true` et `unsupervised_loaded: true`
- [ ] ✅ URL du service notée
- [ ] ✅ Postman configuré avec la bonne URL

---

## 🎉 C'est Prêt !

Une fois tout déployé, vous pouvez :
1. ✅ Tester avec Postman
2. ✅ Intégrer dans votre backend API
3. ✅ Monitorer les performances

**Prochaine étape** : Intégrer le ML Engine dans votre backend API (`backend/app/main.py`) pour scorer automatiquement toutes les transactions.

