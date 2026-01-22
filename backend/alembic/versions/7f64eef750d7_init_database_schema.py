"""init database schema

Revision ID: 7f64eef750d7
Revises: 
Create Date: 2026-01-21 14:46:16.109643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = '7f64eef750d7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Création des schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS auth;")
    op.execute("CREATE SCHEMA IF NOT EXISTS banking;")
    op.execute("CREATE SCHEMA IF NOT EXISTS fraud;")
    op.execute("CREATE SCHEMA IF NOT EXISTS ml;")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit;")
    
    # Table users
    op.execute("""
    CREATE TABLE auth.users (
        id UUID PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK (role IN ('ADMIN','CLIENT','SERVICE')),
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """)

    # Table accounts
    op.execute("""
    CREATE TABLE banking.accounts (
        id UUID PRIMARY KEY,
        user_id UUID REFERENCES auth.users(id),
        balance NUMERIC(14,2) NOT NULL,
        currency CHAR(3) NOT NULL,
        status TEXT CHECK (status IN ('ACTIVE','SUSPENDED')),
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """)

    # Table transactions
    op.execute("""
    CREATE TABLE banking.transactions (
        id UUID PRIMARY KEY,
        account_id UUID REFERENCES banking.accounts(id),
        amount NUMERIC(14,2) NOT NULL,
        currency CHAR(3) NOT NULL,
        merchant_id TEXT,
        merchant_country CHAR(2),
        payment_method TEXT,
        status TEXT CHECK (status IN ('PENDING','APPROVED','BLOCKED')),
        occurred_at TIMESTAMPTZ NOT NULL
    );
    """)

    # Table fraud predictions
    op.execute("""
    CREATE TABLE fraud.predictions (
        id UUID PRIMARY KEY,
        transaction_id UUID REFERENCES banking.transactions(id),
        fraud_score NUMERIC(5,4) CHECK (fraud_score BETWEEN 0 AND 1),
        decision TEXT CHECK (decision IN ('ALLOW','REVIEW','BLOCK')),
        model_version TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """)

def downgrade():
    # Supprimer les tables dans l'ordre inverse pour éviter les FK
    op.execute("DROP TABLE IF EXISTS fraud.predictions;")
    op.execute("DROP TABLE IF EXISTS banking.transactions;")
    op.execute("DROP TABLE IF EXISTS banking.accounts;")
    op.execute("DROP TABLE IF EXISTS auth.users;")
    
    # Supprimer les schemas
    op.execute("DROP SCHEMA IF EXISTS fraud CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS banking CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS auth CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS ml CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS audit CASCADE;")
