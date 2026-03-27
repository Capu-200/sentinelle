# 🛡️ Payon ML Engine - Documentation

Moteur de scoring ML pour la détection de fraude bancaire, déployé sur Google Cloud Run.

## 📋 Vue d'Ensemble

Le ML Engine analyse chaque transaction en temps réel et produit :
- Un **score de risque** (0 → 1)
- Une **décision** : `APPROVE`, `REVIEW`, `BLOCK`
- Une **explication** : liste de règles/signaux déclenchés

### Architecture

```
Backend API (Cloud Run)
  ↓
ML Engine (Cloud Run Service) ← Ce projet
  ├─> Feature Engineering
  ├─> Règles métier
  ├─> Scoring ML (supervisé + non supervisé)
  └─> Décision finale
  ↓
Retourne {risk_score, decision, reasons}
```

---

## 📚 Documentation

### 🎓 [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md)
**Pour** : Entraîner et déployer les modèles ML

**Deux workflows disponibles** :
- **☁️ Cloud** : Entraînement sur Cloud Run Jobs (automatisé, scalable)
- **💻 Local** : Entraînement local → Upload vers Cloud Storage (dataset complet, pas de timeout)

**Contenu** :
- Préparation des données (mapping PaySim, split temporel)
- Feature engineering pour l'entraînement
- Ajustement des paramètres des modèles
- Entraînement (LightGBM supervisé + IsolationForest non supervisé)
- Calibration des seuils
- Versioning des modèles
- Déploiement (Cloud ou Local)

**Quand l'utiliser** : Pour créer ou mettre à jour les modèles ML

---

### ⚖️ [02_REGLES.md](02_REGLES.md)
**Pour** : Comprendre et configurer les règles métier

- Liste complète des règles (R1-R15)
- Configuration des règles
- Exemples de règles déclenchées
- Intégration dans le pipeline

**Quand l'utiliser** : Pour modifier les règles métier ou comprendre leur fonctionnement

---

### 🎯 [03_SCORING.md](03_SCORING.md)
**Pour** : Comprendre le pipeline de scoring et utiliser l'API

- Pipeline complet (features → règles → ML → décision)
- Utilisation de l'API ML Engine
- Interprétation des résultats
- Architecture du flux

**Quand l'utiliser** : Pour intégrer le ML Engine ou comprendre le scoring

---

### ☁️ [04_DEPLOIEMENT.md](04_DEPLOIEMENT.md)
**Pour** : Déployer le ML Engine et les jobs d'entraînement sur Google Cloud

- Déploiement du ML Engine (scoring) sur Cloud Run
- Déploiement du Training Job sur Cloud Run Jobs
- Configuration Cloud (variables d'environnement, ressources)
- Monitoring et logs

**Quand l'utiliser** : Pour déployer en production ou mettre à jour les services

---

### 🧪 [05_POSTMAN_TESTS.md](05_POSTMAN_TESTS.md)
**Pour** : Tester le ML Engine avec Postman

- Cas de test complets : Health check, APPROVE, REVIEW, BLOCK, new user, erreur 400
- Body JSON prêts à l’emploi pour chaque scénario
- Dépannage (404, 400, 422, 500, timeout)
- Référence décisions et seuils

**Quand l'utiliser** : Pour valider l’API en local ou après déploiement

---

### 📊 [07_MONITORING_MLFLOW.md](07_MONITORING_MLFLOW.md)
**Pour** : 
1) Entraîner et versionner les artefacts avec MLflow,  
2) Monitorer le drift en production avec Vertex AI Model Monitoring (logs GCS)

- Objectif : entraînement (MLflow) + monitoring drift prod (Vertex AI)
- Logs d’inférence pris dans `monitoring/inference_logs/` (GCS)
- Baseline optionnelle depuis `monitoring/baseline/<version>/...`
- Checklist + configuration

**Quand l'utiliser** : Pour le suivi des performances et l'intégration MLflow

---

### 📋 [06_MONITORING_VERTEX.md](06_MONITORING_VERTEX.md)
**Pour** : Référence Vertex AI (opérationnel) – Voir [07_MONITORING_MLFLOW.md](07_MONITORING_MLFLOW.md) pour le suivi complet.

---
### 📌 [08_MONITORING_VERTEX_RUN_AFTER_DEPLOY.md](08_MONITORING_VERTEX_RUN_AFTER_DEPLOY.md)
**Pour** : Procédure automatisée/reproductible pour lancer un run Vertex AI après chaque nouveau déploiement de modèle, à partir du trafic réel en prod, avec pipeline `GCS -> BigQuery -> vue 24h -> Vertex`

---

## 🚀 Quick Start

### 1. Entraîner un modèle

**Option A : Cloud** (recommandé pour production)
```bash
cd models
./scripts/deploy-training-job.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"
```

**Option B : Local** (recommandé pour développement)
```bash
cd models
./scripts/train-local.sh 1.0.0
./scripts/upload-artifacts.sh 1.0.0
```

Voir [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md) pour les détails des deux workflows.

---

### 2. Déployer le ML Engine

```bash
cd models
./scripts/deploy-ml-engine.sh \
  "sentinelle-485209" \
  "sentinelle-ml-engine" \
  "europe-west1" \
  "1.0.0"
```

Voir [04_DEPLOIEMENT.md](04_DEPLOIEMENT.md) pour les détails.

---

### 3. Utiliser l'API

```bash
curl -X POST https://sentinelle-ml-engine-xxx.run.app/score \
  -H "Content-Type: application/json" \
  -d '{
    "transaction": {...},
    "context": {...}
  }'
```

Voir [03_SCORING.md](03_SCORING.md) pour les détails.

---

## 🏗️ Structure du Projet

```
models/
├── api/                    # ML Engine API (FastAPI)
│   └── main.py            # Endpoint /score
├── src/                    # Code source ML
│   ├── data/              # Préparation des données
│   ├── features/          # Feature engineering
│   ├── models/            # Modèles ML (supervisé + non supervisé)
│   ├── rules/             # Règles métier
│   └── scoring/           # Scoring et décision
├── scripts/               # Scripts utilitaires
│   ├── train.py          # Entraînement
│   └── deploy-*.sh       # Déploiement Cloud
├── configs/               # Configurations (YAML)
├── schemas/               # Schémas JSON
└── docs/                  # Documentation détaillée (legacy)
```

---

## 🔧 Technologies

- **Python 3.11+**
- **FastAPI** : API ML Engine
- **LightGBM** : Modèle supervisé
- **IsolationForest** : Modèle non supervisé
- **Google Cloud Run** : Déploiement
- **Google Cloud Storage** : Stockage des artefacts

---

## 📖 Pour Aller Plus Loin

- **Nouveau sur le projet ?** → Commencez par [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md)
- **Modifier les règles ?** → Voir [02_REGLES.md](02_REGLES.md)
- **Intégrer l'API ?** → Voir [03_SCORING.md](03_SCORING.md)
- **Déployer en production ?** → Voir [04_DEPLOIEMENT.md](04_DEPLOIEMENT.md)
- **Tester avec Postman ?** → Voir [05_POSTMAN_TESTS.md](05_POSTMAN_TESTS.md)
- **Monitorer les modèles (Vertex AI drift + MLflow entraînement) ?** → Voir [07_MONITORING_MLFLOW.md](07_MONITORING_MLFLOW.md)

---

## 🤝 Contribution

Ce projet fait partie de Payon, une application de détection de fraude bancaire.

**Questions ?** Consultez la documentation correspondante ou contactez l'équipe.

---

**Version** : 1.0.0  
**Dernière mise à jour** : Janvier 2026
