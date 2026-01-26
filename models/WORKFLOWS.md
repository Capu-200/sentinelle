# 🔄 Workflows d'Entraînement

Deux workflows distincts pour entraîner les modèles ML selon vos besoins.

---

## 📊 Vue d'Ensemble

| Workflow | Entraînement | Upload | Avantages | Inconvénients |
|----------|--------------|--------|-----------|---------------|
| **Cloud** | Cloud Run Jobs | Automatique | Pas de setup local, scalable | Timeout limité, coûts |
| **Local** | Machine locale | Manuel | Pas de timeout, debug facile, gratuit | Setup requis, dépend de votre machine |

---

## ☁️ Workflow 1 : Entraînement sur Cloud Run Jobs

### Quand l'utiliser

- ✅ Pas de machine locale puissante
- ✅ Besoin de scalabilité
- ✅ Entraînement automatisé (CI/CD)
- ✅ Échantillonnage suffisant (500k transactions)

### Étapes

#### 1. Déployer le Training Job

```bash
cd models
./scripts/deploy-training-job.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"
```

**Ce que fait le script** :
- ✅ Crée le bucket Cloud Storage
- ✅ Upload les données vers GCS
- ✅ Déploie le job Cloud Run Jobs
- ✅ Configure : 8 CPU, 16GB RAM, 4h timeout

#### 2. Lancer l'Entraînement

```bash
./scripts/run-training-cloud.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"
```

**Temps estimé** : ~2-4h (avec échantillonnage 500k)

#### 3. Les Artefacts sont Automatiquement Uploadés

Les modèles sont automatiquement uploadés vers :
```
gs://sentinelle-485209-ml-data/artifacts/v1.0.0/
```

#### 4. Le ML Engine Charge Automatiquement

Au démarrage du ML Engine, les modèles sont téléchargés depuis GCS.

---

## 💻 Workflow 2 : Entraînement Local → Upload

### Quand l'utiliser

- ✅ Machine locale puissante (10+ cores, 32GB+ RAM)
- ✅ Besoin de dataset complet (6.3M transactions)
- ✅ Pas de contrainte de timeout
- ✅ Développement et expérimentation

### Étapes

#### 1. Entraînement Local

```bash
cd models
./scripts/train-local.sh "1.0.0"
```

**Ce que fait le script** :
- ✅ Utilise **tous les cores** disponibles (10 cores)
- ✅ **Dataset complet** (pas d'échantillonnage)
- ✅ Sauvegarde dans `artifacts/v1.0.0/`

**Temps estimé** : ~2-3h (avec 10 cores, dataset complet)

**Configuration** :
- Processus : 9 (sur 10 cores)
- RAM : Utilise toute la RAM disponible
- Dataset : Complet (6.3M PaySim + 300k Payon)

#### 2. Upload vers Cloud Storage

```bash
./scripts/upload-artifacts.sh "1.0.0"
```

**Ce que fait le script** :
- ✅ Upload `artifacts/v1.0.0/` vers `gs://sentinelle-485209-ml-data/artifacts/v1.0.0/`
- ✅ Crée le symlink `latest` si présent

**Temps** : ~1-2 minutes

#### 3. Le ML Engine Charge Automatiquement

Au prochain démarrage du ML Engine, les modèles sont téléchargés depuis GCS.

**Ou redéployer le ML Engine** :
```bash
./scripts/deploy-ml-engine.sh \
  "sentinelle-485209" \
  "sentinelle-ml-engine" \
  "europe-west1" \
  "1.0.0"
```

---

## 🔄 Comparaison des Workflows

### Workflow Cloud

**Avantages** :
- ✅ Pas de setup local
- ✅ Scalable (peut augmenter CPU/RAM)
- ✅ Automatisé (upload automatique)
- ✅ Pas de dépendance à votre machine

**Inconvénients** :
- ⚠️ Timeout limité (4h max)
- ⚠️ Coûts Cloud (~$0.60 par entraînement)
- ⚠️ Échantillonnage nécessaire (500k au lieu de 6.3M)

**Recommandé pour** : Production, CI/CD, équipes sans machines puissantes

---

### Workflow Local

**Avantages** :
- ✅ Pas de timeout
- ✅ Dataset complet possible
- ✅ Debug facile
- ✅ Gratuit (pas de coûts Cloud)
- ✅ Contrôle total

**Inconvénients** :
- ⚠️ Nécessite une machine puissante
- ⚠️ Upload manuel requis
- ⚠️ Dépend de votre machine

**Recommandé pour** : Développement, expérimentation, dataset complet

---

## 🎯 Recommandation

**Pour votre cas** (10 cores, 32GB RAM, développement) :

👉 **Workflow Local recommandé**

**Raisons** :
1. Machine suffisamment puissante
2. Dataset complet possible (~2-3h)
3. Pas de timeout
4. Debug plus facile
5. Gratuit

**Workflow suggéré** :
```
1. Entraînement local (2-3h)
   ↓
2. Test local des modèles
   ↓
3. Upload vers Cloud Storage (1-2 min)
   ↓
4. ML Engine charge automatiquement
```

---

## 📋 Checklist Workflow Local

- [ ] Données préparées (`Data/processed/*.csv`)
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Entraînement local : `./scripts/train-local.sh 1.0.0`
- [ ] Vérifier les artefacts : `ls artifacts/v1.0.0/`
- [ ] Upload vers GCS : `./scripts/upload-artifacts.sh 1.0.0`
- [ ] Vérifier sur GCS : `gsutil ls gs://sentinelle-485209-ml-data/artifacts/v1.0.0/`
- [ ] Redéployer ML Engine (optionnel) : `./scripts/deploy-ml-engine.sh ...`

---

## 📋 Checklist Workflow Cloud

- [ ] Données préparées (`Data/processed/*.csv`)
- [ ] Déployer le job : `./scripts/deploy-training-job.sh ...`
- [ ] Lancer l'entraînement : `./scripts/run-training-cloud.sh ...`
- [ ] Suivre les logs
- [ ] Vérifier les artefacts sur GCS : `gsutil ls gs://sentinelle-485209-ml-data/artifacts/v1.0.0/`
- [ ] ML Engine charge automatiquement au démarrage

---

## 🔧 Détails Techniques

### Mode Local vs Cloud

Le script `train.py` détecte automatiquement le mode :

**Mode Local** (`--local`) :
- Utilise tous les cores (n_cores - 1)
- Dataset complet (pas d'échantillonnage)
- Optimisé pour machines puissantes

**Mode Cloud** (par défaut) :
- Limite à 5 processus (évite OOM)
- Échantillonnage à 500k transactions
- Optimisé pour Cloud Run Jobs

### Chargement des Modèles dans ML Engine

Le ML Engine télécharge automatiquement les modèles depuis GCS au démarrage si :
- `BUCKET_NAME` est défini
- `MODEL_VERSION` est défini
- Les modèles ne sont pas déjà présents localement

**Script** : `scripts/download-artifacts.sh` (appelé dans `Dockerfile.api`)

---

## 🚀 Quick Start

### Workflow Local (Recommandé)

```bash
# 1. Entraînement
cd models
./scripts/train-local.sh 1.0.0

# 2. Upload
./scripts/upload-artifacts.sh 1.0.0

# 3. ML Engine charge automatiquement au prochain démarrage
```

### Workflow Cloud

```bash
# 1. Déployer
cd models
./scripts/deploy-training-job.sh ... 

# 2. Lancer
./scripts/run-training-cloud.sh ...

# 3. ML Engine charge automatiquement
```

---

**Questions ?** Consultez [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md) pour plus de détails.

