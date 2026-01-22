import os
import uvicorn
from fastapi import FastAPI
from . import database, models

# Créer tables (optionnel, Alembic recommandé pour prod)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Fraud Detection Backend")

@app.get("/")
def read_root():
    return {"message": "Backend FastAPI fonctionne !"}

# Endpoint test users
@app.get("/users")
def get_users(db=database.get_db()):
    return list(db.query(models.User).all())

# POINT CRUCIAL : utiliser le port injecté par Cloud Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Cloud Run injecte PORT
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)