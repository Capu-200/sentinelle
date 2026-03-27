import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import numpy as np
import streamlit as st
from google.cloud import storage


@dataclass
class Config:
    bucket: str
    prefix_date: str  # e.g. "monitoring/inference_logs/2026/03/20"
    limit_files: int
    limit_lines_per_file: int


def _safe_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _parse_jsonl_text(text: str, limit_lines: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for i, line in enumerate(text.splitlines()):
        if not line.strip():
            continue
        if i >= limit_lines:
            break
        rows.append(json.loads(line))
    return rows


@st.cache_data(show_spinner=False)
def load_inference_logs(cfg: Config) -> List[Dict[str, Any]]:
    client = storage.Client()
    blobs = client.list_blobs(cfg.bucket, prefix=cfg.prefix_date)

    jsonl_names: List[str] = []
    for b in blobs:
        if b.name.endswith(".jsonl"):
            jsonl_names.append(b.name)
        if len(jsonl_names) >= cfg.limit_files:
            break

    if not jsonl_names:
        return []

    rows: List[Dict[str, Any]] = []
    for name in jsonl_names:
        blob = client.bucket(cfg.bucket).blob(name)
        txt = blob.download_as_text()
        rows.extend(_parse_jsonl_text(txt, cfg.limit_lines_per_file))

    return rows


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    decisions: Dict[str, int] = {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0}
    model_versions: Dict[str, int] = {}
    risk: List[float] = []

    for r in rows:
        d = str(r.get("decision", "")).strip()
        if d in decisions:
            decisions[d] += 1

        mv = str(r.get("model_version", "unknown")).strip()
        model_versions[mv] = model_versions.get(mv, 0) + 1

        rs = _safe_float(r.get("risk_score"))
        if rs is not None:
            risk.append(rs)

    risk_arr = np.array(risk, dtype=float) if risk else np.array([], dtype=float)

    percentiles = {}
    if risk_arr.size:
        percentiles = {
            "p10": float(np.percentile(risk_arr, 10)),
            "p50": float(np.percentile(risk_arr, 50)),
            "p90": float(np.percentile(risk_arr, 90)),
        }

    summary: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "requests_total": len(rows),
        "decisions": decisions,
        "model_versions": dict(sorted(model_versions.items(), key=lambda x: x[1], reverse=True)),
        "risk_score": {},
    }

    if risk_arr.size:
        summary["risk_score"] = {
            "min": float(risk_arr.min()),
            "max": float(risk_arr.max()),
            "mean": float(risk_arr.mean()),
            **percentiles,
        }

    return summary


def main() -> None:
    st.set_page_config(page_title="Sentinelle - Inference logs", layout="wide")
    st.title("Sentinelle - Monitoring (inference_logs JSONL)")

    with st.sidebar:
        st.header("Source GCS")
        bucket = st.text_input("Bucket", value="sentinelle-485209-ml-data")

        prefix_date = st.text_input(
            "prefix_date (YYYY/MM/DD sous monitoring/inference_logs)",
            value="monitoring/inference_logs/2026/03/20",
        )

        st.header("Limites (pour test)")
        limit_files = st.number_input("limit_files", min_value=1, max_value=500, value=50, step=1)
        limit_lines_per_file = st.number_input(
            "limit_lines_per_file",
            min_value=1,
            max_value=200000,
            value=5000,
            step=100,
        )

        load_btn = st.button("Load & summarize", type="primary")

    cfg = Config(
        bucket=bucket.strip(),
        prefix_date=prefix_date.strip().rstrip("/"),
        limit_files=int(limit_files),
        limit_lines_per_file=int(limit_lines_per_file),
    )

    if not load_btn:
        st.info("Clique sur `Load & summarize` pour charger et calculer les métriques.")
        return

    rows = load_inference_logs(cfg)
    st.write(f"Loaded rows: **{len(rows)}**")

    if not rows:
        st.warning("Aucun fichier .jsonl trouvé (ou limites trop restrictives).")
        return

    summary = summarize(rows)

    c1, c2, c3 = st.columns(3)
    c1.metric("requests_total", summary["requests_total"])
    c2.metric("model_version_top", next(iter(summary["model_versions"].keys()), "unknown"))
    c3.metric("risk_score_mean", summary["risk_score"].get("mean", None))

    st.subheader("Décisions (APPROVE/REVIEW/BLOCK)")
    decision_counts = summary["decisions"]
    st.bar_chart(decision_counts)

    st.subheader("Risk score (stats)")
    st.json(summary["risk_score"])

    st.subheader("Model versions (top)")
    mv_counts = summary["model_versions"]
    top_mv = dict(list(mv_counts.items())[:10])
    st.bar_chart(top_mv)

    st.subheader("Summary JSON (exportable)")
    st.download_button(
        label="Download summary.json",
        data=json.dumps(summary, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="inference_logs_summary.json",
        mime="application/json",
    )

    st.subheader("Exemple de lignes")
    st.dataframe(rows[:5])


if __name__ == "__main__":
    main()

