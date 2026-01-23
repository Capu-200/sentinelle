# 🎓 Entraînement des Modèles ML

Guide complet pour entraîner et déployer les modèles ML sur Google Cloud Run Jobs.

---

## 📋 Vue d'Ensemble

L'entraînement se fait en **4 étapes principales** :

1. **Préparation des données** : Mapping PaySim → Payon, split temporel
2. **Feature Engineering** : Calcul des features transactionnelles et historiques
3. **Entraînement** : LightGBM (supervisé) + IsolationForest (non supervisé)
4. **Déploiement** : Upload vers Cloud Storage, versioning

**Temps estimé** : ~30-45 minutes sur Cloud Run Jobs (8 vCPU, 8GB RAM)

---

## 🚀 Quick Start

### Entraînement sur Google Cloud

```bash
cd models

# 1. Déployer le job
./scripts/deploy-training-job.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"

# 2. Lancer l'entraînement
./scripts/run-training-cloud.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"

# 3. Suivre les logs
gcloud run jobs logs read sentinelle-training \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --limit=100
```

---

## 📊 Étape 1 : Préparation des Données

### Mapping PaySim → Payon

Le dataset PaySim doit être mappé vers le format Payon pour l'entraînement.

**Mapping principal** :
- `step` → `created_at` (conversion en timestamp)
- `type` → `transaction_type`
- `amount` → `amount`
- `nameOrig` → `source_wallet_id`
- `nameDest` → `destination_wallet_id`
- `isFraud` → `is_fraud` (label pour supervisé)

**Code** : `src/data/preparation.py` → `map_paysim_to_payon()`

**Exemple** :
```python
from src.data.preparation import map_paysim_to_payon

payon_df = map_paysim_to_payon(
    paysim_path=Path("Data/raw/paysim dataset.csv"),
    max_amount=None,  # Pas de filtrage
    output_path=Path("Data/processed/paysim_mapped.csv"),
)
```

### Split Temporel

**Important** : Split **temporel** (pas aléatoire) pour éviter le leakage.

**Ratio** : 70% train / 15% val / 15% test

**Code** : `src/data/preparation.py` → `prepare_training_data()`

**Exemple** :
```python
from src.data.preparation import prepare_training_data

train_df, val_df, test_df = prepare_training_data(
    data_path=Path("Data/processed/paysim_mapped.csv"),
    train_ratio=0.7,
    val_ratio=0.15,
    test_ratio=0.15,
)
```

**Validation** : Vérifie qu'il n'y a pas de leakage temporel (train.max < val.min < test.min)

---

## 🔧 Étape 2 : Feature Engineering

### Features Transactionnelles

Features directement extraites de la transaction :

- `amount` : Montant de la transaction
- `log_amount` : log(1 + amount)
- `currency_is_pyc` : Booléen (currency == "PYC")
- `direction_outgoing` : 1 si outgoing, 0 sinon
- `hour_of_day` : Heure (0-23)
- `day_of_week` : Jour de la semaine (0-6)
- Encodage one-hot : `transaction_type`, `country`

**Code** : `src/features/extractor.py` → `extract_transaction_features()`

### Features Historiques

Agrégats calculés depuis l'historique des transactions :

**Fenêtres temporelles** : `5m`, `1h`, `24h`, `7d`, `30d`

**Clés d'agrégation** :
- Wallet source (`source_wallet_id`)
- Wallet destination (`destination_wallet_id`)
- Paire source→destination
- Utilisateur initiateur

**Exemples de features** :
- `src_tx_count_out_1h` : Nombre de transactions sortantes (1h)
- `src_tx_amount_mean_out_7d` : Montant moyen sortant (7j)
- `is_new_destination_30d` : Nouveau destinataire (30j)
- `src_unique_destinations_24h` : Nombre de destinataires uniques (24h)

**Total** : ~36 features historiques

**Code** : `src/features/aggregator.py` → `compute_historical_aggregates()`

### Calcul des Features pour l'Entraînement

**Mode parallèle** (recommandé) :

```python
from src.features.training import compute_features_parallel

features_df = compute_features_parallel(
    transactions_df=train_df,
    n_jobs=7,  # Nombre de processus parallèles
    chunk_size=1000,
    verbose=True,
)
```

**Performance** : ~270-320 it/s sur M2 Pro (10 cores)

