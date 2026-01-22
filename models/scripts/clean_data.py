"""
Data cleaning script for ML Payon.

Inputs (expected in Data/raw/ or data/raw/):
  - Dataset_flaged.csv (PaySim format, supervised label isFraud)
  - dataset_legit_no_status.csv (Payon Transaction-like, no label)
  - dataset_fraud_no_status.csv (Payon Transaction-like, no label)
  - dataset_mixed_no_status.csv (Payon Transaction-like, no label)

Outputs (written in Data/processed/ by default):
  - paysim_clean.csv
  - payon_legit_clean.csv
  - payon_fraud_clean.csv
  - payon_mixed_clean.csv
  - payon_all_clean.csv (union + dataset_source column)

Report (written in Data/reports/ by default):
  - cleaning_report.json

Key rules:
  - Normalize direction: IN/OUT -> incoming/outgoing
  - Parse timestamps as UTC
  - Parse metadata.raw_payload JSON string and extract safe fields
  - Prevent leakage: remove metadata.risk_score from extracted metadata features
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _import_pandas():
    try:
        import pandas as pd  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "pandas is required. Install dependencies first:\n"
            "  python -m pip install -r requirements.txt\n"
        ) from e
    return pd


def _find_data_dir(repo_root: Path, explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()

    candidates = [repo_root / "Data", repo_root / "data"]
    for c in candidates:
        if (c / "raw").exists():
            return c
    # fallback: default to Data even if missing
    return repo_root / "Data"


def _to_iso_z(dt_series, keep_micros: bool = True):
    """
    Convert timezone-aware pandas datetime series to ISO-8601 with Z.
    """
    # dt_series is expected to be tz-aware (UTC). We'll keep microseconds to avoid information loss.
    if keep_micros:
        return dt_series.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ").where(~dt_series.isna(), None)
    return dt_series.dt.strftime("%Y-%m-%dT%H:%M:%SZ").where(~dt_series.isna(), None)


def _normalize_direction(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip().upper()
    if s == "" or s == "NAN":
        return None
    if s == "IN":
        return "incoming"
    if s == "OUT":
        return "outgoing"
    # tolerate already-normalized
    if s == "INCOMING":
        return "incoming"
    if s == "OUTGOING":
        return "outgoing"
    return None


def _safe_bool(val: Any) -> Optional[bool]:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("true", "1", "yes", "y"):
        return True
    if s in ("false", "0", "no", "n"):
        return False
    return None


@dataclass
class DatasetReport:
    name: str
    input_path: str
    rows_in: int
    rows_out: int
    duplicates_dropped: int = 0
    missing_core_dropped: int = 0
    invalid_created_at: int = 0
    unknown_direction: int = 0
    metadata_parse_failed: int = 0
    metadata_had_risk_score: int = 0


def clean_paysim_csv(input_path: Path, output_path: Path) -> DatasetReport:
    pd = _import_pandas()
    df = pd.read_csv(input_path)
    rows_in = int(df.shape[0])

    # Enforce numeric types where expected
    numeric_cols = [
        "step",
        "amount",
        "oldbalanceOrg",
        "newbalanceOrig",
        "oldbalanceDest",
        "newbalanceDest",
        "isFraud",
        "isFlaggedFraud",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Minimal cleaning: drop rows without required fields
    required = ["type", "amount", "nameOrig", "nameDest", "isFraud"]
    before = df.shape[0]
    df = df.dropna(subset=required)
    missing_core_dropped = int(before - df.shape[0])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    return DatasetReport(
        name="paysim_supervised",
        input_path=str(input_path),
        rows_in=rows_in,
        rows_out=int(df.shape[0]),
        missing_core_dropped=missing_core_dropped,
    )


def _parse_metadata_payload(raw: Any) -> Tuple[Dict[str, Any], bool, bool]:
    """
    Returns: (payload_dict, parse_ok, had_risk_score)
    """
    if raw is None:
        return {}, True, False
    s = str(raw).strip()
    if s == "" or s.lower() == "nan":
        return {}, True, False
    try:
        payload = json.loads(s)
        if not isinstance(payload, dict):
            return {}, False, False
        had_risk_score = "risk_score" in payload
        # prevent leakage
        payload.pop("risk_score", None)
        return payload, True, had_risk_score
    except Exception:
        return {}, False, False


def clean_payon_csv(input_path: Path, output_path: Path, dataset_source: str, drop_invalid_core: bool) -> DatasetReport:
    pd = _import_pandas()

    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    rows_in = int(df.shape[0])

    expected_cols = [
        "transaction_id",
        "created_at",
        "provider_created_at",
        "executed_at",
        "provider",
        "provider_tx_id",
        "initiator_user_id",
        "source_wallet_id",
        "destination_wallet_id",
        "amount",
        "currency",
        "transaction_type",
        "direction",
        "country",
        "city",
        "description",
        "metadata.raw_payload",
    ]

    # Ensure all expected columns exist (create missing as empty)
    for c in expected_cols:
        if c not in df.columns:
            df[c] = ""

    # amount -> numeric
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    # timestamps -> UTC
    created_at_dt = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    provider_created_at_dt = pd.to_datetime(df["provider_created_at"], errors="coerce", utc=True)
    executed_at_dt = pd.to_datetime(df["executed_at"], errors="coerce", utc=True)

    invalid_created_at = int(created_at_dt.isna().sum())

    # normalize direction
    direction_norm = df["direction"].map(_normalize_direction)
    unknown_direction = int(direction_norm.isna().sum())

    # metadata parsing (stringified JSON)
    meta_is_vpn = []
    meta_ip_version = []
    meta_source_device = []
    metadata_parse_failed = 0
    metadata_had_risk_score = 0

    for raw in df["metadata.raw_payload"].tolist():
        payload, ok, had_risk = _parse_metadata_payload(raw)
        if not ok:
            metadata_parse_failed += 1
        if had_risk:
            metadata_had_risk_score += 1

        meta_is_vpn.append(_safe_bool(payload.get("is_vpn")))
        meta_ip_version.append(payload.get("ip_version"))
        meta_source_device.append(payload.get("source_device"))

    df["meta_is_vpn"] = meta_is_vpn
    df["meta_ip_version"] = meta_ip_version
    df["meta_source_device"] = meta_source_device

    # Do NOT keep raw metadata by default in processed outputs (can contain PII).
    # If you need it for debugging, modify this script or produce a dedicated debug export.
    df = df.drop(columns=["metadata.raw_payload"], errors="ignore")

    # derived flags
    df["has_provider_tx_id"] = df["provider_tx_id"].astype(str).str.strip().ne("")
    df["has_executed_at"] = ~executed_at_dt.isna()
    df["dataset_source"] = dataset_source

    # replace timestamp columns with normalized ISO Z strings
    df["created_at"] = _to_iso_z(created_at_dt)
    df["provider_created_at"] = _to_iso_z(provider_created_at_dt)
    df["executed_at"] = _to_iso_z(executed_at_dt)

    # normalize direction
    df["direction"] = direction_norm

    # core fields required for training/scoring
    core_required = [
        "transaction_id",
        "created_at",
        "initiator_user_id",
        "source_wallet_id",
        "destination_wallet_id",
        "amount",
        "currency",
        "transaction_type",
        "direction",
    ]
    before_core = df.shape[0]
    if drop_invalid_core:
        df = df.dropna(subset=core_required)
        # transaction_id could be empty string (not NA); enforce non-empty
        df = df[df["transaction_id"].astype(str).str.strip().ne("")]
    missing_core_dropped = int(before_core - df.shape[0])

    # dedup by transaction_id (keep first)
    before_dups = df.shape[0]
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")
    duplicates_dropped = int(before_dups - df.shape[0])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    return DatasetReport(
        name=dataset_source,
        input_path=str(input_path),
        rows_in=rows_in,
        rows_out=int(df.shape[0]),
        duplicates_dropped=duplicates_dropped,
        missing_core_dropped=missing_core_dropped,
        invalid_created_at=invalid_created_at,
        unknown_direction=unknown_direction,
        metadata_parse_failed=metadata_parse_failed,
        metadata_had_risk_score=metadata_had_risk_score,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean Payon ML datasets (raw -> processed).")
    parser.add_argument("--data-dir", default=None, help="Path to data directory (containing raw/). Auto-detected by default.")
    parser.add_argument("--raw-dir", default=None, help="Override raw directory (defaults to <data-dir>/raw).")
    parser.add_argument("--out-dir", default=None, help="Output directory (defaults to <data-dir>/processed).")
    parser.add_argument("--report-dir", default=None, help="Report directory (defaults to <data-dir>/reports).")
    parser.add_argument("--drop-invalid-core", action="store_true", default=True, help="Drop rows missing core fields (default: true).")
    parser.add_argument("--keep-invalid-core", action="store_false", dest="drop_invalid_core", help="Keep rows even if core fields missing.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    data_dir = _find_data_dir(repo_root, args.data_dir)
    raw_dir = Path(args.raw_dir).resolve() if args.raw_dir else (data_dir / "raw")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else (data_dir / "processed")
    report_dir = Path(args.report_dir).resolve() if args.report_dir else (data_dir / "reports")

    if not raw_dir.exists():
        print(f"[ERROR] raw directory not found: {raw_dir}", file=sys.stderr)
        return 2

    report_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    reports = []

    # PaySim supervised
    paysim_in = raw_dir / "Dataset_flaged.csv"
    if paysim_in.exists():
        reports.append(clean_paysim_csv(paysim_in, out_dir / "paysim_clean.csv"))
    else:
        print(f"[WARN] missing {paysim_in}")

    # Payon-like datasets (no label)
    payon_files = [
        ("payon_legit_no_status", "dataset_legit_no_status.csv", "payon_legit_clean.csv"),
        ("payon_fraud_no_status", "dataset_fraud_no_status.csv", "payon_fraud_clean.csv"),
        ("payon_mixed_no_status", "dataset_mixed_no_status.csv", "payon_mixed_clean.csv"),
    ]

    cleaned_frames = []
    pd = _import_pandas()

    for ds_name, in_name, out_name in payon_files:
        p_in = raw_dir / in_name
        if not p_in.exists():
            print(f"[WARN] missing {p_in}")
            continue
        rep = clean_payon_csv(p_in, out_dir / out_name, ds_name, drop_invalid_core=bool(args.drop_invalid_core))
        reports.append(rep)

        # Reload cleaned to build a union file (keeps script simple and consistent)
        cleaned_frames.append(pd.read_csv(out_dir / out_name))

    if cleaned_frames:
        df_all = pd.concat(cleaned_frames, ignore_index=True)
        df_all.to_csv(out_dir / "payon_all_clean.csv", index=False)

    report_path = report_dir / "cleaning_report.json"
    payload = {
        "data_dir": str(data_dir),
        "raw_dir": str(raw_dir),
        "out_dir": str(out_dir),
        "report_dir": str(report_dir),
        "datasets": [asdict(r) for r in reports],
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"[OK] Wrote cleaned datasets to: {out_dir}")
    print(f"[OK] Wrote report to: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

