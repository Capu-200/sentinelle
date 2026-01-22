# Partie Backend 

Ce repository contient le backend de l’application de détection de fraude bancaire.  
Il est construit avec **Python**, **FastAPI**, **SQLModel / SQLAlchemy**, **Alembic** et se connecte à une **base PostgreSQL** via Docker.  

Actuellement le backend gère :  
- La gestion des utilisateurs (`auth.users`)  
- Les comptes bancaires et transactions (`banking.accounts`, `banking.transactions`)  
- Les prédictions de fraude (`fraud.predictions`)  
- Les logs d’audit (`audit.logs`)  
- La gestion des modèles ML (`ml.models`)

---

## **Technologies**

- Python 3.11  
- FastAPI  
- SQLModel / SQLAlchemy  
- PostgreSQL (via Docker)  
- Alembic (pour les migrations)  
- Docker & Docker Compose  

---

## **Structure du projet**

```
project-root/
├── backend/
│   ├── app/                 # Code FastAPI
│   ├── alembic/             # Dossier Alembic
│   │   ├── env.py
│   │   └── versions/        # Migrations
│   └── Dockerfile
├── docker-compose.yml       # Orchestration Docker
└── README.md
```

---

## **Prérequis**

- Docker & Docker Compose
- Python 3.11
- pip ou poetry
- Optionnel : un environnement virtuel Python

---

## **Installation et lancement**

### 1️⃣ Cloner le repository

```bash
git clone <url_du_repo>
cd project-root
```

### 2️⃣ Créer un environnement Python (optionnel mais recommandé)

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

### 3️⃣ Installer les dépendances

```bash
pip install -r backend/requirements.txt
```
### 4️⃣ Lancer PostgreSQL via Docker

```bash
docker-compose up -d postgres
```

Il faut ensuite vérifier que PostgreSQL tourne :
```bash
docker ps
```

### 5️⃣ Configurer Alembic

Dans backend/alembic.ini, vérifier l’URL de connexion à la DB :
```ini
sqlalchemy.url = postgresql+psycopg2://fraud_user:fraud_pwd@localhost:5432/fraud_db
```
⚠️ Si Alembic / backend tourne dans Docker, il faut remplacer localhost par le nom du service Docker : postgres

### 6️⃣ Appliquer les migrations

```bash
python -m alembic upgrade head
```
Cela va créer tous les schémas et tables nécessaires.

### 7️⃣ Test rapide de la DB

Depuis PostgreSQL :

```bash
docker exec -it <postgres_container_name> psql -U fraud_user -d fraud_db

\dt auth.*          -- vérifier les tables users

SELECT * FROM auth.users;
```

### Bonnes pratiques

- Toujours activer ton environnement virtuel Python avant de travailler.
- Appliquer Alembic après chaque changement de table / schéma.
- Vérifier PostgreSQL est bien lancé avant de lancer le backend.
- Pour un déploiement sur Docker (Cloud Run), adapter DATABASE_URL avec les variables d’environnement.