**Code** : `src/features/training.py` → `compute_features_parallel()`

---

## 🤖 Étape 3 : Entraînement des Modèles

### Modèle Supervisé (LightGBM)

**Dataset** : PaySim (avec labels `is_fraud`)

**Objectif** : Apprendre à détecter la fraude depuis des exemples labelisés

**Configuration par défaut** :
```python
{
    "objective": "binary",
    "metric": "average_precision",  # PR-AUC
    "num_leaves": 31,
    "learning_rate": 0.05,
    "scale_pos_weight": auto,  # Gère le déséquilibre
    "n_estimators": 1000,
    "early_stopping": 100,
}
```

**Gestion du déséquilibre** :
- `scale_pos_weight` calculé automatiquement
- Optimisation de PR-AUC (robuste aux classes rares)

**Code** : `src/models/supervised/train.py` → `SupervisedModel`

**Exemple** :
```python
from src.models.supervised.train import SupervisedModel

model = SupervisedModel(model_version="1.0.0")
model.train(
    X=train_features,
    y=train_labels,
    val_data=val_features,
    val_labels=val_labels,
)
```

### Modèle Non Supervisé (IsolationForest)

**Dataset** : Payon Legit (transactions normales uniquement)

**Objectif** : Détecter les anomalies (patterns inconnus)

**Configuration par défaut** :
```python
{
    "contamination": 0.1,  # 10% d'anomalies attendues
    "random_state": 42,
    "n_estimators": 100,
}
```

**Calibration** : Scores bruts → [0,1] via quantile mapping

**Code** : `src/models/unsupervised/train.py` → `UnsupervisedModel`

**Exemple** :
```python
from src.models.unsupervised.train import UnsupervisedModel

model = UnsupervisedModel(model_version="1.0.0")
model.train(X=payon_legit_features)  # Pas de labels
```

---

## 📈 Étape 4 : Calibration des Seuils

Les seuils déterminent les décisions finales (BLOCK/REVIEW/APPROVE).

**Méthode** : Quantiles sur le validation set

```python
# Calculer les seuils
block_threshold = val_risk_scores.quantile(0.999)  # Top 0.1%
review_threshold = val_risk_scores.quantile(0.990)  # Top 1%
```

**Vérification** :
- Recall fraude
- Precision sur BLOCK
- PR-AUC
- % BLOCK / % REVIEW

**Sauvegarde** : `thresholds.json` dans les artefacts

---

## 💾 Étape 5 : Versioning et Sauvegarde

### Structure des Artefacts

```
artifacts/
├── v1.0.0/
│   ├── supervised_model.pkl
│   ├── unsupervised_model.pkl
│   ├── feature_schema.json
│   └── thresholds.json
└── latest -> v1.0.0/
```

### Versioning SemVer

- **MAJOR** (2.0.0) : Changement majeur d'architecture
- **MINOR** (1.1.0) : Amélioration des hyperparamètres
- **PATCH** (1.0.1) : Correction de bugs

**Code** : `src/utils/versioning.py` → `save_artifacts()`

---

## ☁️ Étape 6 : Déploiement sur Cloud Run Jobs

### Prérequis

1. **Google Cloud SDK installé**
2. **Authentification** : `gcloud auth login`
3. **Projet configuré** : `gcloud config set project sentinelle-485209`
4. **Données préparées** : `Data/processed/*.csv`

### Déploiement

**Script automatique** :

```bash
./scripts/deploy-training-job.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"
```

**Ce que fait le script** :
1. ✅ Active les APIs nécessaires
2. ✅ Crée le bucket Cloud Storage (`sentinelle-485209-ml-data`)
3. ✅ Upload les données vers Cloud Storage (~874 MB)
4. ✅ Construit l'image Docker
5. ✅ Déploie le job Cloud Run Jobs

**Temps** : ~5-10 minutes (première fois)

### Lancement

```bash
./scripts/run-training-cloud.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"
```

**Temps d'exécution** : ~30-45 minutes

### Suivi des Logs

```bash
# Logs en temps réel
gcloud run jobs logs read sentinelle-training \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --limit=100
```

### Récupération des Artefacts

```bash
# Télécharger depuis Cloud Storage
gsutil -m cp -r gs://sentinelle-485209-ml-data/artifacts/v1.0.0/ ./artifacts/
```

---

## ⚙️ Ajustement des Paramètres

