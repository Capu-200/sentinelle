"""add_missing_user_columns

Revision ID: dd9a55d325e7
Revises: 7f64eef750d7
Create Date: 2026-01-26 16:15:24.879194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'dd9a55d325e7'
down_revision: Union[str, Sequence[str], None] = '7f64eef750d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # We removed op.drop_table for ai_decisions, etc. because we want to keep them.
    # They were missing from models.py but exist in DB.
    
    op.alter_column('transactions', 'amount',
               existing_type=sa.NUMERIC(precision=15, scale=2),
               nullable=False)
    op.alter_column('transactions', 'currency',
               existing_type=sa.VARCHAR(length=3),
               nullable=False)
    op.alter_column('transactions', 'transaction_type',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('transactions', 'direction',
               existing_type=sa.VARCHAR(length=10),
               nullable=False)
    op.alter_column('transactions', 'description',
               existing_type=sa.TEXT(),
               type_=sqlmodel.sql.sqltypes.AutoString(),
               existing_nullable=True)
    op.alter_column('transactions', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('transactions', 'kyc_status',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.drop_column('transactions', 'executed_at')
    op.drop_column('transactions', 'provider')
    op.drop_column('transactions', 'metadata_raw_payload')
    op.drop_column('transactions', 'reason_code')
    op.drop_column('transactions', 'provider_created_at')
    op.drop_column('transactions', 'provider_tx_id')
    op.add_column('users', sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.add_column('users', sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False))
    op.add_column('users', sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False))
    op.alter_column('users', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.drop_column('users', 'kyc_status')
    op.alter_column('wallets', 'currency',
               existing_type=sa.VARCHAR(length=3),
               nullable=False)
    op.alter_column('wallets', 'balance',
               existing_type=sa.NUMERIC(precision=15, scale=2),
               nullable=False)
    op.alter_column('wallets', 'kyc_status',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)
    op.alter_column('wallets', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('wallets', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('wallets', 'kyc_status',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('wallets', 'balance',
               existing_type=sa.NUMERIC(precision=15, scale=2),
               nullable=True)
    op.alter_column('wallets', 'currency',
               existing_type=sa.VARCHAR(length=3),
               nullable=True)
    op.add_column('users', sa.Column('kyc_status', sa.VARCHAR(length=20), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.alter_column('users', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'full_name')
    op.drop_column('users', 'email')
    
    # Re-adding columns dropped in upgrade
    op.add_column('transactions', sa.Column('provider_tx_id', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.add_column('transactions', sa.Column('provider_created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('transactions', sa.Column('reason_code', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('transactions', sa.Column('metadata_raw_payload', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('transactions', sa.Column('provider', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('transactions', sa.Column('executed_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    
    op.alter_column('transactions', 'kyc_status',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('transactions', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('transactions', 'description',
               existing_type=sqlmodel.sql.sqltypes.AutoString(),
               type_=sa.TEXT(),
               existing_nullable=True)
    op.alter_column('transactions', 'direction',
               existing_type=sa.VARCHAR(length=10),
               nullable=True)
    op.alter_column('transactions', 'transaction_type',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.alter_column('transactions', 'currency',
               existing_type=sa.VARCHAR(length=3),
               nullable=True)
    op.alter_column('transactions', 'amount',
               existing_type=sa.NUMERIC(precision=15, scale=2),
               nullable=True)
