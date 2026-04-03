"""
Application settings loaded from environment variables.
"""
import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql+psycopg2://fraud_user:fraud_pwd@localhost:5432/fraud_db",
        alias="DATABASE_URL",
    )

    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        alias="KAFKA_BOOTSTRAP_SERVERS",
    )
    kafka_topic_requests: str = Field(
        default="transaction.requests",
        alias="KAFKA_TOPIC_REQUESTS",
    )
    kafka_topic_decisions: str = Field(
        default="transaction.decisions",
        alias="KAFKA_TOPIC_DECISIONS",
    )

    # ML Engine
    ml_engine_url: str = Field(
        default="https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app",
        alias="ML_ENGINE_URL",
    )
    ml_engine_health_url: str = Field(
        default="https://sentinelle-ml-engine-v2-ntqku76mya-ew.a.run.app/health",
        alias="ML_ENGINE_HEALTH_URL",
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        extra = "ignore"
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
