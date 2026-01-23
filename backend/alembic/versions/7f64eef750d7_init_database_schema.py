"""init database schema

Revision ID: 7f64eef750d7
Revises: 
Create Date: 2026-01-21 14:46:16.109643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f64eef750d7'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Table USERS (Pas de dépendance)
    op.execute("""
    CREATE TABLE users (
        user_id VARCHAR(50) PRIMARY KEY,
        display_name VARCHAR(100),
        created_at TIMESTAMP,
        risk_level VARCHAR(20),
        kyc_status VARCHAR(20),
        country_home VARCHAR(5),
        trust_score INT,
        last_risk_update_at TIMESTAMP
    );
    """)

    # 2. Table WALLETS (Dépend de Users)
    op.execute("""
    CREATE TABLE wallets (
        wallet_id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(50) REFERENCES users(user_id),
        currency VARCHAR(3),
        balance NUMERIC(15, 2),
        kyc_status VARCHAR(20),
        updated_at TIMESTAMP,
        last_transaction_at TIMESTAMP
    );
    """)

    # 3. Table TRANSACTIONS (Dépend de Users et Wallets)
    op.execute("""
    CREATE TABLE transactions (
        transaction_id VARCHAR(50) PRIMARY KEY,
        created_at TIMESTAMP,
        provider_created_at TIMESTAMP,
        executed_at TIMESTAMP,
        provider VARCHAR(50),
        provider_tx_id VARCHAR(100),
        initiator_user_id VARCHAR(50) REFERENCES users(user_id),
        source_wallet_id VARCHAR(50) REFERENCES wallets(wallet_id),
        destination_wallet_id VARCHAR(50) REFERENCES wallets(wallet_id),
        amount NUMERIC(15, 2),
        currency VARCHAR(3),
        transaction_type VARCHAR(20),
        direction VARCHAR(10),
        country VARCHAR(5),
        city VARCHAR(100),
        description TEXT,
        kyc_status VARCHAR(20),
        reason_code VARCHAR(50),
        metadata_raw_payload JSONB
    );
    """)

    # 4. Table WALLET_LEDGER (Dépend de Transactions et Wallets)
    op.execute("""
    CREATE TABLE wallet_ledger (
        ledger_id VARCHAR(50) PRIMARY KEY,
        wallet_id VARCHAR(50) REFERENCES wallets(wallet_id),
        transaction_id VARCHAR(50) REFERENCES transactions(transaction_id),
        entry_type VARCHAR(10),
        amount NUMERIC(15, 2),
        balance_after NUMERIC(15, 2),
        executed_at TIMESTAMP,
        created_at TIMESTAMP
    );
    """)

    # 5. Table AI_DECISIONS (Dépend de Transactions)
    op.execute("""
    CREATE TABLE ai_decisions (
        decision_id VARCHAR(50) PRIMARY KEY,
        transaction_id VARCHAR(50) REFERENCES transactions(transaction_id),
        fraud_score NUMERIC(5, 4),
        decision VARCHAR(20),
        reasons VARCHAR(100),
        model_version VARCHAR(20),
        latency_ms INT,
        threshold_used NUMERIC(5, 4),
        features_snapshot JSONB,
        created_at TIMESTAMP
    );
    """)

    # 6. Table HUMAN_REVIEWS (Dépend de Transactions)
    op.execute("""
    CREATE TABLE human_reviews (
        review_id VARCHAR(50) PRIMARY KEY,
        transaction_id VARCHAR(50) REFERENCES transactions(transaction_id),
        analyst_id VARCHAR(50),
        action VARCHAR(20),
        label VARCHAR(20),
        comment TEXT,
        final_status VARCHAR(20),
        created_at TIMESTAMP
    );
    """)

def downgrade():
    # Supprimer les tables dans l'ordre inverse pour éviter les FK
    op.execute("DROP TABLE IF EXISTS human_reviews;")
    op.execute("DROP TABLE IF EXISTS ai_decisions;")
    op.execute("DROP TABLE IF EXISTS wallet_ledger;")
    op.execute("DROP TABLE IF EXISTS transactions;")
    op.execute("DROP TABLE IF EXISTS wallets;")
    op.execute("DROP TABLE IF EXISTS users;")
