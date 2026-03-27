# 📊 Monitoring ML – Vertex AI Model Monitoring (GCS) + MLflow (training)

Monitoring en production via **Vertex AI Model Monitoring** alimenté par les logs d’inférence écrits en **GCS** (`monitoring/inference_logs/`).
**MLflow** est utilisé pour l’entraînement (métriques + artefacts) et le versioning des modèles.

---

## 🎯 Objectif

Centraliser le suivi des performances des modèles ML via **MLflow (entraînement)** et **Vertex AI Model Monitoring (inférence)** pour :

1. **Entraînement** : visualiser les métriques de chaque run (accuracy, F1, PR-AUC, seuils)
2. **Inférence** : suivre le drift des données et des prédictions en production (Vertex AI à partir des logs GCS)
3. **Comparaison** : comparer les runs entre versions (ex. v1.0.0 vs v2.0.0)
4. **Traçabilité** : garder un historique des entraînements et des artefacts

---

## 🔗 Intégration

### Flux actuel

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUX D'ENTRAÎNEMENT                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  Google Cloud Console                    Databricks MLflow
  (Cloud Run Jobs)                              │
         │                                      │
         │ 1. Lancement job                     │
         │    sentinelle-training               │
         ▼                                      │
  ┌──────────────────┐                         │
  │ train.py         │                         │
  │ - Préparation    │                         │
  │ - Features       │                         │
  │ - LightGBM       │                         │
  │ - IsolationForest│                         │
  │ - Seuils         │                         │
  │ - Artefacts → GCS│                         │
  └────────┬─────────┘                         │
           │                                   │
           │ 2. Transposition / sync            │
           │    (manuel ou script)              │
           └──────────────────────────────────►│
                                               │
                                    ┌──────────▼──────────┐
                                    │ MLflow Experiments   │
                                    │ - Sentinelle Prod    │
                                    │ - Sentinelle Test    │
                                    │ - Sentinelle Payon   │
                                    └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUX D'INFÉRENCE                                     │
└─────────────────────────────────────────────────────────────────────────────┘

  ML Engine (Cloud Run)  ──►  GCS (inference_logs)  ──►  Vertex AI Model Monitoring (drift)
```

### Plateforme cible

| Composant | Plateforme |
|-----------|------------|
| **Entraînement** | Google Cloud Run Jobs |
| **Scoring** | Google Cloud Run (ML Engine) |
| **Monitoring centralisé** | **Vertex AI Model Monitoring** |
| **Vertex AI** | ✅ Opérationnel (drift via baseline + inference logs) |

---

## ✅ Développement déjà réalisé

### 1. Entraînement MLflow (Databricks)

| Élément | Statut | Détail |
|---------|--------|--------|
| **Experiments** | ✅ Créés | Sentinelle Production, Sentinelle Test, Sentinelle Payon |
| **Run exemple** | ✅ Réalisé | `train-v2.0.1-mlflow` (mars 2026) |
| **Métriques loguées** | ✅ | val_accuracy, val_f1, val_pr_auc, block_threshold, review_threshold |
| **Artefacts** | ✅ | baseline_train.jsonl, feature_schema.json, thresholds.json |
| **Workspace** | ✅ | `https://dbc-576fb506-d185.cloud.databricks.com` |

### 2. Entraînement (Google Cloud)

| Élément | Statut | Fichier / Référence |
|---------|--------|---------------------|
| **train.py** | ✅ | `models/scripts/train.py` |
| **Calibration seuils** | ✅ | block_threshold, review_threshold |
| **Export baseline GCS** | ✅ | Si `EXPORT_BASELINE_GCS_BUCKET` défini |
| **Artefacts GCS** | ✅ | `gs://sentinelle-485209-ml-data/artifacts/vX.X.X/` |

### 3. Inférence (ML Engine)

| Élément | Statut | Fichier / Référence |
|---------|--------|---------------------|
| **Logging GCS** | ✅ | `models/src/monitoring/gcs_logger.py` |
| **Variables Cloud Run** | ✅ | MONITORING_GCS_BUCKET, MONITORING_SAMPLE_RATE |
| **Format JSONL** | ✅ | request_time, features, risk_score, decision, model_version |

---

## 🚧 Développement à faire

### Priorité 1 : Intégration MLflow dans l'entraînement

| Tâche | Description | Fichier concerné |
|-------|-------------|------------------|
| **1.1** | Ajouter `mlflow` au `requirements.txt` ou `pyproject.toml` | `models/` |
| **1.2** | Instrumenter `train.py` avec `mlflow.log_metric()`, `mlflow.log_param()`, `mlflow.log_artifact()` | `models/scripts/train.py` |
| **1.3** | Définir l’experiment MLflow (ex. `/Shared/Sentinelle Production`) | Variable d’env ou config |
| **1.4** | Logger les métriques : val_accuracy, val_f1, val_pr_auc, block_threshold, review_threshold | `train.py` + `supervised/train.py` |
| **1.5** | Logger les artefacts : feature_schema.json, thresholds.json, baseline_train.jsonl | `train.py` |

### Priorité 2 : Monitoring inférence via Vertex AI Model Monitoring

