#!/usr/bin/env python3
"""
Pipeline automatise pour le monitoring post-deploiement.

Flux normal :
1) verification optionnelle du service ML Engine (/health)
2) lecture des logs d'inference reels depuis GCS
3) normalisation des types instables (bool -> 0/1) pour BigQuery
4) chargement dans une table BigQuery normalisee
5) creation / refresh d'une vue last_24h
6) verification GO / NO-GO (COUNT + min/max request_time)
7) lancement du run Vertex AI via le script existant

Optionnellement, le script peut aussi generer un petit trafic de validation
technique via /score pour un smoke test post-deploiement.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from google.cloud import bigquery
from google.cloud import storage


ROOT = Path(__file__).resolve().parent.parent


def _normalize_version(version: str) -> str:
    version = version.strip()
    return version[1:] if version.startswith("v") else version


def _default_smoke_test_payload() -> dict[str, Any]:
    return {
        "transaction": {
            "transaction_id": "monitoring-test",
            "amount": 75.50,
            "currency": "PYC",
            "source_wallet_id": "wallet_user_123",
            "destination_wallet_id": "wallet_merchant_456",
            "transaction_type": "TRANSFER",
            "direction": "outgoing",
            "created_at": "2026-01-01T00:00:00Z",
            "country": "FR",
            "features": {
                "transactional": {
                    "amount": 75.50,
                    "log_amount": 4.32,
                    "currency_is_pyc": True,
                    "direction_outgoing": 1,
                    "hour_of_day": 14,
                    "day_of_week": 1,
                    "transaction_type_TRANSFER": 1,
                },
                "historical": {
                    "src_tx_count_out_5m": 0,
                    "src_tx_count_out_1h": 2,
                    "src_tx_count_out_24h": 8,
                    "src_tx_count_out_7d": 45,
                    "src_tx_amount_sum_out_1h": 150.0,
                    "src_tx_amount_mean_out_7d": 65.0,
                    "src_tx_amount_max_out_7d": 120.0,
                    "src_unique_destinations_24h": 3,
                    "is_new_destination_30d": 0,
                    "src_to_dst_tx_count_30d": 5,
                    "days_since_last_src_to_dst": 2.5,
                    "src_destination_concentration_7d": 0.15,
                    "src_destination_entropy_7d": 2.8,
                    "is_new_country_30d": 0,
                    "country_mismatch": 0,
                    "src_failed_count_24h": 0,
                    "src_failed_ratio_7d": 0.0,
                },
            },
        },
        "context": {
            "source_wallet": {"balance": 500.0, "status": "active"},
            "user": {"status": "active", "risk_level": "low"},
        },
    }


def _run_curl_json(*, method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, str]:
    marker = "HTTP_CODE:"
    cmd = ["curl", "-sS", "-X", method.upper(), url, "-w", f"\n{marker}%{{http_code}}"]
    if payload is not None:
        cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(payload)])

    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"curl a echoue ({completed.returncode}) : {completed.stderr.strip()}")

    stdout = completed.stdout
    body, sep, status = stdout.rpartition(f"\n{marker}")
    if not sep:
        raise RuntimeError(f"Reponse curl inattendue : {stdout}")

    return int(status.strip()), body.strip()


def _resolve_ml_engine_url(*, project: str, region: str, service: str) -> str:
    cmd = [
        "gcloud",
        "run",
        "services",
        "describe",
        service,
        f"--region={region}",
        f"--project={project}",
        "--format=value(status.url)",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Impossible de recuperer l'URL ML Engine : {completed.stderr.strip()}")

    url = completed.stdout.strip()
    if not url:
        raise RuntimeError("gcloud run services describe n'a retourne aucune URL.")
    return url


def _assert_health(url: str) -> dict[str, Any]:
    status, body = _run_curl_json(method="GET", url=f"{url.rstrip('/')}/health")
    if status != 200:
        raise RuntimeError(f"/health a retourne HTTP {status}: {body}")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Reponse /health non JSON : {body}") from exc

    print(f"OK /health : model_version={payload.get('model_version')}")
    return payload


def _generate_test_traffic(*, url: str, count: int, pause_ms: int) -> None:
    if count <= 0:
        return

    base_payload = _default_smoke_test_payload()
    ok = 0
    for i in range(count):
        payload = copy.deepcopy(base_payload)
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        payload["transaction"]["transaction_id"] = f"monitoring-test-{int(time.time())}-{i}"
        payload["transaction"]["created_at"] = now

        status, body = _run_curl_json(method="POST", url=f"{url.rstrip('/')}/score", payload=payload)
        if status != 200:
            raise RuntimeError(f"/score a retourne HTTP {status}: {body}")
        ok += 1
        print(f"Score smoke test {i + 1}/{count} OK")
        if pause_ms > 0:
            time.sleep(pause_ms / 1000.0)

    print(f"Trafic de validation termine : {ok}/{count} requetes OK")


def _date_prefixes(*, base_prefix: str, days_back: int) -> list[str]:
    today = datetime.now(timezone.utc).date()
    prefixes: list[str] = []
    cleaned_prefix = base_prefix.strip().strip("/")
    for offset in range(days_back):
        day = today - timedelta(days=offset)
        prefixes.append(f"{cleaned_prefix}/{day.strftime('%Y/%m/%d')}")
    return prefixes


def _normalize_for_bigquery(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, list):
        return [_normalize_for_bigquery(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_for_bigquery(item) for key, item in value.items()}
    return value


def _download_gcs_rows(*, bucket_name: str, prefixes: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    client = storage.Client()
    rows: list[dict[str, Any]] = []
    matched_files: list[str] = []

    for prefix in prefixes:
        print(f"Lecture GCS : gs://{bucket_name}/{prefix}/")
        for blob in client.list_blobs(bucket_name, prefix=prefix):
            if not blob.name.endswith(".jsonl"):
                continue
            matched_files.append(blob.name)
            text = blob.download_as_text()
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                row = json.loads(line)
                rows.append(_normalize_for_bigquery(row))

    return rows, matched_files


def _ensure_dataset(*, client: bigquery.Client, project: str, dataset_name: str, region: str) -> None:
    dataset_id = f"{project}.{dataset_name}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = region
    client.create_dataset(dataset, exists_ok=True)


def _load_rows_to_bigquery(
    *,
    client: bigquery.Client,
    table_id: str,
    rows: list[dict[str, Any]],
) -> bigquery.table.Table:
    if not rows:
        raise RuntimeError("Aucune ligne a charger dans BigQuery.")

    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()
    table = client.get_table(table_id)
    print(f"Chargement BigQuery OK : {table.num_rows} lignes dans {table_id}")
    return table


def _window_to_sql_interval(window: str) -> str:
    match = re.fullmatch(r"(\d+)([hd])", window.strip().lower())
    if not match:
        raise ValueError(f"Window non supportee pour la vue BigQuery : {window}. Exemples : 24h, 2d")

    quantity = int(match.group(1))
    unit = match.group(2)
    if unit == "h":
        return f"INTERVAL {quantity} HOUR"
    return f"INTERVAL {quantity} DAY"


def _create_or_replace_view(
    *,
    client: bigquery.Client,
    project: str,
    dataset: str,
    table: str,
    view: str,
    timestamp_field: str,
    window: str,
) -> None:
    interval = _window_to_sql_interval(window)
    query = f"""
    CREATE OR REPLACE VIEW `{project}.{dataset}.{view}` AS
    SELECT *
    FROM `{project}.{dataset}.{table}`
    WHERE SAFE_CAST({timestamp_field} AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), {interval})
    """
    client.query(query).result()
    print(f"Vue BigQuery OK : {project}.{dataset}.{view}")


def _read_view_stats(
    *,
    client: bigquery.Client,
    project: str,
    dataset: str,
    view: str,
    timestamp_field: str,
) -> dict[str, Any]:
    query = f"""
    SELECT
      COUNT(*) AS total_rows,
      MIN(SAFE_CAST({timestamp_field} AS TIMESTAMP)) AS min_request_time,
      MAX(SAFE_CAST({timestamp_field} AS TIMESTAMP)) AS max_request_time
    FROM `{project}.{dataset}.{view}`
    """
    rows = list(client.query(query).result())
    if not rows:
        raise RuntimeError("La requete de stats n'a retourne aucun resultat.")

    row = rows[0]
    result = {
        "total_rows": int(row["total_rows"] or 0),
        "min_request_time": row["min_request_time"],
        "max_request_time": row["max_request_time"],
    }
    print(
        "Vue last_24h : "
        f"count={result['total_rows']}, "
        f"min={result['min_request_time']}, "
        f"max={result['max_request_time']}"
    )
    return result


def _launch_vertex_run(
    *,
    version: str,
    project: str,
    region: str,
    bucket: str,
    timestamp_field: str,
    window: str,
    alert_email: str,
    target_bq_table_uri: str,
    schema_path: str | None,
    local_baseline_path: str | None,
    baseline_gcs_uri: str | None,
    model_monitor_display_name: str | None,
    reference_model_resource: str | None,
    reference_model_display_name: str | None,
    no_reuse_existing_model_monitor: bool,
    no_reuse_existing_reference_model: bool,
) -> None:
    script_path = ROOT / "scripts" / "run-vertex-monitoring-after-deploy.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--version",
        version,
        "--target-bq-table-uri",
        target_bq_table_uri,
        "--project",
        project,
        "--region",
        region,
        "--bucket",
        bucket,
        "--timestamp-field",
        timestamp_field,
        "--window",
        window,
        "--alert-email",
        alert_email,
    ]

    if schema_path:
        cmd.extend(["--schema-path", schema_path])
    if local_baseline_path:
        cmd.extend(["--local-baseline-path", local_baseline_path])
    if baseline_gcs_uri:
        cmd.extend(["--baseline-gcs-uri", baseline_gcs_uri])
    if model_monitor_display_name:
        cmd.extend(["--model-monitor-display-name", model_monitor_display_name])
    if reference_model_resource:
        cmd.extend(["--reference-model-resource", reference_model_resource])
    if reference_model_display_name:
        cmd.extend(["--reference-model-display-name", reference_model_display_name])
    if no_reuse_existing_model_monitor:
        cmd.append("--no-reuse-existing-model-monitor")
    if no_reuse_existing_reference_model:
        cmd.append("--no-reuse-existing-reference-model")

    print("Lancement du run Vertex...")
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline monitoring post-deploiement")
    parser.add_argument("--version", required=True, help="Ex: 2.0.1-mlflow ou v2.0.1-mlflow")
    parser.add_argument("--project", default="sentinelle-485209")
    parser.add_argument("--region", default="europe-west1")
    parser.add_argument("--bucket", default="sentinelle-485209-ml-data")
    parser.add_argument("--logs-prefix", default="monitoring/inference_logs")
    parser.add_argument("--timestamp-field", default="request_time")
    parser.add_argument("--window", default="24h", help="Ex: 24h, 2d")
    parser.add_argument("--alert-email", default="carel.clogenson@epitech.digital")

    parser.add_argument("--bq-dataset", default="ml_monitoring")
    parser.add_argument("--bq-table", default="inference_logs_v2")
    parser.add_argument("--bq-view", default="inference_logs_last_24h")
    parser.add_argument("--days-back", type=int, default=2, help="Nombre de jours GCS a charger (aujourd'hui inclus)")
    parser.add_argument("--min-rows", type=int, default=1, help="Nombre minimum de lignes avant run Vertex")

    parser.add_argument("--ml-engine-service", default="sentinelle-ml-engine-v2")
    parser.add_argument("--ml-engine-url", default=None)
    parser.add_argument("--skip-health-check", action="store_true")
    parser.add_argument(
        "--generate-test-traffic",
        type=int,
        default=0,
        help="Option de smoke test: nombre de requetes /score a envoyer. Laisser 0 pour le flux prod normal.",
    )
    parser.add_argument("--traffic-pause-ms", type=int, default=0, help="Pause entre requetes de test")
    parser.add_argument("--wait-after-traffic-sec", type=int, default=5, help="Pause avant lecture GCS")

    parser.add_argument("--skip-vertex-run", action="store_true", help="Preparer GCS/BigQuery sans lancer Vertex.")
    parser.add_argument("--schema-path", default=None)
    parser.add_argument("--local-baseline-path", default=None)
    parser.add_argument("--baseline-gcs-uri", default=None)
    parser.add_argument("--model-monitor-display-name", default=None)
    parser.add_argument("--reference-model-resource", default=None)
    parser.add_argument("--reference-model-display-name", default="sentinelle-ml-engine-reference")
    parser.add_argument("--no-reuse-existing-model-monitor", action="store_true")
    parser.add_argument("--no-reuse-existing-reference-model", action="store_true")

    args = parser.parse_args()

    version = _normalize_version(args.version)
    ml_engine_url = args.ml_engine_url
    need_service_url = args.generate_test_traffic > 0 or not args.skip_health_check
    if need_service_url and not ml_engine_url:
        ml_engine_url = _resolve_ml_engine_url(
            project=args.project,
            region=args.region,
            service=args.ml_engine_service,
        )
        print(f"ML Engine URL : {ml_engine_url}")

    if not args.skip_health_check:
        _assert_health(ml_engine_url)

    if args.generate_test_traffic > 0:
        _generate_test_traffic(
            url=ml_engine_url,
            count=args.generate_test_traffic,
            pause_ms=args.traffic_pause_ms,
        )
        if args.wait_after_traffic_sec > 0:
            print(f"Pause de {args.wait_after_traffic_sec}s pour laisser GCS se remplir...")
            time.sleep(args.wait_after_traffic_sec)

    prefixes = _date_prefixes(base_prefix=args.logs_prefix, days_back=args.days_back)
    rows, matched_files = _download_gcs_rows(bucket_name=args.bucket, prefixes=prefixes)
    print(f"Fichiers GCS trouves : {len(matched_files)}")
    print(f"Lignes JSONL lues : {len(rows)}")
    if not rows:
        raise RuntimeError("Aucun log d'inference trouve dans GCS pour la fenetre demandee.")

    bq_client = bigquery.Client(project=args.project)
    _ensure_dataset(client=bq_client, project=args.project, dataset_name=args.bq_dataset, region=args.region)

    table_id = f"{args.project}.{args.bq_dataset}.{args.bq_table}"
    _load_rows_to_bigquery(client=bq_client, table_id=table_id, rows=rows)

    _create_or_replace_view(
        client=bq_client,
        project=args.project,
        dataset=args.bq_dataset,
        table=args.bq_table,
        view=args.bq_view,
        timestamp_field=args.timestamp_field,
        window=args.window,
    )

    stats = _read_view_stats(
        client=bq_client,
        project=args.project,
        dataset=args.bq_dataset,
        view=args.bq_view,
        timestamp_field=args.timestamp_field,
    )

    if stats["total_rows"] < args.min_rows:
        raise RuntimeError(
            f"GO/NO-GO refuse : {stats['total_rows']} ligne(s) dans la vue, minimum requis = {args.min_rows}"
        )

    if args.skip_vertex_run:
        print("Run Vertex saute (--skip-vertex-run).")
        print(f"Table cible prete : bq://{args.project}.{args.bq_dataset}.{args.bq_view}")
        return

    _launch_vertex_run(
        version=version,
        project=args.project,
        region=args.region,
        bucket=args.bucket,
        timestamp_field=args.timestamp_field,
        window=args.window,
        alert_email=args.alert_email,
        target_bq_table_uri=f"bq://{args.project}.{args.bq_dataset}.{args.bq_view}",
        schema_path=args.schema_path,
        local_baseline_path=args.local_baseline_path,
        baseline_gcs_uri=args.baseline_gcs_uri,
        model_monitor_display_name=args.model_monitor_display_name,
        reference_model_resource=args.reference_model_resource,
        reference_model_display_name=args.reference_model_display_name,
        no_reuse_existing_model_monitor=args.no_reuse_existing_model_monitor,
        no_reuse_existing_reference_model=args.no_reuse_existing_reference_model,
    )

    print("Pipeline termine.")
    print("A verifier dans Google Cloud :")
    print("1. BigQuery > vue inference_logs_last_24h : COUNT/min/max OK")
    print("2. Vertex AI > Model monitoring > Run status = Succeeded")
    print("3. Vertex AI > onglets Input feature drift et Output inference drift")


if __name__ == "__main__":
    main()
