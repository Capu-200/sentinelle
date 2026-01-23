"""
API FastAPI pour le ML Engine (scoring).

Endpoint principal : POST /score
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.pipeline import FeaturePipeline
from src.models.supervised.predictor import SupervisedPredictor
from src.models.unsupervised.predictor import UnsupervisedPredictor
from src.rules.engine import RulesEngine
from src.scoring.decision import DecisionEngine
from src.scoring.scorer import GlobalScorer

# Initialiser l'application
app = FastAPI(
    title="Sentinelle ML Engine",
    description="Moteur de scoring ML pour la détection de fraude",
    version="1.0.0",
)

# Charger les modèles au démarrage
MODEL_VERSION = os.getenv("MODEL_VERSION", "latest")
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))

# Initialiser les composants
feature_pipeline = FeaturePipeline()
rules_engine = RulesEngine()
global_scorer = GlobalScorer()
decision_engine = DecisionEngine()

# Charger les modèles
try:
    supervised_predictor = SupervisedPredictor.load_version(MODEL_VERSION, ARTIFACTS_DIR)
    print(f"✅ Modèle supervisé chargé: {MODEL_VERSION}")
except Exception as e:
    print(f"⚠️  Modèle supervisé non disponible: {e}")
    supervised_predictor = None

try:
    unsupervised_predictor = UnsupervisedPredictor.load_version(MODEL_VERSION, ARTIFACTS_DIR)
    print(f"✅ Modèle non supervisé chargé: {MODEL_VERSION}")
except Exception as e:
    print(f"⚠️  Modèle non supervisé non disponible: {e}")
    unsupervised_predictor = None


class ScoreRequest(BaseModel):
    """Requête de scoring."""
    transaction: dict
    context: dict | None = None


class ScoreResponse(BaseModel):
    """Réponse de scoring."""
    risk_score: float
    decision: str
    reasons: list[str]
    model_version: str


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "model_version": MODEL_VERSION,
        "supervised_loaded": supervised_predictor is not None,
        "unsupervised_loaded": unsupervised_predictor is not None,
    }


@app.post("/score", response_model=ScoreResponse)
async def score_transaction(request: ScoreRequest):
    """
    Score une transaction.
    
    Args:
        request: Transaction enrichie avec features pré-calculées
    
    Returns:
        Score de risque, décision, et raisons
    """
    transaction = request.transaction
    context = request.context or {}
    
    # 1. Feature Engineering
    features = feature_pipeline.transform(transaction, historical_data=None)
    
    # 2. Règles métier
    rules_output = rules_engine.evaluate(transaction, features, context)
    
    # Si BLOCK, arrêter ici
    if rules_output.decision == "BLOCK":
        return ScoreResponse(
            risk_score=rules_output.rule_score,
            decision="BLOCK",
            reasons=rules_output.reasons,
            model_version=MODEL_VERSION,
        )
    
    # 3. Scoring ML
    if supervised_predictor:
        supervised_score = supervised_predictor.predict(features)
    else:
        supervised_score = 0.5  # Valeur par défaut
    
    if unsupervised_predictor:
        unsupervised_score = unsupervised_predictor.predict(features)
    else:
        unsupervised_score = 0.5  # Valeur par défaut
    
    # 4. Score global
    risk_score = global_scorer.compute_score(
        rule_score=rules_output.rule_score,
        supervised_score=supervised_score,
        unsupervised_score=unsupervised_score,
        boost_factor=rules_output.boost_factor,
    )
    
    # 5. Décision finale
    decision = decision_engine.decide(
        risk_score=risk_score,
        reasons=rules_output.reasons,
        hard_block=False,
        model_version=MODEL_VERSION,
    )
    
    return ScoreResponse(
        risk_score=decision.risk_score,
        decision=decision.decision,
        reasons=decision.reasons,
        model_version=MODEL_VERSION,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