Le drift est calculé par **Vertex AI Model Monitoring** à partir de :
- des logs d’inférence écrits par l’API dans `gs://sentinelle-485209-ml-data/monitoring/inference_logs/` (JSONL)
- d’une baseline exportée depuis l’entraînement dans `gs://<bucket>/monitoring/baseline/<version>/train_features.jsonl` (si disponible)

Procédure complète : voir `06_MONITORING_VERTEX.md`.

### Priorité 4 : Comparaison des runs

| Tâche | Description |
|-------|-------------|
| **4.1** | Documenter l’usage de "Compare" dans MLflow UI |
| **4.2** | Définir des tags par version (ex. `version=2.0.0`, `env=production`) |

---

## 📋 Métriques à suivre

### Entraînement (à logger dans MLflow)

| Métrique | Description | Source |
|----------|-------------|--------|
| **val_accuracy** | Accuracy sur le validation set | Modèle supervisé |
| **val_f1** | F1-score sur le validation set | Modèle supervisé |
| **val_pr_auc** | Precision-Recall AUC | Modèle supervisé |
| **block_threshold** | Seuil BLOCK (top 0.1–0.5 %) | Calibration |
| **review_threshold** | Seuil REVIEW (top 1 %) | Calibration |

### Paramètres à logger

| Paramètre | Exemple |
|-----------|---------|
| version | 1.0.0-monitoring |
| local | True |
| data_dir | Data/processed |
| config_dir | configs |
| artifacts_dir | artifacts |

### Inférence (Vertex AI Model Monitoring)

Vertex AI calcule automatiquement :

| Objectif | Description |
|----------|-------------|
| Input feature drift | Divergence des distributions des features |
| Output drift | Divergence de `risk_score` et `decision` |
| Alertes | Déclenchement selon les seuils configurés (numeric: Jensen–Shannon, categorical: L-infinity) |

---

## 📁 Structure des experiments Databricks

| Experiment | Usage |
|------------|-------|
| **Sentinelle Production** | Runs de modèles déployés en prod |
| **Sentinelle Test** | Runs de validation / tests |
| **Sentinelle Payon** | Runs POC / développement |

---

## 🔧 Configuration

### Variables d'environnement (entraînement)

| Variable | Description | Exemple |
|----------|-------------|---------|
| `MLFLOW_TRACKING_URI` | URI du serveur MLflow Databricks | `databricks` ou URL complète |
| `DATABRICKS_HOST` | Host Databricks | `https://dbc-576fb506-d185.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | Token d’accès | (secret) |
| `MLFLOW_EXPERIMENT_NAME` | Nom de l’experiment | `/Shared/Sentinelle Production` |

### Variables d'environnement (ML Engine – inférence)

| Variable | Description | Valeur actuelle |
|----------|-------------|-----------------|
| `MONITORING_GCS_BUCKET` | Bucket pour les logs | sentinelle-485209-ml-data |
| `MONITORING_GCS_PREFIX` | Préfixe des objets | monitoring/inference_logs |
| `MONITORING_SAMPLE_RATE` | Taux d’échantillonnage | 0.1 (10 %) |

---

## 📌 Checklist de suivi de l'intégration

### Phase 1 : Entraînement

- [ ] MLflow installé dans l’environnement d’entraînement - [x] `train.py` instrumenté avec `mlflow.start_run()`, `log_metric`, `log_param`, `log_artifact`
- [x] Tracking URI Databricks configuré (local)
- [x] Premier run visible dans MLflow : train-v2.0.1-mlflow (mars 2026)
- [ ] Comparaison de 2 runs fonctionnelle dans l’UI MLflow

### Phase 2 : Inférence (drift via Vertex AI Model Monitoring)

- [x] Stratégie choisie : Vertex AI Model Monitoring (target = logs GCS `monitoring/inference_logs/`)
- [ ] Runs de monitoring visibles dans Vertex AI (drift input/output)
- [ ] Alertes ou seuils définis (optionnel)

### Phase 3 : Documentation et processus

- [ ] Procédure de lancement d’un entraînement documentée
- [ ] Procédure de consultation des runs MLflow documentée
- [ ] Rôle et responsabilités définis (qui consulte, qui lance, qui valide)

---

## 📚 Références

| Document | Contenu |
|----------|---------|
| [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md) | Entraînement local et Cloud |
| [04_DEPLOIEMENT.md](04_DEPLOIEMENT.md) | Déploiement ML Engine et jobs |
| [06_MONITORING_VERTEX.md](06_MONITORING_VERTEX.md) | Vertex AI (opérationnel, drift via GCS) |

---

## 🚀 Déploiement en production

Après un entraînement avec MLflow :

```bash
cd models

# 1. Upload des artefacts vers GCS
./scripts/upload-artifacts.sh "2.0.1-mlflow"

# 2. Déployer le ML Engine v2
./scripts/deploy-ml-engine.sh "sentinelle-485209" "sentinelle-ml-engine-v2" "europe-west1" "2.0.1-mlflow"
```

---

## ⚠️ Note sur Vertex AI

Le monitoring via **Vertex AI Model Monitoring** est désormais opérationnel (drift input/output basé sur `monitoring/inference_logs/` + baseline exportée).

---

**Version** : 1.0.0  
**Dernière mise à jour** : Mars 2026  
**Statut** : Phase 1 complétée – Intégration MLflow opérationnelle
