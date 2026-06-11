"""create freshness_metrics table

Revision ID: 006_freshness_metrics
Revises: 005_metrics
Create Date: 2026-06-11

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_freshness_metrics'
down_revision = '005_metrics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create freshness_metrics table"""
    op.create_table(
        'freshness_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('ingestion_timestamp', sa.DateTime(), nullable=False),
        sa.Column('validation_timestamp', sa.DateTime(), nullable=True),
        sa.Column('dataset_age_hours', sa.Float(), nullable=False),
        sa.Column('freshness_status', sa.String(length=50), nullable=False),
        sa.Column('freshness_threshold_hours', sa.Float(), nullable=False),
        sa.Column('ingestion_start_time', sa.DateTime(), nullable=True),
        sa.Column('ingestion_end_time', sa.DateTime(), nullable=True),
        sa.Column('ingestion_latency_seconds', sa.Float(), nullable=True),
        sa.Column('validation_start_time', sa.DateTime(), nullable=True),
        sa.Column('validation_end_time', sa.DateTime(), nullable=True),
        sa.Column('validation_latency_seconds', sa.Float(), nullable=True),
        sa.Column('sla_threshold_hours', sa.Float(), nullable=True),
        sa.Column('sla_status', sa.String(length=50), nullable=True),
        sa.Column('dag_id', sa.String(length=255), nullable=True),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_freshness_metrics_id', 'freshness_metrics', ['id'])
    op.create_index('ix_freshness_metrics_dataset_name', 'freshness_metrics', ['dataset_name'])
    op.create_index('ix_freshness_metrics_ingestion_timestamp', 'freshness_metrics', ['ingestion_timestamp'])
    op.create_index('ix_freshness_metrics_freshness_status', 'freshness_metrics', ['freshness_status'])
    op.create_index('ix_freshness_metrics_sla_status', 'freshness_metrics', ['sla_status'])
    
    # Create composite indexes for common query patterns
    op.create_index('idx_dataset_ingestion_timestamp', 'freshness_metrics', ['dataset_name', 'ingestion_timestamp'])
    op.create_index('idx_freshness_status_timestamp', 'freshness_metrics', ['freshness_status', 'ingestion_timestamp'])
    op.create_index('idx_sla_status_timestamp', 'freshness_metrics', ['sla_status', 'ingestion_timestamp'])


def downgrade() -> None:
    """Drop freshness_metrics table"""
    op.drop_index('idx_sla_status_timestamp', table_name='freshness_metrics')
    op.drop_index('idx_freshness_status_timestamp', table_name='freshness_metrics')
    op.drop_index('idx_dataset_ingestion_timestamp', table_name='freshness_metrics')
    op.drop_index('ix_freshness_metrics_sla_status', table_name='freshness_metrics')
    op.drop_index('ix_freshness_metrics_freshness_status', table_name='freshness_metrics')
    op.drop_index('ix_freshness_metrics_ingestion_timestamp', table_name='freshness_metrics')
    op.drop_index('ix_freshness_metrics_dataset_name', table_name='freshness_metrics')
    op.drop_index('ix_freshness_metrics_id', table_name='freshness_metrics')
    op.drop_table('freshness_metrics')
