# 🎯 Scoring ML

Guide complet du pipeline de scoring : de la transaction à la décision finale.

---

## 📋 Vue d'Ensemble

Le scoring combine **3 signaux** pour produire une décision finale :

1. **Règles métier** (déterministe, explicable)
2. **Modèle supervisé** (LightGBM - patterns connus)
3. **Modèle non supervisé** (IsolationForest - anomalies)

**Pipeline complet** :
```
Transaction enrichie
  ↓
1. Feature Engineering (extraction)
  ↓
2. Règles métier
  ├─> Si BLOCK → Arrêt immédiat
  └─> Sinon → Continue
  ↓
3. Scoring ML (si pas BLOCK)
  ├─> Modèle Supervisé (LightGBM)
  └─> Modèle Non Supervisé (IsolationForest)
  ↓
4. Score global (agrégation)
  ↓
5. Décision finale (BLOCK/REVIEW/APPROVE)
```

---

## 🚀 Quick Start

### Utiliser l'API ML Engine

```bash
curl -X POST https://sentinelle-ml-engine-xxx.run.app/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {
      "transaction_id": "tx_001",
      "amount": 150.0,
      "currency": "PYC",
      "source_wallet_id": "wallet_001",
      "destination_wallet_id": "wallet_002",
      "transaction_type": "TRANSFER",
      "direction": "outgoing",
      "created_at": "2026-01-23T12:00:00Z"
    },
    "context": {
      "source_wallet": {"balance": 1000.0, "status": "active"},
      "user": {"status": "active", "risk_level": "low"}
    }
  }'
```

**Réponse** :
```json
{
  "risk_score": 0.75,
  "decision": "REVIEW",
  "reasons": ["RULE_FREQ_SPIKE", "high_velocity"],
  "model_version": "v1.0.0"
}
```

---

## 🔄 Pipeline Complet

### Étape 1 : Feature Engineering

**Objectif** : Extraire les features depuis la transaction enrichie

**Code** : `src/features/pipeline.py` → `FeaturePipeline`

**Format d'entrée** : Transaction enrichie avec `features.historical` pré-calculées

**Format de sortie** : Dictionnaire de features (transactionnelles + historiques)

**Exemple** :
```python
from src.features.pipeline import FeaturePipeline

pipeline = FeaturePipeline()
features = pipeline.transform(enriched_transaction)
# → {"amount": 150.0, "log_amount": 5.01, "src_tx_count_out_1h": 3, ...}
```

**Features calculées** :
- **Transactionnelles** : `amount`, `log_amount`, `direction_outgoing`, `hour_of_day`, etc.
- **Historiques** : `src_tx_count_out_1h`, `avg_amount_30d`, `is_new_destination_30d`, etc.

**Total** : ~50 features

---

### Étape 2 : Règles Métier

**Objectif** : Évaluer les règles déterministes

**Code** : `src/rules/engine.py` → `RulesEngine`

**Résultat** :
- Si `BLOCK` → Arrêt immédiat (pas de scoring ML)
- Sinon → Continue avec `rule_score` et `boost_factor`

**Exemple** :
```python
from src.rules.engine import RulesEngine

engine = RulesEngine()
rules_output = engine.evaluate(transaction, features, context)

if rules_output.decision == "BLOCK":
    return {"decision": "BLOCK", "reasons": rules_output.reasons}
```

**Voir** : [02_REGLES.md](02_REGLES.md) pour les détails

---

### Étape 3 : Scoring ML

**Objectif** : Obtenir les scores des modèles ML

#### Modèle Supervisé (LightGBM)

**Dataset d'entraînement** : PaySim (avec labels `is_fraud`)

**Sortie** : `supervised_score` [0,1] = probabilité de fraude

**Code** : `src/models/supervised/predictor.py` → `SupervisedPredictor`

**Exemple** :
```python
from src.models.supervised.predictor import SupervisedPredictor

predictor = SupervisedPredictor.load_version("v1.0.0", artifacts_dir)
supervised_score = predictor.predict(features)
# → 0.75 (75% de probabilité de fraude)
```

#### Modèle Non Supervisé (IsolationForest)

**Dataset d'entraînement** : Payon Legit (transactions normales uniquement)

**Sortie** : `unsupervised_score` [0,1] = score d'anomalie calibré

**Code** : `src/models/unsupervised/predictor.py` → `UnsupervisedPredictor`

