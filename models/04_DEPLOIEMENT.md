# ☁️ Déploiement sur Google Cloud

Guide complet pour déployer le ML Engine et les jobs d'entraînement sur Google Cloud Run.

---

## 📋 Vue d'Ensemble

**2 services** à déployer :

1. **ML Engine** (Cloud Run Service) : Scoring en temps réel
2. **Training Job** (Cloud Run Jobs) : Entraînement périodique

---

## 🚀 Quick Start

### Déployer le ML Engine

```bash
cd models
./scripts/deploy-ml-engine.sh \
  "sentinelle-485209" \
  "sentinelle-ml-engine" \
  "europe-west1" \
  "1.0.0"
```

### Déployer le Training Job

```bash
cd models
./scripts/deploy-training-job.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"
```

---

## 🎯 Partie 1 : Déploiement du ML Engine

### Objectif

Déployer le service de scoring ML sur Cloud Run pour qu'il soit accessible via HTTP.

### Prérequis

1. **Modèles entraînés** : Les artefacts doivent exister dans Cloud Storage
2. **Google Cloud SDK** : Installé et authentifié
3. **Projet GCP** : `sentinelle-485209` configuré

### Déploiement Automatique

**Script** : `scripts/deploy-ml-engine.sh`

```bash
./scripts/deploy-ml-engine.sh \
  "sentinelle-485209" \
  "sentinelle-ml-engine" \
  "europe-west1" \
  "1.0.0"
```

**Ce que fait le script** :
1. ✅ Active les APIs nécessaires
2. ✅ Vérifie que les artefacts existent
3. ✅ Construit l'image Docker
4. ✅ Déploie sur Cloud Run
5. ✅ Configure les variables d'environnement

**Temps** : ~5-10 minutes (première fois)

### Configuration

**Variables d'environnement** :
- `MODEL_VERSION` : Version du modèle (ex: "1.0.0" ou "latest")
- `ARTIFACTS_DIR` : Dossier des artefacts (défaut: "/app/artifacts")

**Ressources** :
- **CPU** : 2 vCPU (configurable)
- **RAM** : 2 GB (configurable)
- **Timeout** : 300 secondes (5 minutes)
- **Max instances** : 10 (auto-scaling)

### Vérification

**Health check** :
```bash
curl https://sentinelle-ml-engine-xxx.run.app/health
```

**Réponse attendue** :
```json
{
  "status": "healthy",
  "model_version": "v1.0.0",
  "supervised_loaded": true,
  "unsupervised_loaded": true
}
```

### Mise à Jour

**Pour mettre à jour les modèles** :

1. Entraîner une nouvelle version (voir [01_ENTRAINEMENT.md](01_ENTRAINEMENT.md))
2. Redéployer avec la nouvelle version :
```bash
./scripts/deploy-ml-engine.sh \
  "sentinelle-485209" \
  "sentinelle-ml-engine" \
  "europe-west1" \
  "1.1.0"  # Nouvelle version
```

---

## 🎓 Partie 2 : Déploiement du Training Job

### Objectif

Déployer le job d'entraînement sur Cloud Run Jobs pour entraîner les modèles périodiquement.

### Prérequis

1. **Données préparées** : `Data/processed/*.csv` doivent exister
2. **Google Cloud SDK** : Installé et authentifié
3. **Projet GCP** : `sentinelle-485209` configuré

### Déploiement Automatique

**Script** : `scripts/deploy-training-job.sh`

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

### Configuration

**Variables d'environnement** :
- `DATA_DIR` : Dossier des données (défaut: "/app/data")
- `ARTIFACTS_DIR` : Dossier des artefacts (défaut: "/app/artifacts")
- `BUCKET_NAME` : Nom du bucket Cloud Storage
- `VERSION` : Version du modèle (ex: "1.0.0")

**Ressources** :
- **CPU** : 8 vCPU (configurable)
- **RAM** : 8 GB (configurable)
- **Timeout** : 7200 secondes (2 heures max)
- **Max retries** : 1

### Lancer l'Entraînement

**Script** : `scripts/run-training-cloud.sh`

```bash
./scripts/run-training-cloud.sh \
  "sentinelle-485209" \
  "sentinelle-training" \
  "europe-west1" \
  "1.0.0"
```

**Ou manuellement** :
```bash
gcloud run jobs execute sentinelle-training \
  --region=europe-west1 \
  --project=sentinelle-485209
```

**Temps d'exécution** : ~30-45 minutes

### Suivre les Logs

**En temps réel** :
```bash
# Obtenir le nom de l'exécution
EXECUTION=$(gcloud run jobs executions list \
  --job=sentinelle-training \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --limit=1 \
  --format="value(metadata.name)")

# Suivre les logs
gcloud run jobs executions logs tail $EXECUTION \
  --region=europe-west1 \
  --project=sentinelle-485209
```

**Après la fin** :
```bash
gcloud run jobs executions logs read $EXECUTION \
  --region=europe-west1 \
  --project=sentinelle-485209
```

### Récupérer les Artefacts

**Les modèles sont automatiquement uploadés vers Cloud Storage** :

```bash
# Lister les artefacts
gsutil ls -r gs://sentinelle-485209-ml-data/artifacts/

# Télécharger les artefacts
gsutil -m cp -r gs://sentinelle-485209-ml-data/artifacts/v1.0.0/ ./artifacts/
```

---

## ⚙️ Configuration Avancée

### Modifier les Ressources

#### ML Engine

```bash
gcloud run services update sentinelle-ml-engine \
  --region=europe-west1 \
  --cpu=4 \
  --memory=4Gi \
  --project=sentinelle-485209
```

