"""
Database connection configuration
Supports both local Docker and Google Cloud SQL
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://fraud_user:fraud_pwd@localhost:5432/fraud_db"
)

# For Cloud SQL, we use Unix socket connection when running on Cloud Run
# Format: postgresql+psycopg2://USER:PASSWORD@/DATABASE?host=/cloudsql/INSTANCE_CONNECTION_NAME
# For local development with Cloud SQL Auth Proxy, use: postgresql+psycopg2://USER:PASSWORD@127.0.0.1:5432/DATABASE

# Create engine
# Use NullPool for serverless (Cloud Run) to avoid connection pool issues
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Important for Cloud Run
    echo=False  # Set to True for SQL query debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