**Exemple** :
```python
from src.models.unsupervised.predictor import UnsupervisedPredictor

predictor = UnsupervisedPredictor.load_version("v1.0.0", artifacts_dir)
unsupervised_score = predictor.predict(features)
# → 0.60 (60% d'anomalie)
```

---

### Étape 4 : Score Global

**Objectif** : Combiner les 3 signaux en un score unique

**Formule** :
```
risk_score = (0.2 × rule_score + 0.6 × supervised_score + 0.2 × unsupervised_score) × boost_factor
```

**Poids par défaut** :
- Règles : 20%
- Supervisé : 60%
- Non supervisé : 20%

**Code** : `src/scoring/scorer.py` → `GlobalScorer`

**Exemple** :
```python
from src.scoring.scorer import GlobalScorer

scorer = GlobalScorer()
risk_score = scorer.compute_score(
    rule_score=0.3,
    supervised_score=0.75,
    unsupervised_score=0.60,
    boost_factor=1.2,  # Boost de +20% (règle R9 déclenchée)
)
# → 0.75 (score global)
```

**Configuration** : `configs/scoring_config.yaml`

---

### Étape 5 : Décision Finale

**Objectif** : Appliquer les seuils pour décider (BLOCK/REVIEW/APPROVE)

**Seuils** (par défaut) :
- `BLOCK` : `risk_score >= 0.99` (top 0.1%)
- `REVIEW` : `risk_score >= 0.99` (top 1%)
- `APPROVE` : `risk_score < 0.99` (reste)

**Code** : `src/scoring/decision.py` → `DecisionEngine`

**Exemple** :
```python
from src.scoring.decision import DecisionEngine

engine = DecisionEngine()
decision = engine.decide(
    risk_score=0.75,
    reasons=["RULE_FREQ_SPIKE"],
    hard_block=False,
    model_version="v1.0.0",
)
# → Decision(risk_score=0.75, decision="REVIEW", reasons=[...])
```

**Configuration** : `configs/scoring_config.yaml` → `thresholds`

---

## 🔌 Utilisation de l'API ML Engine

### Endpoint : POST /score

**URL** : `https://sentinelle-ml-engine-xxx.run.app/score`

**Méthode** : `POST`

**Headers** :
```
Content-Type: application/json
```

**Body** :
```json
{
  "transaction": {
    "transaction_id": "tx_001",
    "amount": 150.0,
    "currency": "PYC",
    "source_wallet_id": "wallet_001",
    "destination_wallet_id": "wallet_002",
    "transaction_type": "TRANSFER",
    "direction": "outgoing",
    "created_at": "2026-01-23T12:00:00Z",
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
    },
    "destination_wallet": {
      "status": "active"
    }
  }
}
```

**Réponse** :
```json
{
  "risk_score": 0.75,
  "decision": "REVIEW",
  "reasons": ["RULE_FREQ_SPIKE", "high_velocity"],
  "model_version": "v1.0.0"
}
```

### Endpoint : GET /health

**Vérifier l'état du service** :

```bash
curl https://sentinelle-ml-engine-xxx.run.app/health
```

**Réponse** :
```json
{
  "status": "healthy",
  "model_version": "v1.0.0",
  "supervised_loaded": true,
  "unsupervised_loaded": true
}
```

---

## 📊 Interprétation des Résultats

### Décisions

| Décision | Signification | Action |
|----------|---------------|--------|
| **APPROVE** | Transaction normale | Autoriser |
| **REVIEW** | Transaction suspecte | Révision manuelle |
| **BLOCK** | Transaction frauduleuse | Bloquer |

### Risk Score

**Échelle** : [0, 1]

- **0.0 - 0.5** : Risque faible → `APPROVE`
- **0.5 - 0.8** : Risque moyen → `REVIEW`
- **0.8 - 1.0** : Risque élevé → `BLOCK`

**Note** : Les seuils exacts sont configurés dans `scoring_config.yaml`

### Reasons

**Format** : Liste de `reason_code` (ex: `["RULE_FREQ_SPIKE", "high_velocity"]`)

**Types** :
- **Règles** : `RULE_*` (explicables, déterministes)
- **Signaux ML** : `high_velocity`, `amount_unusual` (si disponibles)

**Priorité** : Les raisons des règles sont prioritaires (100% explicables)

---

## 🔧 Configuration

### Poids du Score Global

**Fichier** : `configs/scoring_config.yaml`

