"""create schema_contracts table

Revision ID: 002_schema_contracts
Revises: 001_validation_logs
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_schema_contracts'
down_revision = '001_validation_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create schema_contracts table"""
    op.create_table(
        'schema_contracts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('schema_definition', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_schema_contracts_name', 'schema_contracts', ['name'])
    op.create_index('ix_schema_contracts_dataset_name', 'schema_contracts', ['dataset_name'])


def downgrade() -> None:
    """Drop schema_contracts table"""
    op.drop_index('ix_schema_contracts_dataset_name', table_name='schema_contracts')
    op.drop_index('ix_schema_contracts_name', table_name='schema_contracts')
    op.drop_table('schema_contracts')