#### Training Job

```bash
gcloud run jobs update sentinelle-training \
  --region=europe-west1 \
  --cpu=16 \
  --memory=16Gi \
  --project=sentinelle-485209
```

**Plus de CPU = Plus rapide mais plus cher**

### Variables d'Environnement

#### ML Engine

```bash
gcloud run services update sentinelle-ml-engine \
  --region=europe-west1 \
  --set-env-vars="MODEL_VERSION=1.1.0,ARTIFACTS_DIR=/app/artifacts" \
  --project=sentinelle-485209
```

#### Training Job

```bash
gcloud run jobs update sentinelle-training \
  --region=europe-west1 \
  --set-env-vars="VERSION=1.1.0,BUCKET_NAME=sentinelle-485209-ml-data" \
  --project=sentinelle-485209
```

---

## 💰 Coûts Estimés

### ML Engine (Scoring)

**Par requête** :
- **CPU** : 2 vCPU × 0.2s × $0.00002400 = **$0.0000096**
- **RAM** : 2 GB × 0.2s × $0.00000250 = **$0.000001**
- **Total** : **~$0.00001 par requête**

**Pour 1M requêtes** : **~$10**

### Training Job

**Par entraînement** :
- **CPU** : 8 vCPU × 2700s × $0.00002400 = **$0.52**
- **RAM** : 8 GB × 2700s × $0.00000250 = **$0.05**
- **Storage** : Négligeable
- **Total** : **~$0.60 par entraînement**

**Pour 10 entraînements** : **~$6**

---

## 🔐 Sécurité

### Authentification

**Par défaut** : Service public (accessible sans authentification)

**Pour sécuriser** :
```bash
gcloud run services update sentinelle-ml-engine \
  --region=europe-west1 \
  --no-allow-unauthenticated \
  --project=sentinelle-485209
```

**Puis utiliser un token** :
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" \
  https://sentinelle-ml-engine-xxx.run.app/score
```

### Secrets

**Pour les mots de passe** : Utiliser Secret Manager

```bash
# Créer le secret
echo -n "VOTRE_MOT_DE_PASSE" | gcloud secrets create db-password \
  --data-file=- \
  --project=sentinelle-485209

# Utiliser dans Cloud Run
gcloud run services update sentinelle-ml-engine \
  --set-secrets="DB_PASSWORD=db-password:latest" \
  --region=europe-west1 \
  --project=sentinelle-485209
```

---

## 🔄 Workflow Complet

### 1. Entraîner un Nouveau Modèle

```bash
# Déployer le job (si pas déjà fait)
./scripts/deploy-training-job.sh ...

# Lancer l'entraînement
./scripts/run-training-cloud.sh ...

# Suivre les logs
gcloud run jobs executions logs tail ...

# Récupérer les artefacts
gsutil -m cp -r gs://sentinelle-485209-ml-data/artifacts/v1.1.0/ ./artifacts/
```

### 2. Déployer le ML Engine avec la Nouvelle Version

```bash
# Déployer avec la nouvelle version
./scripts/deploy-ml-engine.sh \
  "sentinelle-485209" \
  "sentinelle-ml-engine" \
  "europe-west1" \
  "1.1.0"  # Nouvelle version
```

### 3. Tester

```bash
# Health check
curl https://sentinelle-ml-engine-xxx.run.app/health

# Test de scoring
curl -X POST https://sentinelle-ml-engine-xxx.run.app/score \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## 🐛 Dépannage

### Erreur : "Service not found"

**Solution** : Vérifier que le service est bien déployé

```bash
gcloud run services list \
  --region=europe-west1 \
  --project=sentinelle-485209
```

### Erreur : "Modèle non disponible"

**Solution** : Vérifier que les artefacts sont bien uploadés

```bash
gsutil ls gs://sentinelle-485209-ml-data/artifacts/v1.0.0/
```

### Erreur : "Permission denied"

**Solution** : Vérifier les permissions

```bash
gcloud projects get-iam-policy sentinelle-485209
```

### Job échoue

**Solution** : Vérifier les logs

```bash
gcloud run jobs executions logs read <EXECUTION_NAME> \
  --region=europe-west1 \
  --project=sentinelle-485209
```

---

## 📊 Monitoring

### Logs Cloud Run

**ML Engine** :
```bash
gcloud run services logs read sentinelle-ml-engine \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --limit=100
```

**Training Job** :
```bash
gcloud run jobs executions logs read <EXECUTION_NAME> \
  --region=europe-west1 \
  --project=sentinelle-485209
```

### Métriques

**Dans Google Cloud Console** :
- Requêtes par seconde
- Latence (p50, p95, p99)
- Taux d'erreur
- Utilisation CPU/RAM

---

## ✅ Checklist

### ML Engine

- [ ] Modèles entraînés et uploadés vers Cloud Storage
- [ ] Script de déploiement exécuté
- [ ] Health check OK
- [ ] Test de scoring réussi
- [ ] Variables d'environnement configurées

### Training Job

- [ ] Données préparées (`Data/processed/*.csv`)
- [ ] Script de déploiement exécuté
- [ ] Bucket Cloud Storage créé
- [ ] Données uploadées
- [ ] Test d'exécution réussi

---

## 🎯 Prochaines Étapes

Après le déploiement :

1. ✅ Intégrer le ML Engine dans le Backend API
2. ✅ Configurer `ML_ENGINE_URL` dans le backend
3. ✅ Tester le flux complet (Backend → ML Engine → DB)
4. ✅ Monitorer les performances

---

**Prêt à déployer ?** Lancez les scripts de déploiement ! 🚀

