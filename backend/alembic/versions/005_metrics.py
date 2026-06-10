"""create metrics table

Revision ID: 005_metrics
Revises: 004_dag_executions
Create Date: 2026-06-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_metrics'
down_revision = '004_dag_executions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create metrics table"""
    op.create_table(
        'metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('metric_name', sa.String(length=255), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('execution_time', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=True),
        sa.Column('validation_type', sa.String(length=100), nullable=True),
        sa.Column('dag_id', sa.String(length=255), nullable=True),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_metrics_id', 'metrics', ['id'])
    op.create_index('ix_metrics_metric_name', 'metrics', ['metric_name'])
    op.create_index('ix_metrics_metric_type', 'metrics', ['metric_type'])
    op.create_index('ix_metrics_timestamp', 'metrics', ['timestamp'])
    op.create_index('ix_metrics_dataset_name', 'metrics', ['dataset_name'])
    op.create_index('ix_metrics_validation_type', 'metrics', ['validation_type'])
    
    # Create composite indexes for common query patterns
    op.create_index('idx_metric_name_timestamp', 'metrics', ['metric_name', 'timestamp'])
    op.create_index('idx_dataset_timestamp', 'metrics', ['dataset_name', 'timestamp'])
    op.create_index('idx_validation_type_timestamp', 'metrics', ['validation_type', 'timestamp'])


def downgrade() -> None:
    """Drop metrics table"""
    op.drop_index('idx_validation_type_timestamp', table_name='metrics')
    op.drop_index('idx_dataset_timestamp', table_name='metrics')
    op.drop_index('idx_metric_name_timestamp', table_name='metrics')
    op.drop_index('ix_metrics_validation_type', table_name='metrics')
    op.drop_index('ix_metrics_dataset_name', table_name='metrics')
    op.drop_index('ix_metrics_timestamp', table_name='metrics')
    op.drop_index('ix_metrics_metric_type', table_name='metrics')
    op.drop_index('ix_metrics_metric_name', table_name='metrics')
    op.drop_index('ix_metrics_id', table_name='metrics')
    op.drop_table('metrics')
