from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Central application configuration loaded from environment variables."""

    log_level: str = Field("INFO", env="LOG_LEVEL")

    database_url: str = Field(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
        env="DATABASE_URL",
    )

    kafka_bootstrap_servers: str = Field(
        "localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS",
    )
    kafka_topic_requests: str = Field(
        "transaction.requests",
        env="KAFKA_TOPIC_REQUESTS",
    )

    ml_engine_health_url: str = Field(
        "http://localhost:8001/health",
        env="ML_ENGINE_HEALTH_URL",
    )

    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance to avoid repeated env parsing."""
    return Settings()

