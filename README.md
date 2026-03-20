# 🛡️ Payon - Détection de Fraude Bancaire

Application de détection de fraude bancaire avec backend FastAPI et base de données PostgreSQL hébergée sur Google Cloud SQL.

---

## 🚀 Démarrage Rapide

### Prérequis

- **Google Cloud SDK** installé et configuré
- **Accès au projet Google Cloud** `sentinelle-485209`
- **Cloud SQL Auth Proxy** installé (pour se connecter localement)

### Installation Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# Se connecter
gcloud auth login
gcloud auth application-default login
```

---

## 🔌 Se Connecter à la Base de Données Cloud SQL

### ⚡ Méthode Rapide (Recommandée)

**1. Installer Cloud SQL Auth Proxy** (une seule fois)

```bash
# macOS (Apple Silicon)
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.arm64
chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/

# macOS (Intel)
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/

# Linux
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/
```

**2. Démarrer le proxy** (dans un terminal séparé)

```bash
# Connection Name à obtenir depuis le chef de projet ou Google Cloud Console
cloud-sql-proxy "PROJECT_ID:REGION:INSTANCE_NAME" --port=5432
```

**3. Se connecter à la base de données**

```bash
# Avec psql
psql -h 127.0.0.1 -U fraud_user -d fraud_db

# Ou avec votre application
export DATABASE_URL="postgresql+psycopg2://fraud_user:VOTRE_MOT_DE_PASSE@127.0.0.1:5432/fraud_db"
```

### 📋 Informations de Connexion

**Pour obtenir ces informations, contactez le chef de projet :**

- **Connection Name** : Format `PROJECT_ID:REGION:INSTANCE_NAME`
  - Exemple : `sentinelle-485209:europe-west1:sentinelle-db`
- **Base de données** : `fraud_db`
- **Utilisateur** : `fraud_user`
- **Mot de passe** : À demander au chef de projet (partagé de manière sécurisée)
- **Port local** : `5432` (via Cloud SQL Auth Proxy)

### 🔍 Obtenir le Connection Name

Si vous avez accès au projet Google Cloud :

```bash
export PROJECT_ID="sentinelle-485209"
gcloud config set project $PROJECT_ID

# Obtenir le Connection Name
gcloud sql instances describe sentinelle-db \
  --format="value(connectionName)"
```

---

## 💻 Développement Local

### Configuration

**1. Créer un fichier `.env` dans `backend/`** (copier depuis `backend/env.example`)

```env
DATABASE_URL=postgresql+psycopg2://fraud_user:VOTRE_MOT_DE_PASSE@127.0.0.1:5432/fraud_db
```

**⚠️ Important** : Ne jamais commiter le fichier `.env` (déjà dans `.gitignore`)

**2. Démarrer Cloud SQL Auth Proxy** (Terminal 1)

```bash
cloud-sql-proxy "CONNECTION_NAME" --port=5432
```

**3. Lancer le backend** (Terminal 2)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload
```

L'API sera accessible sur `http://localhost:8000`

---

## 📊 Structure de la Base de Données

### Tables principales

- **users** : Utilisateurs du système
- **wallets** : Portefeuilles des utilisateurs
- **transactions** : Transactions bancaires
- **wallet_ledger** : Journal des mouvements de portefeuille
- **ai_decisions** : Décisions de l'IA (scores de fraude)
- **human_reviews** : Revues manuelles des transactions

### Exécuter les migrations

Si la base de données n'a pas encore été initialisée :

```bash
export PROJECT_ID="sentinelle-485209"
./scripts/run-migrations.sh \
  "$PROJECT_ID" \
  "sentinelle-db" \
  "fraud_db" \
  "fraud_user" \
  "VOTRE_MOT_DE_PASSE"
```

---

## 🚀 Déploiement (Chef de Projet)

### Créer l'instance Cloud SQL

```bash
export PROJECT_ID="sentinelle-485209"
./scripts/deploy-cloud-sql.sh \
  "$PROJECT_ID" \
  "sentinelle-db" \
  "fraud_db" \
  "fraud_user" \
  'VOTRE_MOT_DE_PASSE'
```

### Déployer le backend sur Cloud Run

```bash
./scripts/deploy-cloud-run.sh \
  "$PROJECT_ID" \
  "sentinelle-api" \
  "europe-west1" \
  "sentinelle-db"
```

---

## 🛠️ Technologies

- **Backend** : Python 3.11, FastAPI
- **Base de données** : PostgreSQL 15 (Google Cloud SQL)
- **ORM** : SQLModel / SQLAlchemy
- **Migrations** : Alembic
- **Déploiement** : Google Cloud Run (serverless)
- **Base de données** : Google Cloud SQL

---

## 📁 Structure du Projet

```
sentinelle/
├── backend/              # Backend FastAPI
│   ├── app/             # Code de l'application
│   ├── alembic/         # Migrations de base de données
│   └── requirements.txt  # Dépendances Python
├── front/                # Frontend Next.js
├── models/               # Modèles ML
├── scripts/              # Scripts de déploiement
│   ├── deploy-cloud-sql.sh
│   ├── deploy-cloud-run.sh
│   └── run-migrations.sh
└── README.md
```

---

## 🔐 Sécurité

### Accès à la base de données

**⚠️ Important** : Les personnes qui clonent le repo n'ont **PAS automatiquement** accès à la base Cloud SQL.

Pour obtenir l'accès :
1. Avoir un compte Google Cloud avec accès au projet `sentinelle-485209`
2. Installer Cloud SQL Auth Proxy
3. Obtenir le Connection Name et le mot de passe (via le chef de projet)

### Bonnes pratiques

- ✅ Ne jamais commiter les mots de passe
- ✅ Utiliser Cloud SQL Auth Proxy pour les connexions locales
- ✅ Partager les credentials via un canal sécurisé (pas dans Git)
- ✅ Utiliser des variables d'environnement pour les configurations

---

## 🐛 Dépannage

### Erreur : "cloud-sql-proxy: command not found"

Installez Cloud SQL Auth Proxy (voir section "Se Connecter à la Base de Données")

### Erreur : "Permission denied" lors de la connexion

1. Vérifier que Cloud SQL Auth Proxy est en cours d'exécution
2. Vérifier le mot de passe
3. Vérifier que vous avez accès au projet Google Cloud

### Erreur : "Instance does not exist"

Vérifier le Connection Name :
```bash
gcloud sql instances list
```

### Le proxy ne démarre pas

Vérifier que vous êtes connecté à Google Cloud :
```bash
gcloud auth list
gcloud auth application-default login
```

---

## 📚 Ressources

- [Documentation Cloud SQL](https://cloud.google.com/sql/docs/postgres)
- [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Alembic](https://alembic.sqlalchemy.org/)

---

## 👥 Équipe

Pour toute question ou problème d'accès, contacter le chef de projet.

---

**🎉 Bon développement !**
