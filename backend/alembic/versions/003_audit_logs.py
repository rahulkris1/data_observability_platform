"""create audit_logs table

Revision ID: 003_audit_logs
Revises: 002_schema_contracts
Create Date: 2026-06-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_audit_logs'
down_revision = '002_schema_contracts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create audit_logs table"""
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('validation_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('total_records', sa.Integer(), nullable=False),
        sa.Column('failed_records', sa.Integer(), nullable=False),
        sa.Column('pass_rate', sa.Float(), nullable=False),
        sa.Column('validator_name', sa.String(length=255), nullable=False),
        sa.Column('triggered_by', sa.String(length=100), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_dataset_name', 'audit_logs', ['dataset_name'])
    op.create_index('ix_audit_logs_validation_type', 'audit_logs', ['validation_type'])
    op.create_index('ix_audit_logs_status', 'audit_logs', ['status'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    """Drop audit_logs table"""
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_status', table_name='audit_logs')
    op.drop_index('ix_audit_logs_validation_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_dataset_name', table_name='audit_logs')
    op.drop_index('ix_audit_logs_id', table_name='audit_logs')
    op.drop_table('audit_logs')
