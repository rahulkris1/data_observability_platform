"""create profiling_results table

Revision ID: 011_profiling_results
Revises: 010_users
Create Date: 2026-06-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_profiling_results'
down_revision = '010_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create profiling_results table for storing dataset profiling statistics"""
    op.create_table(
        'profiling_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('column_statistics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('column_distributions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('profiled_by', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for common queries
    op.create_index('ix_profiling_results_dataset_name', 'profiling_results', ['dataset_name'])
    op.create_index('ix_profiling_results_status', 'profiling_results', ['status'])


def downgrade() -> None:
    """Drop profiling_results table"""
    op.drop_index('ix_profiling_results_status', table_name='profiling_results')
    op.drop_index('ix_profiling_results_dataset_name', table_name='profiling_results')
    op.drop_table('profiling_results')
