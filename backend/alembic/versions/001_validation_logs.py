"""create validation_logs table

Revision ID: 001_validation_logs
Revises: 
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_validation_logs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create validation_logs table"""
    op.create_table(
        'validation_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('validation_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False),
        sa.Column('failed_records', sa.Integer(), nullable=False),
        sa.Column('pass_rate', sa.Float(), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('validator_name', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_validation_logs_id', 'validation_logs', ['id'])
    op.create_index('ix_validation_logs_dataset_name', 'validation_logs', ['dataset_name'])
    op.create_index('ix_validation_logs_validation_type', 'validation_logs', ['validation_type'])
    op.create_index('ix_validation_logs_status', 'validation_logs', ['status'])


def downgrade() -> None:
    """Drop validation_logs table"""
    op.drop_index('ix_validation_logs_status', table_name='validation_logs')
    op.drop_index('ix_validation_logs_validation_type', table_name='validation_logs')
    op.drop_index('ix_validation_logs_dataset_name', table_name='validation_logs')
    op.drop_index('ix_validation_logs_id', table_name='validation_logs')
    op.drop_table('validation_logs')
