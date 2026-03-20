import json
import logging
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

from .config import get_settings

settings = get_settings()
logger = logging.getLogger("kafka-producer")

_producer: Optional[KafkaProducer] = None


def _get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        logger.info(
            "Initialising Kafka producer bootstrap=%s", settings.kafka_bootstrap_servers
        )
        _producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            linger_ms=10,
            retries=5,
        )
    return _producer


def publish_transaction_request(payload: dict) -> None:
    """Publish a transaction request event to Kafka."""
    producer = _get_producer()
    future = producer.send(settings.kafka_topic_requests, payload)
    try:
        future.get(timeout=10)
        logger.info(
            "Published transaction request tx=%s topic=%s",
            payload.get("transaction_id"),
            settings.kafka_topic_requests,
        )
    except KafkaError as exc:
        logger.exception(
            "Failed to publish transaction request tx=%s", payload.get("transaction_id")
        )
        raise RuntimeError("Kafka publish failed") from exc

