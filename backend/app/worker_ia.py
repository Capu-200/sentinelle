import os
import json
import time
import requests
from kafka import KafkaConsumer, KafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL")

TOPIC_IN = "transaction.requests"
TOPIC_OUT = "transaction.decisions"

def build_enriched_payload(tx: dict) -> dict:
    """
    MVP: si on ne sait pas calculer les 50 features historiques,
    on envoie un format enrichi minimal (new user) accepté par le ML engine.
    """
    # Champs transaction de base
    transaction = {
        "transaction_id": tx.get("transaction_id"),
        "amount": float(tx.get("amount", 0)),
        "currency": tx.get("currency", "PAY"),
        "source_wallet_id": tx.get("source_wallet_id", "unknown"),
        "destination_wallet_id": tx.get("destination_wallet_id", "unknown"),
        "transaction_type": tx.get("transaction_type", "TRANSFER"),
        "direction": tx.get("direction", "outgoing"),
        "created_at": tx.get("created_at"),
        "country": tx.get("country", "FR"),
        "features": {
            "transactional": {
                "amount": float(tx.get("amount", 0)),
                "log_amount": 0.0,
                "currency_is_pyc": (tx.get("currency") == "PYC"),
                "direction_outgoing": 1,
                "hour_of_day": 12,
                "day_of_week": 1,
                "transaction_type_TRANSFER": 1
            },
            "historical": {
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
                "src_failed_ratio_7d": 0.0
            }
        }
    }

    context = tx.get("context") or {
        "source_wallet": {"balance": 0.0, "status": "active"},
        "user": {"status": "active", "risk_level": "low"}
    }

    return {"transaction": transaction, "context": context}

def call_ml_engine(payload: dict) -> dict:
    r = requests.post(ML_ENGINE_URL, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()

def main():
    if not ML_ENGINE_URL:
        raise RuntimeError("ML_ENGINE_URL is not set")

    consumer = KafkaConsumer(
        TOPIC_IN,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="ia-worker",
    )

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"[IA-WORKER] Listening on {TOPIC_IN} ...")

    for msg in consumer:
        tx = msg.value
        tx_id = tx.get("transaction_id")
        try:
            enriched = build_enriched_payload(tx)
            result = call_ml_engine(enriched)

            out = {
                "transaction_id": tx_id,
                "decision": result.get("decision"),
                "risk_score": result.get("risk_score"),
                "reasons": result.get("reasons", []),
                "model_version": result.get("model_version"),
                "scored_at": time.time(),
            }

            producer.send(TOPIC_OUT, out)
            producer.flush()
            print(f"[IA-WORKER] Scored tx={tx_id} -> {out['decision']} ({out['risk_score']})")

        except Exception as e:
            # En MVP: on publie quand même une décision REVIEW en cas d'erreur
            out = {
                "transaction_id": tx_id,
                "decision": "REVIEW",
                "risk_score": 0.5,
                "reasons": [f"worker_error:{type(e).__name__}"],
                "model_version": "unknown",
                "scored_at": time.time(),
            }
            producer.send(TOPIC_OUT, out)
            producer.flush()
            print(f"[IA-WORKER] ERROR tx={tx_id} -> REVIEW (fallback). Error={e}")

if __name__ == "__main__":
    main()
