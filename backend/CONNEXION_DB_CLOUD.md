# 🔌 Connexion à la Base de Données Google Cloud SQL

## ✅ Configuration Actuelle

Le backend est déjà configuré pour se connecter à Cloud SQL. La connexion se fait via la variable d'environnement `DATABASE_URL`.

---

## 🚀 Sur Cloud Run (Production)

### Format de connexion

**Unix Socket** (recommandé pour Cloud Run) :
```
postgresql+psycopg2://USER:PASSWORD@/DATABASE?host=/cloudsql/CONNECTION_NAME
```

**Exemple** :
```
postgresql+psycopg2://fraud_user:VOTRE_MOT_DE_PASSE@/fraud_db?host=/cloudsql/sentinelle-485209:europe-west1:sentinelle-db
```

### Déploiement avec script

Le script `scripts/deploy-cloud-run.sh` configure automatiquement :

```bash
./scripts/deploy-cloud-run.sh \
  "sentinelle-485209" \
  "sentinelle-api" \
  "europe-west1" \
  "sentinelle-db"
```

**Ce que fait le script** :
1. ✅ Récupère le Connection Name automatiquement
2. ✅ Configure `--add-cloudsql-instances` (permission Cloud SQL)
3. ✅ Configure `DATABASE_URL` avec Unix socket
4. ✅ Déploie sur Cloud Run

---

## 💻 En Local (Développement)

### Option 1 : Cloud SQL Auth Proxy (Recommandé)

**1. Installer Cloud SQL Auth Proxy** (une seule fois)

```bash
# macOS (Apple Silicon)
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.arm64
chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/
```

**2. Démarrer le proxy** (dans un terminal séparé)

```bash
# Obtenir le Connection Name
CONNECTION_NAME=$(gcloud sql instances describe sentinelle-db \
  --project=sentinelle-485209 \
  --format="value(connectionName)")

# Démarrer le proxy
cloud-sql-proxy "$CONNECTION_NAME" --port=5432
```

**3. Configurer DATABASE_URL**

```bash
# Dans backend/.env ou export
export DATABASE_URL="postgresql+psycopg2://fraud_user:VOTRE_MOT_DE_PASSE@127.0.0.1:5432/fraud_db"
```

**4. Démarrer le backend**

```bash
cd backend
uvicorn app.main:app --reload
```

---

## 📋 Informations Nécessaires

Pour se connecter, vous avez besoin de :

1. **Connection Name** : `sentinelle-485209:europe-west1:sentinelle-db`
   ```bash
   gcloud sql instances describe sentinelle-db \
     --project=sentinelle-485209 \
     --format="value(connectionName)"
   ```

2. **Base de données** : `fraud_db`

3. **Utilisateur** : `fraud_user`

4. **Mot de passe** : À obtenir du chef de projet (partagé de manière sécurisée)

---

## 🔧 Configuration dans le Code

Le fichier `backend/app/database.py` gère automatiquement :

```python
# Récupère DATABASE_URL depuis l'environnement
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://fraud_user:fraud_pwd@localhost:5432/fraud_db"  # Default local
)

# Crée l'engine SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Important pour Cloud Run (serverless)
    echo=False
)
```

**Pas besoin de modifier le code** - tout se fait via `DATABASE_URL` ! ✅

---

## 🧪 Test de Connexion

### Test local

```bash
# 1. Démarrer le proxy
cloud-sql-proxy "sentinelle-485209:europe-west1:sentinelle-db" --port=5432

# 2. Dans un autre terminal
export DATABASE_URL="postgresql+psycopg2://fraud_user:VOTRE_MOT_DE_PASSE@127.0.0.1:5432/fraud_db"

# 3. Tester avec Python
python -c "
from app.database import engine
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('✅ Connexion réussie!')
"
```

### Test sur Cloud Run

```bash
# Vérifier les logs
gcloud run services logs read sentinelle-api \
  --region=europe-west1 \
  --project=sentinelle-485209 \
  --limit=50
```

---

## 🔐 Sécurité

### Option 1 : Variable d'environnement (actuel)

✅ Simple
⚠️ Mot de passe visible dans les variables d'environnement

### Option 2 : Secret Manager (recommandé pour production)

```bash
# Créer le secret
echo -n "VOTRE_MOT_DE_PASSE" | gcloud secrets create db-password \
  --data-file=- \
  --project=sentinelle-485209

# Utiliser dans Cloud Run
gcloud run deploy sentinelle-api \
  --set-secrets="DB_PASSWORD=db-password:latest" \
  --set-env-vars="DATABASE_URL=postgresql+psycopg2://fraud_user:${DB_PASSWORD}@/fraud_db?host=/cloudsql/..."
```

---

## ✅ Checklist

- [x] Code backend configuré (`database.py`)
- [x] Script de déploiement Cloud Run (`deploy-cloud-run.sh`)
- [x] Documentation dans README.md
- [ ] Obtenir le mot de passe DB du chef de projet
- [ ] Tester la connexion locale avec Cloud SQL Auth Proxy
- [ ] Déployer le backend sur Cloud Run
- [ ] Tester la connexion sur Cloud Run

---

## 🚨 Dépannage

### Erreur : "Connection refused"

**Cause** : Le proxy n'est pas démarré ou le port est incorrect.

**Solution** :
```bash
# Vérifier que le proxy tourne
ps aux | grep cloud-sql-proxy

# Redémarrer le proxy
cloud-sql-proxy "CONNECTION_NAME" --port=5432
```

### Erreur : "Authentication failed"

**Cause** : Mot de passe incorrect ou utilisateur inexistant.

**Solution** : Vérifier les credentials avec le chef de projet.

### Erreur : "Instance connection name not found"

**Cause** : Connection Name incorrect.

**Solution** :
```bash
# Vérifier le Connection Name
gcloud sql instances describe sentinelle-db \
  --project=sentinelle-485209 \
  --format="value(connectionName)"
```

---

**Tout est prêt ! Il suffit de configurer `DATABASE_URL` et ça fonctionne.** ✅

