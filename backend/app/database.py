"""
Database connection configuration
Supports both local Docker and Google Cloud SQL.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .config import get_settings

settings = get_settings()

# Create engine (NullPool avoids keeping idle connections on Cloud Run)
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
