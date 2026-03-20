import json
import logging
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError


def _env(key: str, default: str) -> str:
    value = os.getenv(key)
    if value:
        return value
    logging.warning("Env var %s missing. Falling back to %s", key, default)
    return default


KAFKA_BOOTSTRAP = _env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_IN = _env("KAFKA_TOPIC_IN", "transaction.requests")
TOPIC_OUT = _env("KAFKA_TOPIC_OUT", "transaction.decisions")
GROUP_ID = _env("KAFKA_GROUP_ID", "payon-ia-worker")
ML_ENGINE_URL = _env(
    "ML_ENGINE_URL", "https://sentinelle-ml-engine-ntqku76mya-ew.a.run.app/score"
)
ML_TIMEOUT_S = int(os.getenv("ML_TIMEOUT_S", "10"))
ML_MAX_RETRIES = int(os.getenv("ML_MAX_RETRIES", "3"))
ML_RETRY_BACKOFF_S = float(os.getenv("ML_RETRY_BACKOFF_S", "1.0"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ia-worker] %(message)s",
    force=True,
)
logger = logging.getLogger("ia-worker")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def build_transactional_features(tx: Dict[str, Any]) -> Dict[str, Any]:
    amount = safe_float(tx.get("amount", 0))
    created_at = tx.get("created_at") or now_iso()
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        hour_of_day = dt.hour
        day_of_week = dt.weekday()
    except Exception:
        hour_of_day = 0
        day_of_week = 0
    currency = tx.get("currency", "PYC")
    direction = tx.get("direction", "outgoing") or "outgoing"
    txn_type = (tx.get("transaction_type") or "TRANSFER").upper()
    return {
        "amount": amount,
        "log_amount": round(math.log1p(amount), 4),
        "currency_is_pyc": currency.upper() == "PYC",
        "direction_outgoing": 1 if direction.lower() == "outgoing" else 0,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
        "transaction_type_TRANSFER": 1 if txn_type == "TRANSFER" else 0,
    }


def build_historical_features_new_user() -> Dict[str, Any]:
    return {
        "src_tx_count_out_5m": 0,
        "src_tx_count_out_1h": 0,
        "src_tx_count_out_24h": 0,
        "src_tx_count_out_7d": 0,
        "src_tx_amount_sum_out_1h": 0.0,
        "src_tx_amount_mean_out_7d": 0.0,
        "src_tx_amount_max_out_7d": 0.0,
        "src_unique_destinations_24h": 0,
        "is_new_destination_30d": 1,
        "src_to_dst_tx_count_30d": 0,
        "days_since_last_src_to_dst": -1.0,
        "src_destination_concentration_7d": 0.0,
        "src_destination_entropy_7d": 0.0,
        "is_new_country_30d": 1,
        "country_mismatch": 0,
        "src_failed_count_24h": 0,
        "src_failed_ratio_7d": 0.0,
    }


def build_enriched_payload(tx: Dict[str, Any]) -> Dict[str, Any]:
    created_at = tx.get("created_at") or now_iso()
    transaction = {
        "transaction_id": tx.get("transaction_id"),
        "amount": safe_float(tx.get("amount", 0)),
        "currency": tx.get("currency", "PYC"),
        "source_wallet_id": tx.get("source_wallet_id"),
        "destination_wallet_id": tx.get("destination_wallet_id"),
        "transaction_type": tx.get("transaction_type", "TRANSFER"),
        "direction": tx.get("direction", "outgoing"),
        "created_at": created_at,
        "country": tx.get("country", "FR"),
        "features": {
            "transactional": build_transactional_features(tx),
            "historical": tx.get("features", {})
            .get("historical", {})
            or tx.get("historical_features")
            or build_historical_features_new_user(),
        },
    }
    context = tx.get("context") or {
        "source_wallet": {
            "balance": safe_float(tx.get("source_balance", 0.0)),
            "status": tx.get("source_status", "active"),
        },
        "user": {
            "status": tx.get("user_status", "active"),
            "risk_level": tx.get("user_risk_level", "low"),
        },
    }
    return {"transaction": transaction, "context": context}


