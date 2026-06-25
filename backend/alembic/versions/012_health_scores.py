"""create health_scores table

Revision ID: 012_health_scores
Revises: 011_profiling_results
Create Date: 2026-06-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_health_scores'
down_revision = '011_profiling_results'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create health_scores table"""
    op.create_table(
        'health_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('pipeline_name', sa.String(length=255), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('validation_score', sa.Float(), nullable=False),
        sa.Column('freshness_score', sa.Float(), nullable=False),
        sa.Column('latency_score', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('validation_pass_rate', sa.Float(), nullable=True),
        sa.Column('freshness_violations', sa.Float(), nullable=True),
        sa.Column('avg_latency_seconds', sa.Float(), nullable=True),
        sa.Column('total_validations', sa.Float(), nullable=True),
        sa.Column('passed_validations', sa.Float(), nullable=True),
        sa.Column('failed_validations', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('score_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_health_scores_id', 'health_scores', ['id'])
    op.create_index('ix_health_scores_pipeline_name', 'health_scores', ['pipeline_name'])
    op.create_index('ix_health_scores_timestamp', 'health_scores', ['timestamp'])
    op.create_index('ix_health_scores_status', 'health_scores', ['status'])
    op.create_index('idx_pipeline_timestamp', 'health_scores', ['pipeline_name', 'timestamp'])
    op.create_index('idx_status_timestamp', 'health_scores', ['status', 'timestamp'])
    op.create_index('idx_overall_score', 'health_scores', ['overall_score'])


def downgrade() -> None:
    """Drop health_scores table"""
    op.drop_index('idx_overall_score', 'health_scores')
    op.drop_index('idx_status_timestamp', 'health_scores')
    op.drop_index('idx_pipeline_timestamp', 'health_scores')
    op.drop_index('ix_health_scores_status', 'health_scores')
    op.drop_index('ix_health_scores_timestamp', 'health_scores')
    op.drop_index('ix_health_scores_pipeline_name', 'health_scores')
    op.drop_index('ix_health_scores_id', 'health_scores')
    op.drop_table('health_scores')
