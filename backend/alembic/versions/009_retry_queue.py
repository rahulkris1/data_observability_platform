"""create retry_queue table

Revision ID: 009_retry_queue
Revises: 008_failed_loads_audit
Create Date: 2026-06-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_retry_queue'
down_revision = '008_failed_loads_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create retry_queue table for tracking validation retry requests"""
    op.create_table(
        'retry_queue',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('validation_log_id', sa.Integer(), nullable=False),
        sa.Column('retry_status', sa.String(length=50), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('initiated_by', sa.String(length=255), nullable=False),
        sa.Column('retry_reason', sa.Text(), nullable=True),
        sa.Column('last_retry_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['validation_log_id'], ['validation_logs.id'], ondelete='CASCADE')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_retry_queue_id', 'retry_queue', ['id'])
    op.create_index('ix_retry_queue_validation_log_id', 'retry_queue', ['validation_log_id'])
    op.create_index('ix_retry_queue_retry_status', 'retry_queue', ['retry_status'])


def downgrade() -> None:
    """Drop retry_queue table"""
    op.drop_index('ix_retry_queue_retry_status', table_name='retry_queue')
    op.drop_index('ix_retry_queue_validation_log_id', table_name='retry_queue')
    op.drop_index('ix_retry_queue_id', table_name='retry_queue')
    op.drop_table('retry_queue')