### Hyperparamètres LightGBM

**Fichier** : `configs/model_config.yaml`

**Paramètres principaux** :
- `num_leaves` : Complexité du modèle (défaut: 31)
- `learning_rate` : Vitesse d'apprentissage (défaut: 0.05)
- `n_estimators` : Nombre d'arbres (défaut: 1000)
- `scale_pos_weight` : Gestion du déséquilibre (auto)

**Modifier** :
```python
config = {
    "num_leaves": 63,  # Plus complexe
    "learning_rate": 0.01,  # Plus lent mais meilleur
}
model = SupervisedModel(config=config)
```

### Hyperparamètres IsolationForest

**Paramètres principaux** :
- `contamination` : Proportion d'anomalies attendues (défaut: 0.1)
- `n_estimators` : Nombre d'arbres (défaut: 100)

**Modifier** :
```python
config = {
    "contamination": 0.05,  # Moins d'anomalies attendues
    "n_estimators": 200,  # Plus d'arbres
}
model = UnsupervisedModel(config=config)
```

### Ressources Cloud Run Jobs

**Modifier les ressources** :

```bash
gcloud run jobs update sentinelle-training \
  --region=europe-west1 \
  --cpu=16 \
  --memory=16Gi \
  --project=sentinelle-485209
```

**Plus de CPU = Plus rapide mais plus cher**

---

## 💰 Coûts Estimés

**Par entraînement** :
- **CPU** : 8 vCPU × 2700s × $0.00002400 = **$0.52**
- **RAM** : 8 GB × 2700s × $0.00000250 = **$0.05**
- **Storage** : Négligeable
- **Total** : **~$0.60 par entraînement**

**Pour 10 entraînements** : **~$6**

---

## 🐛 Dépannage

### Erreur : "Dataset PaySim non trouvé"

**Solution** : Vérifier que `Data/processed/paysim_mapped.csv` existe

```bash
ls -lh Data/processed/paysim_mapped.csv
```

### Erreur : "LEAKAGE TEMPOREL DÉTECTÉ"

**Solution** : Le split temporel a détecté un problème. Vérifier les timestamps :

```python
# Vérifier les timestamps
print(f"Train max: {train_df['created_at'].max()}")
print(f"Val min: {val_df['created_at'].min()}")
print(f"Val max: {val_df['created_at'].max()}")
print(f"Test min: {test_df['created_at'].min()}")
```

### Job Cloud Run échoue

**Solution** : Vérifier les logs

```bash
gcloud run jobs executions logs read <EXECUTION_NAME> \
  --region=europe-west1 \
  --project=sentinelle-485209
```

---

## 📚 Pour Aller Plus Loin

### Pipeline Complet

Le script `scripts/train.py` orchestre tout le pipeline :

```python
# 1. Préparation
train_df, val_df, test_df = prepare_training_data(...)

# 2. Feature Engineering
train_features = compute_features_parallel(train_df)
val_features = compute_features_parallel(val_df)

# 3. Entraînement
supervised_model = train_supervised_model(train_features, train_labels)
unsupervised_model = train_unsupervised_model(payon_legit_features)

# 4. Calibration
thresholds = calibrate_thresholds(val_features, val_labels)

# 5. Sauvegarde
save_artifacts(version="1.0.0", artifacts={...})
```

### Workflow Complet

```
1. Préparer les données (mapping PaySim)
   ↓
2. Split temporel (70/15/15)
   ↓
3. Calculer les features (parallèle)
   ↓
4. Entraîner LightGBM (supervisé)
   ↓
5. Entraîner IsolationForest (non supervisé)
   ↓
6. Calibrer les seuils
   ↓
7. Sauvegarder les artefacts (versioning)
   ↓
8. Upload vers Cloud Storage
```

---

## ✅ Checklist

- [ ] Données préparées (`paysim_mapped.csv`, `payon_legit_clean.csv`)
- [ ] Google Cloud SDK installé et authentifié
- [ ] Projet GCP configuré
- [ ] Déployer : `./scripts/deploy-training-job.sh`
- [ ] Lancer : `./scripts/run-training-cloud.sh`
- [ ] Suivre les logs
- [ ] Récupérer les artefacts depuis Cloud Storage

---

**Prêt à entraîner ?** Lancez `./scripts/deploy-training-job.sh` ! 🚀

