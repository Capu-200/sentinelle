import requests
import json
import datetime

ML_ENGINE_URL = "https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app"

payload = {
    "schema_version": "1.0.0",
    "transaction": {
        "transaction_id": "debug_test_001",
        "amount": 350.0,
        "currency": "PYC",
        "source_wallet_id": "test_src",
        "destination_wallet_id": "test_dest",
        "transaction_type": "TRANSFER",
        "direction": "OUTGOING",
        "created_at": datetime.datetime.utcnow().isoformat(),
        "country": "FR",
        "description": "Test debug",
        "initiator_user_id": "test_user",
        "kyc_status": "PENDING"
    },
    "context": {
        "source_wallet": {
            "balance": 1000.0,
            "status": "ACTIVE"
        },
        "user": {"status": "ACTIVE", "risk_level": "LOW"},
        "destination_wallet": {"status": "ACTIVE"},
    },
    "features": {
        "transactional": {
            "amount": 350.0,
            "log_amount": 5.86,
            "currency_is_pyc": 1,
            "direction_outgoing": 1,
            "hour_of_day": 14,
            "day_of_week": 1,
            "transaction_type_TRANSFER": 1
        },
        "historical": {
            # Dummy historical features as used in main.py defaults or similar
            "src_tx_count_out_5m": 0,
            "src_tx_count_out_1h": 0,
            "src_tx_count_out_24h": 0,
            "src_tx_count_out_7d": 0,
            "src_tx_amount_sum_out_1h": 0,
            "src_tx_amount_mean_out_7d": 0,
            "src_tx_amount_max_out_7d": 0,
            "src_unique_destinations_24h": 0,
            "is_new_destination_30d": 1,
            "src_to_dst_tx_count_30d": 0,
            "days_since_last_src_to_dst": -1,
            "src_destination_concentration_7d": 0,
            "src_destination_entropy_7d": 0,
            "is_new_country_30d": 0,
            "country_mismatch": 0,
            "src_failed_count_24h": 0,
            "src_failed_ratio_7d": 0
        }
    }
}

print(f"Sending payload to {ML_ENGINE_URL}/score...")
try:
    resp = requests.post(f"{ML_ENGINE_URL}/score", json=payload, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Response Body: {resp.text}")
except Exception as e:
    print(f"Exception: {e}")
