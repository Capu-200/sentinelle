"""
API FastAPI pour le ML Engine (scoring).

Endpoint principal : POST /score
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.features.pipeline import FeaturePipeline
from src.models.supervised.predictor import SupervisedPredictor
from src.models.unsupervised.predictor import UnsupervisedPredictor
from src.monitoring.gcs_logger import log_inference_to_gcs
from src.rules.engine import RulesEngine
from src.scoring.decision import DecisionEngine
from src.scoring.scorer import GlobalScorer

# Initialiser l'application
app = FastAPI(
    title="Payon ML Engine",
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


def _require_enriched_transaction(transaction: dict) -> None:
    """Exige le format enrichi : transaction.features.transactional et .historical."""
    if "features" not in transaction:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TRANSACTION_FORMAT_REQUIRED",
                "message": "Format enrichi obligatoire. La transaction doit contenir 'features.transactional' et 'features.historical'. Voir EXEMPLES_JSON_HISTORIQUE.md.",
            },
        )
    feats = transaction.get("features") or {}
    if "transactional" not in feats or "historical" not in feats:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TRANSACTION_FORMAT_REQUIRED",
                "message": "transaction.features doit contenir 'transactional' et 'historical' (même vides pour un nouveau compte).",
            },
        )


@app.post("/score", response_model=ScoreResponse)
async def score_transaction(request: ScoreRequest, background_tasks: BackgroundTasks):
    """
    Score une transaction.
    
    Format accepté : transaction enrichie uniquement.
    transaction doit contenir features.transactional et features.historical
    (pour un new user, historical peut être à 0 / -1.0 / 1).
    
    Returns:
        Score de risque, décision, et raisons
    """
    transaction = request.transaction
    context = request.context or {}
    
    _require_enriched_transaction(transaction)
    
    # 1. Feature Engineering (format enrichi uniquement)
    features = feature_pipeline.transform(transaction)
    
    # 2. Règles métier
    rules_output = rules_engine.evaluate(transaction, features, context)
    
    # Si BLOCK, arrêter ici (logging Vertex en arrière-plan)
    if rules_output.decision == "BLOCK":
        background_tasks.add_task(
            log_inference_to_gcs,
            features,
            float(rules_output.rule_score),
            "BLOCK",
            MODEL_VERSION,
        )
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

    # Logging Vertex (GCS) en arrière-plan
    background_tasks.add_task(
        log_inference_to_gcs,
        features,
        decision.risk_score,
        decision.decision,
        MODEL_VERSION,
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

