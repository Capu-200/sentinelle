# Scripts de Déploiement

Ce dossier contient les scripts pour déployer l'application sur Google Cloud.

## Scripts disponibles

### 1. `deploy-cloud-sql.sh`
Crée l'instance Cloud SQL PostgreSQL.

**Usage:**
```bash
./scripts/deploy-cloud-sql.sh [PROJECT_ID] [INSTANCE_NAME] [DATABASE_NAME] [USER_NAME] [PASSWORD]
```

**Exemple:**
```bash
./scripts/deploy-cloud-sql.sh \
  "my-project-id" \
  "sentinelle-db" \
  "fraud_db" \
  "fraud_user" \
  "MonMotDePasse123!"
```

### 2. `setup-secrets.sh`
Configure les secrets dans Google Cloud Secret Manager.

**Usage:**
```bash
./scripts/setup-secrets.sh [PROJECT_ID] [DB_PASSWORD] [DB_NAME]
```

**Exemple:**
```bash
./scripts/setup-secrets.sh \
  "my-project-id" \
  "MonMotDePasse123!" \
  "fraud_db"
```

### 3. `run-migrations.sh`
Exécute les migrations Alembic sur Cloud SQL via Cloud SQL Auth Proxy.

**Usage:**
```bash
./scripts/run-migrations.sh [PROJECT_ID] [INSTANCE_NAME] [DATABASE_NAME] [USER_NAME] [PASSWORD]
```

**Exemple:**
```bash
./scripts/run-migrations.sh \
  "my-project-id" \
  "sentinelle-db" \
  "fraud_db" \
  "fraud_user" \
  "MonMotDePasse123!"
```

### 4. `deploy-cloud-run.sh`
Déploie le backend FastAPI sur Cloud Run.

**Usage:**
```bash
./scripts/deploy-cloud-run.sh [PROJECT_ID] [SERVICE_NAME] [REGION] [CLOUD_SQL_INSTANCE]
```

**Exemple:**
```bash
./scripts/deploy-cloud-run.sh \
  "my-project-id" \
  "sentinelle-api" \
  "europe-west1" \
  "sentinelle-db"
```

## Ordre d'exécution recommandé

1. `deploy-cloud-sql.sh` - Créer l'instance Cloud SQL
2. `setup-secrets.sh` - Configurer les secrets
3. `run-migrations.sh` - Exécuter les migrations
4. `deploy-cloud-run.sh` - Déployer le backend

## Prérequis

- Google Cloud SDK installé et configuré
- Permissions sur le projet Google Cloud
- Cloud SQL Auth Proxy installé (pour `run-migrations.sh`)

