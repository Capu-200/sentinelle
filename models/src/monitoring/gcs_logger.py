"""
Logging des inferences vers GCS pour Vertex AI Model Monitoring.

Écrit une ligne JSONL par score dans gs://<bucket>/<prefix>/YYYY/MM/DD/<uuid>.jsonl.
Activé si MONITORING_GCS_BUCKET est défini.
"""

from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict


def _to_json_serializable(val: Any) -> Any:
    """Convertit des valeurs numpy/list en types JSON-serialisables."""
    if hasattr(val, "tolist"):
        return val.tolist()
    if isinstance(val, (list, tuple)):
        return [_to_json_serializable(v) for v in val]
    if isinstance(val, dict):
        return {k: _to_json_serializable(v) for k, v in val.items()}
    if isinstance(val, (int, float, str, bool)) or val is None:
        return val
    if hasattr(val, "item"):  # numpy scalar
        return val.item()
    return val


def log_inference_to_gcs(
    features: Dict[str, Any],
    risk_score: float,
    decision: str,
    model_version: str,
) -> None:
    """
    Écrit une ligne JSONL dans GCS pour Vertex Model Monitoring.

    Variables d'environnement :
    - MONITORING_GCS_BUCKET : bucket (ex. sentinelle-485209-ml-data). Si vide, no-op.
    - MONITORING_GCS_PREFIX : préfixe (défaut "monitoring/inference_logs").
    - MONITORING_SAMPLE_RATE : taux d'échantillonnage 0.0–1.0 (défaut 1.0).

    Args:
        features: Dictionnaire des features (mêmes clés que feature_schema.json).
        risk_score: Score de risque retourné.
        decision: Décision (APPROVE, REVIEW, BLOCK).
        model_version: Version du modèle.
    """
    bucket_name = (os.getenv("MONITORING_GCS_BUCKET") or "").strip()
    if not bucket_name:
        return

    try:
        sample_rate = float(os.getenv("MONITORING_SAMPLE_RATE", "1.0"))
    except (TypeError, ValueError):
        sample_rate = 1.0
    if sample_rate <= 0 or random.random() >= sample_rate:
        return

    prefix = (os.getenv("MONITORING_GCS_PREFIX") or "monitoring/inference_logs").strip().rstrip("/")
    now = datetime.now(timezone.utc)
    date_path = now.strftime("%Y/%m/%d")
    blob_name = f"{prefix}/{date_path}/{uuid.uuid4().hex}.jsonl"

    # Une ligne JSONL : request_time + features + risk_score + decision + model_version
    row: Dict[str, Any] = {
        "request_time": now.isoformat(),
        "risk_score": float(risk_score),
        "decision": str(decision),
        "model_version": str(model_version),
    }
    for k, v in features.items():
        row[k] = _to_json_serializable(v)

    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(row, default=str) + "\n",
            content_type="application/json",
        )
    except Exception as e:
        # Ne pas faire échouer la requête si le logging échoue
        import sys
        print(f"[monitoring] log_inference_to_gcs failed: {e}", file=sys.stderr)