def call_ml_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(
        ML_ENGINE_URL,
        json=payload,
        timeout=ML_TIMEOUT_S,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return response.json()


def score_with_retry(payload: Dict[str, Any]) -> Dict[str, Any]:
    attempts = 0
    backoff = ML_RETRY_BACKOFF_S
    while True:
        try:
            return call_ml_engine(payload)
        except requests.RequestException as exc:
            attempts += 1
            if attempts >= ML_MAX_RETRIES:
                logger.error(
                    "ML scoring retries exhausted for tx=%s error=%s",
                    payload.get("transaction", {}).get("transaction_id"),
                    exc,
                )
                raise
            logger.warning(
                "ML scoring failed attempt=%s tx=%s retrying in %.1fs",
                attempts,
                payload.get("transaction", {}).get("transaction_id"),
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2.0
        except Exception:
            # Non HTTP issues (JSON, unexpected) should bubble up
            raise


def build_fallback(tx_id: Optional[str], features: Dict[str, Any], context: Dict[str, Any], reason: str) -> Dict[str, Any]:
    logger.warning("Fallback REVIEW decision emitted for %s (%s)", tx_id, reason)
    return {
        "transaction_id": tx_id,
        "fraud_score": 0.5,
        "decision": "REVIEW",
        "reasons": [reason],
        "model_version": "fallback",
        "features_snapshot": features,
        "context": context,
        "created_at": now_iso(),
    }


def publish_decision(producer: KafkaProducer, payload: Dict[str, Any]) -> bool:
    future = producer.send(TOPIC_OUT, payload)
    try:
        future.get(timeout=10)
        logger.info(
            "Decision published for tx=%s decision=%s score=%s",
            payload.get("transaction_id"),
            payload.get("decision"),
            payload.get("fraud_score"),
        )
        return True
    except KafkaError:
        logger.exception("Failed to publish decision for tx=%s", payload.get("transaction_id"))
        return False


def process_message(raw_message: bytes, producer: KafkaProducer) -> bool:
    try:
        payload = json.loads(raw_message.decode("utf-8"))
    except Exception:
        logger.exception("Invalid JSON payload. Skipping message.")
        return True

    tx_id = payload.get("transaction_id")
    if not tx_id:
        logger.warning("Payload without transaction_id: %s", payload)
        return True

    enriched = build_enriched_payload(payload)
    features_snapshot = enriched["transaction"]["features"]
    context_snapshot = enriched.get("context", {})

    try:
        result = score_with_retry(enriched)
        decision_payload = {
            "transaction_id": tx_id,
            "fraud_score": result.get("risk_score"),
            "decision": result.get("decision"),
            "reasons": result.get("reasons", []),
            "model_version": result.get("model_version"),
            "features_snapshot": features_snapshot,
            "context": context_snapshot,
            "created_at": now_iso(),
        }
    except Exception as exc:
        logger.exception("ML scoring failed for tx=%s", tx_id)
        decision_payload = build_fallback(
            tx_id, features_snapshot, context_snapshot, f"WORKER_ERROR: {exc}"
        )

    return publish_decision(producer, decision_payload)


def main():
    time.sleep(2)
    consumer = KafkaConsumer(
        TOPIC_IN,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda m: m,
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    logger.info(
        "Worker ready | bootstrap=%s in=%s out=%s ml=%s",
        KAFKA_BOOTSTRAP,
        TOPIC_IN,
        TOPIC_OUT,
        ML_ENGINE_URL,
    )

    for msg in consumer:
        success = process_message(msg.value, producer)
        if success:
            consumer.commit()
        else:
            logger.warning("Decision publish failed. Will retry after backoff.")
            time.sleep(1)


if __name__ == "__main__":
    main()

