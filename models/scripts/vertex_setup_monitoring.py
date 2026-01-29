#!/usr/bin/env python3
"""
Configure Vertex AI Model Monitoring v2 pour le ML Engine Payon (Cloud Run).

- Enregistre un reference model dans le Model Registry
- Crée un Model Monitor (schéma depuis feature_schema.json, baseline GCS optionnelle, alertes)

Usage:
  cd models
  export PROJECT_ID=sentinelle-485209 REGION=europe-west1
  export ALERT_EMAIL=carel.clogenson@epitech.digital
  python scripts/vertex_setup_monitoring.py

Variables d'environnement:
  PROJECT_ID         Projet GCP (défaut: sentinelle-485209)
  REGION             Région Vertex (défaut: europe-west1)
  MODEL_DISPLAY_NAME Nom du modèle dans le Registry (défaut: sentinelle-ml-engine)
  FEATURE_SCHEMA_PATH Chemin vers feature_schema.json (défaut: artifacts/v1.0.0-test/feature_schema.json)
  BASELINE_GCS_URI   gs://bucket/monitoring/baseline/v1.0.0-test/train_features.jsonl (optionnel)
  ALERT_EMAIL        Email pour alertes drift (défaut: carel.clogenson@epitech.digital)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Répertoire racine models
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _vertex_type(feature_name: str) -> str:
    """Mappe un nom de feature vers le type Vertex (float, integer, categorical)."""
    n = feature_name.lower()
    if any(x in n for x in ("amount", "sum_", "mean_", "max_", "ratio", "concentration", "entropy", "log_")):
        return "float"
    if any(x in n for x in ("count", "hour_", "day_of_", "destinations_", "days_since", "tx_count")):
        return "integer"
    return "categorical"


def build_monitoring_schema(feature_names: list[str]):
    """Construit ModelMonitoringSchema à partir de la liste de features."""
    try:
        from vertexai.resources.preview import ml_monitoring
    except ImportError as e:
        raise ImportError(
            "vertexai.resources.preview.ml_monitoring non disponible. "
            "Lance: python3 -m pip install --upgrade google-cloud-aiplatform"
        ) from e

    feature_fields = [
        ml_monitoring.spec.FieldSchema(name=name, data_type=_vertex_type(name))
        for name in feature_names
    ]
    prediction_fields = [
        ml_monitoring.spec.FieldSchema(name="risk_score", data_type="float"),
        ml_monitoring.spec.FieldSchema(name="decision", data_type="categorical"),
    ]
    return ml_monitoring.spec.ModelMonitoringSchema(
        feature_fields=feature_fields,
        prediction_fields=prediction_fields,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Vertex AI Model Monitoring – setup Payon")
    parser.add_argument("--project", default=os.getenv("PROJECT_ID", "sentinelle-485209"))
    parser.add_argument("--region", default=os.getenv("REGION", "europe-west1"))
    parser.add_argument("--model-name", default=os.getenv("MODEL_DISPLAY_NAME", "sentinelle-ml-engine"))
    parser.add_argument(
        "--schema",
        type=Path,
        default=ROOT / "artifacts" / "v1.0.0-test" / "feature_schema.json",
    )
    parser.add_argument("--baseline-gcs", default=os.getenv("BASELINE_GCS_URI", ""))
    parser.add_argument("--alert-email", default=os.getenv("ALERT_EMAIL", "carel.clogenson@epitech.digital"))
    parser.add_argument(
        "--model-resource",
        default=os.getenv("VERTEX_MODEL_RESOURCE_NAME", ""),
        help="Resource name d'un modèle déjà créé (ex. projects/.../models/123). Si vide, on tente Model.upload.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Afficher la config sans exécuter")
    args = parser.parse_args()

    if not args.schema.exists():
        print(f"❌ Schéma introuvable: {args.schema}")
        print("   Indiquez --schema ou exportez les artifacts (ex. v1.0.0-test).")
        sys.exit(1)

    with open(args.schema) as f:
        schema_data = json.load(f)
    feature_names = schema_data.get("features", [])
    if not feature_names:
        print("❌ Aucune feature dans le schéma")
        sys.exit(1)

    print("🔧 Vertex AI Model Monitoring – configuration Payon")
    print(f"   Projet: {args.project}")
    print(f"   Région: {args.region}")
    print(f"   Modèle: {args.model_name}")
    print(f"   Features: {len(feature_names)}")
    print(f"   Alert email: {args.alert_email}")

    if args.dry_run:
        print("\n[DRY-RUN] Rien n'est exécuté.")
        return

    try:
        from google.cloud import aiplatform
        from vertexai.resources.preview import ml_monitoring
    except ImportError as e:
        print(f"❌ Import impossible: {e}")
        print("   Installe le SDK avec le même Python que tu utilises pour lancer le script:")
        print("   python3 -m pip install --upgrade google-cloud-aiplatform")
        sys.exit(1)

    aiplatform.init(project=args.project, location=args.region)

    # 1. Reference model (placeholder pour Cloud Run)
    model_version_id = "1"
    if args.model_resource:
        model_resource = args.model_resource.strip()
        print(f"\n1️⃣  Modèle existant: {model_resource}")
        # Extraire l'ID de version si présent (ex. .../models/123@1)
        if "@" in model_resource:
            model_resource, model_version_id = model_resource.rsplit("@", 1)
    else:
        print("\n1️⃣  Enregistrement du reference model…")
        try:
            model = aiplatform.Model.upload(
                display_name=args.model_name,
            )
            model_resource = model.resource_name
            print(f"   ✅ Modèle enregistré: {model_resource}")
        except Exception as e:
            print("   ⚠️  Model.upload a échoué (certains SDK exigent un artifact).")
            print("   Créez le modèle depuis la console Vertex AI → Model Registry → créer un modèle « non déployé »,")
            print("   puis relancez avec: --model-resource projects/.../locations/.../models/<ID>")
            raise SystemExit(1) from e
    print(f"   Version ID: {model_version_id}")

    # 2. Schéma
    monitoring_schema = build_monitoring_schema(feature_names)

    # 3. Baseline (optionnel)
    training_input = None
    if args.baseline_gcs and args.baseline_gcs.startswith("gs://"):
        print(f"\n2️⃣  Baseline GCS: {args.baseline_gcs}")
        training_input = ml_monitoring.spec.MonitoringInput(
            gcs_uri=args.baseline_gcs.rstrip("/"),
            data_format="jsonl",
        )
    else:
        print("\n2️⃣  Pas de baseline GCS (jobs pourront cibler un chemin target uniquement).")

    # 4. Objectifs (drift)
    drift_spec = ml_monitoring.spec.DataDriftSpec(
        categorical_metric_type="l_infinity",
        numeric_metric_type="jensen_shannon_divergence",
        default_categorical_alert_threshold=0.1,
        default_numeric_alert_threshold=0.1,
    )
    tabular_spec = ml_monitoring.spec.TabularObjective(
        feature_drift_spec=drift_spec,
        prediction_output_drift_spec=drift_spec,
    )

    # 5. Notification
    notification_spec = ml_monitoring.spec.NotificationSpec(
        user_emails=[args.alert_email],
    )

    # 6. Créer le Model Monitor
    print("\n3️⃣  Création du Model Monitor…")
    monitor = ml_monitoring.ModelMonitor.create(
        display_name=f"{args.model_name}-monitor",
        model_name=model_resource,
        model_version_id=model_version_id,
        model_monitoring_schema=monitoring_schema,
        training_dataset=training_input,
        tabular_objective_spec=tabular_spec,
        notification_spec=notification_spec,
    )
    print(f"   ✅ Model Monitor créé: {monitor.resource_name}")
    print("\n📌 Prochaines étapes:")
    print("   - Lancer un job: console Vertex AI → Monitoring → Run now")
    print("   - Target dataset: gs://sentinelle-485209-ml-data/monitoring/inference_logs/")
    print("   - Voir 05_MONITORING_VERTEX.md pour les détails.")


if __name__ == "__main__":
    main()
