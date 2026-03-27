#!/usr/bin/env python3
"""
Driver automatisant le "run Vertex AI Model Monitoring" apres un nouveau deploiement.

Ce script automatise :
1) Upload de baseline (baseline_train.jsonl -> gs://.../monitoring/baseline/v<V>/train_features.jsonl) si absent
2) Reutilisation ou creation d'un ModelMonitor (schema + baseline "Training")
3) Lancement d'un ModelMonitoringJob (Run now) target sur une table BigQuery, window par defaut 24h

Usage minimal :
  python3 scripts/run-vertex-monitoring-after-deploy.py \
    --version 2.0.1-mlflow \
    --target-bq-table-uri bq://sentinelle-485209.ml_monitoring.inference_logs_last_24h \
    --project sentinelle-485209 \
    --region europe-west1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.cloud import storage


def _normalize_version(version: str) -> str:
    version = version.strip()
    return version[1:] if version.startswith("v") else version


def _to_epoch_seconds(timestamp: object) -> float:
    if timestamp is None:
        return 0.0
    dt = getattr(timestamp, "timestamp", None)
    if callable(dt):
        return float(dt())
    seconds = getattr(timestamp, "seconds", None)
    nanos = getattr(timestamp, "nanos", None)
    if seconds is not None:
        return float(seconds) + float(nanos or 0) / 1_000_000_000
    return 0.0


def _pick_latest_by_create_time(resources: list[object]) -> object | None:
    if not resources:
        return None
    return max(resources, key=lambda item: _to_epoch_seconds(getattr(item, "create_time", None)))


def _ensure_baseline_uploaded(*, local_baseline_path: Path, bucket_name: str, baseline_gcs_uri: str) -> None:
    """
    baseline_gcs_uri attend un format gs://bucket/path
    """
    if not baseline_gcs_uri.startswith("gs://"):
        raise ValueError(f"baseline_gcs_uri doit commencer par gs:// : {baseline_gcs_uri}")

    # gs://sentinelle-.../monitoring/baseline/v<V>/train_features.jsonl
    _, _, remainder = baseline_gcs_uri.partition("gs://")
    parts = remainder.split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"baseline_gcs_uri invalide : {baseline_gcs_uri}")
    gcs_bucket, blob_path = parts[0], parts[1]

    if gcs_bucket != bucket_name:
        print(
            f"⚠️ Bucket incoherent : baseline_gcs_uri contient {gcs_bucket} "
            f"mais --bucket vaut {bucket_name}. On suit l'URI.",
            file=sys.stderr,
        )

    client = storage.Client()
    bucket = client.bucket(gcs_bucket)
    blob = bucket.blob(blob_path)

    if blob.exists():
        print(f"✅ Baseline deja presente : {baseline_gcs_uri}")
        return

    if not local_baseline_path.exists():
        raise FileNotFoundError(
            f"Baseline absente dans GCS ({baseline_gcs_uri}) et baseline locale introuvable : {local_baseline_path}"
        )

    print(f"📤 Upload baseline vers : {baseline_gcs_uri}")
    blob.upload_from_filename(str(local_baseline_path), content_type="application/json")
    print("✅ Upload baseline termine.")


def _vertex_type(feature_name: str) -> str:
    n = feature_name.lower()
    if any(x in n for x in ("amount", "sum_", "mean_", "max_", "ratio", "concentration", "entropy", "log_")):
        return "float"
    if any(x in n for x in ("count", "hour_", "day_of_", "destinations_", "days_since", "tx_count")):
        return "integer"
    return "categorical"


def _build_monitoring_schema(feature_names: list[str]):
    # Imports locaux car l'environnement peut ne pas avoir aiplatform installe
    try:
        from vertexai.resources.preview import ml_monitoring
    except ImportError as e:
        raise ImportError(
            "vertexai.resources.preview.ml_monitoring non disponible. "
            "Lance: python3 -m pip install --upgrade google-cloud-aiplatform"
        ) from e

    feature_fields = [
        ml_monitoring.spec.FieldSchema(name=name, data_type=_vertex_type(name)) for name in feature_names
    ]
    prediction_fields = [
        ml_monitoring.spec.FieldSchema(name="risk_score", data_type="float"),
        ml_monitoring.spec.FieldSchema(name="decision", data_type="categorical"),
    ]

    return ml_monitoring.spec.ModelMonitoringSchema(
        feature_fields=feature_fields, prediction_fields=prediction_fields
    )


def _normalize_bq_table_uri(value: str) -> str:
    """
    Vertex attend typiquement un format : bq://project.dataset.table
    On accepte aussi project.dataset.table (sans préfixe bq://) pour éviter les erreurs.
    """
    v = value.strip()
    if "<" in v or ">" in v:
        raise ValueError(
            "Valeur --target-bq-table-uri contient des placeholders ('<' ou '>'). "
            "Remplace-les par un dataset/table réel."
        )
    if v.startswith("bq://"):
        return v
    # Accept: project.dataset.table
    parts = v.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"--target-bq-table-uri invalide : {value}. Attendu : bq://project.dataset.table "
            "ou project.dataset.table"
        )
    return f"bq://{v}"


def _find_existing_reference_model(*, aiplatform, project: str, region: str, display_name: str):
    models = aiplatform.Model.list(project=project, location=region)
    matches = [model for model in models if getattr(model, "display_name", None) == display_name]
    return _pick_latest_by_create_time(matches)


def _find_existing_model_monitor(*, ml_monitoring, project: str, region: str, display_name: str):
    monitors = ml_monitoring.ModelMonitor.list(project=project, location=region)
    matches = [monitor for monitor in monitors if getattr(monitor, "display_name", None) == display_name]
    return _pick_latest_by_create_time(matches)


def main() -> None:
    ROOT = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(description="Vertex AI Model Monitoring - run after deploy")
    parser.add_argument("--project", default="sentinelle-485209")
    parser.add_argument("--region", default="europe-west1")
    parser.add_argument("--bucket", default="sentinelle-485209-ml-data")

    parser.add_argument("--version", required=True, help="Ex: 2.0.1-mlflow ou v2.0.1-mlflow")
    parser.add_argument(
        "--target-bq-table-uri",
        required=True,
        help='Format attendu: bq://project.dataset.table (ex: bq://sentinelle-485209.ml_monitoring.inference_logs_last_24h)',
    )
    parser.add_argument("--timestamp-field", default="request_time")
    parser.add_argument("--window", default="24h", help="Format Vertex attendu: 1h/2d/24h...")
    parser.add_argument("--alert-email", default="carel.clogenson@epitech.digital")

    parser.add_argument(
        "--schema-path",
        default=None,
        help="Chemin local vers feature_schema.json. Par defaut: artifacts/v<V>/feature_schema.json",
    )
    parser.add_argument(
        "--local-baseline-path",
        default=None,
        help="Chemin local vers baseline_train.jsonl. Par defaut: artifacts/v<V>/baseline_train.jsonl",
    )
    parser.add_argument(
        "--baseline-gcs-uri",
        default=None,
        help="URI GCS baseline (jsonl). Par defaut: gs://<bucket>/monitoring/baseline/v<V>/train_features.jsonl",
    )

    parser.add_argument(
        "--run-name",
        default=None,
        help="Nom affiché du job de monitoring. Par defaut: inference-<version>-<dateUTC>",
    )
    parser.add_argument(
        "--model-monitor-display-name",
        default=None,
        help="Display name du ModelMonitor. Par defaut: sentinelle-ml-engine-v2-monitor-<version>",
    )
    parser.add_argument(
        "--reference-model-resource",
        default=None,
        help="Resource name d'un reference model Vertex existant (optionnel). Ex: projects/.../models/<ID>@1",
    )
    parser.add_argument(
        "--reference-model-display-name",
        default="sentinelle-ml-engine-reference",
        help="Display name du reference model Vertex a reutiliser si possible.",
    )
    parser.add_argument(
        "--no-reuse-existing-model-monitor",
        action="store_true",
        help="Forcer la creation d'un nouveau ModelMonitor meme si un display_name identique existe deja.",
    )
    parser.add_argument(
        "--no-reuse-existing-reference-model",
        action="store_true",
        help="Forcer la creation d'un nouveau reference model meme si un display_name identique existe deja.",
    )

    args = parser.parse_args()

    version = _normalize_version(args.version)
    version_dir = f"v{version}"

    schema_path = Path(args.schema_path) if args.schema_path else ROOT / "artifacts" / version_dir / "feature_schema.json"
    local_baseline_path = (
        Path(args.local_baseline_path)
        if args.local_baseline_path
        else ROOT / "artifacts" / version_dir / "baseline_train.jsonl"
    )

    baseline_gcs_uri = (
        args.baseline_gcs_uri
        if args.baseline_gcs_uri
        else f"gs://{args.bucket}/monitoring/baseline/{version_dir}/train_features.jsonl"
    )

    run_name = args.run_name
    if not run_name:
        run_name = f"inference-{version}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    model_monitor_display_name = args.model_monitor_display_name
    if not model_monitor_display_name:
        model_monitor_display_name = f"sentinelle-ml-engine-v2-monitor-{version}"

    # 1) Ensure baseline exists in GCS
    _ensure_baseline_uploaded(
        local_baseline_path=local_baseline_path,
        bucket_name=args.bucket,
        baseline_gcs_uri=baseline_gcs_uri,
    )

    # 2) Load schema
    schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
    feature_names = schema_data.get("features") or []
    if not feature_names:
        raise ValueError(f"Aucune feature dans le schema : {schema_path}")

    # 3) Setup Vertex AI Model Monitor + Run
    try:
        from google.cloud import aiplatform
        from vertexai.resources.preview import ml_monitoring
    except ImportError as e:
        raise ImportError(
            "Imports Vertex/Aiplatform manquants. Lance: python3 -m pip install --upgrade google-cloud-aiplatform"
        ) from e

    aiplatform.init(project=args.project, location=args.region)

    # Reference model : si fourni on le reuse, sinon on tente de reutiliser le plus recent,
    # puis seulement en dernier recours on cree un placeholder.
    model_version_id = "1"
    model_resource = ""
    if args.reference_model_resource:
        model_resource = args.reference_model_resource.strip()
        if "@" in model_resource:
            model_resource, model_version_id = model_resource.rsplit("@", 1)
    else:
        reused_model = None
        if not args.no_reuse_existing_reference_model:
            reused_model = _find_existing_reference_model(
                aiplatform=aiplatform,
                project=args.project,
                region=args.region,
                display_name=args.reference_model_display_name,
            )

        if reused_model is not None:
            model_resource = reused_model.resource_name
            model_version_id = getattr(reused_model, "version_id", None) or "1"
            print(f"♻️ Reference model reutilise: {reused_model.resource_name}@{model_version_id}")
        else:
            # Upload d'un reference model (placeholder). Peut necessiter des permissions Vertex.
            print("🆕 Aucun reference model reutilisable, creation...")
            model = aiplatform.Model.upload(display_name=args.reference_model_display_name)
            model_resource = model.resource_name
            model_version_id = getattr(model, "version_id", None) or "1"
            print(f"✅ Reference model cree: {model.resource_name}@{model_version_id}")

    # Monitoring schema
    monitoring_schema = _build_monitoring_schema(feature_names)

    drift_spec = ml_monitoring.spec.DataDriftSpec(
        categorical_metric_type="l_infinity",
        numeric_metric_type="jensen_shannon_divergence",
        default_categorical_alert_threshold=0.1,
        default_numeric_alert_threshold=0.1,
    )
    tabular_objective_spec = ml_monitoring.spec.TabularObjective(
        feature_drift_spec=drift_spec, prediction_output_drift_spec=drift_spec
    )
    notification_spec = ml_monitoring.spec.NotificationSpec(user_emails=[args.alert_email])

    training_input = ml_monitoring.spec.MonitoringInput(gcs_uri=baseline_gcs_uri, data_format="jsonl")

    model_monitor = None
    if not args.no_reuse_existing_model_monitor:
        model_monitor = _find_existing_model_monitor(
            ml_monitoring=ml_monitoring,
            project=args.project,
            region=args.region,
            display_name=model_monitor_display_name,
        )

    if model_monitor is not None:
        print(f"♻️ ModelMonitor reutilise: {model_monitor.resource_name}")
    else:
        print("🧩 Creation du ModelMonitor...")
        model_monitor = ml_monitoring.ModelMonitor.create(
            display_name=model_monitor_display_name,
            model_name=model_resource,
            model_version_id=model_version_id,
            model_monitoring_schema=monitoring_schema,
            training_dataset=training_input,
            tabular_objective_spec=tabular_objective_spec,
            notification_spec=notification_spec,
        )

        print(f"✅ ModelMonitor cree: {model_monitor.resource_name}")

    target_table_uri = _normalize_bq_table_uri(args.target_bq_table_uri)

    target_input = ml_monitoring.spec.MonitoringInput(
        table_uri=target_table_uri,
        timestamp_field=args.timestamp_field,
        window=args.window,
    )

    print("🚀 Lancement du ModelMonitoringJob (sync)...")
    job = model_monitor.run(target_dataset=target_input, display_name=run_name, sync=True)
    print(f"✅ Job termine. Resource name: {job.resource_name}")


if __name__ == "__main__":
    main()