**Modifier** :
```yaml
scoring:
  weights:
    rule_score: 0.2      # Poids des règles
    supervised: 0.6      # Poids du modèle supervisé
    unsupervised: 0.2     # Poids du modèle non supervisé
```

### Seuils de Décision

**Fichier** : `configs/scoring_config.yaml`

**Modifier** :
```yaml
scoring:
  thresholds:
    block: 0.99   # Top 0.1% → BLOCK
    review: 0.99  # Top 1% → REVIEW
```

**Calcul des seuils** : Voir [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md) - Calibration

---

## 🏗️ Architecture du Flux

### Backend API → ML Engine

```
Backend API (Cloud Run)
  ↓
1. Reçoit la transaction
2. Enrichit avec features historiques (DB)
3. Appelle ML Engine
  ↓
ML Engine (Cloud Run Service)
  ↓
4. Feature Engineering (extraction)
5. Règles métier
6. Scoring ML (supervisé + non supervisé)
7. Score global
8. Décision finale
  ↓
Retourne {risk_score, decision, reasons}
  ↓
Backend API
  ↓
9. Sauvegarde dans DB (ai_decisions)
10. Retourne la réponse
```

**Voir** : [ARCHITECTURE_FLUX.md](ARCHITECTURE_FLUX.md) pour les détails

---

## 💻 Code Complet

### Dans l'API ML Engine

**Fichier** : `api/main.py`

```python
@app.post("/score")
async def score_transaction(request: ScoreRequest):
    transaction = request.transaction
    context = request.context or {}
    
    # 1. Feature Engineering
    features = feature_pipeline.transform(transaction)
    
    # 2. Règles métier
    rules_output = rules_engine.evaluate(transaction, features, context)
    if rules_output.decision == "BLOCK":
        return {"decision": "BLOCK", ...}
    
    # 3. Scoring ML
    supervised_score = supervised_predictor.predict(features)
    unsupervised_score = unsupervised_predictor.predict(features)
    
    # 4. Score global
    risk_score = global_scorer.compute_score(
        rule_score=rules_output.rule_score,
        supervised_score=supervised_score,
        unsupervised_score=unsupervised_score,
        boost_factor=rules_output.boost_factor,
    )
    
    # 5. Décision finale
    decision = decision_engine.decide(risk_score, ...)
    
    return {"risk_score": decision.risk_score, "decision": decision.decision, ...}
```

---

## 📈 Performance

### Latence Cible

- **Feature Engineering** : < 50ms
- **Règles métier** : < 10ms
- **Scoring ML** : < 100ms
- **Total** : < 200ms (objectif)

### Optimisations

- **Modèles chargés au démarrage** (pas à chaque requête)
- **Features historiques pré-calculées** (côté backend)
- **Cache des règles** (évaluation rapide)

---

## 🐛 Dépannage

### Erreur : "Modèle non disponible"

**Solution** : Vérifier que les modèles sont bien déployés

```bash
# Vérifier les artefacts
gsutil ls gs://sentinelle-485209-ml-data/artifacts/v1.0.0/

# Vérifier le health check
curl https://sentinelle-ml-engine-xxx.run.app/health
```

### Erreur : "Features manquantes"

**Solution** : Vérifier que la transaction est bien enrichie

```json
{
  "transaction": {...},
  "features": {
    "historical": {
      "avg_amount_30d": 85.5,
      "tx_last_10min": 3,
      ...
    }
  }
}
```

---

## 📚 Pour Aller Plus Loin

### Versioning des Modèles

Les modèles sont versionnés (SemVer) :

```python
# Charger une version spécifique
predictor = SupervisedPredictor.load_version("v1.0.0", artifacts_dir)

# Ou utiliser "latest"
predictor = SupervisedPredictor.load_version("latest", artifacts_dir)
```

**Voir** : [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md) - Versioning

### Monitoring

Chaque décision inclut `model_version` pour le monitoring :

```json
{
  "risk_score": 0.75,
  "decision": "REVIEW",
  "model_version": "v1.0.0"  // ← Pour le monitoring
}
```

---

## ✅ Checklist

- [ ] ML Engine déployé sur Cloud Run
- [ ] Modèles chargés (vérifier `/health`)
- [ ] Transaction enrichie avec features historiques
- [ ] Context fourni (wallet, user info)
- [ ] Tester avec des exemples

---

**Besoin d'intégrer l'API ?** Voir [04_DEPLOIEMENT.md](04_DEPLOIEMENT.md) pour le déploiement.

