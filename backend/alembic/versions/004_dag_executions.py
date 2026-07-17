"""Create DAG executions table

Revision ID: 004
Revises: 003
Create Date: 2026-06-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create dag_executions table"""
    op.create_table(
        'dag_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dag_id', sa.String(length=255), nullable=False),
        sa.Column('dag_run_id', sa.String(length=255), nullable=False),
        sa.Column('execution_date', sa.DateTime(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('run_type', sa.String(length=50), nullable=True),
        sa.Column('total_tasks', sa.Integer(), nullable=True, default=0),
        sa.Column('completed_tasks', sa.Integer(), nullable=True, default=0),
        sa.Column('failed_tasks', sa.Integer(), nullable=True, default=0),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('conf', JSON(), nullable=True),
        sa.Column('task_details', JSON(), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for common queries
    op.create_index('ix_dag_executions_dag_id', 'dag_executions', ['dag_id'])
    op.create_index('ix_dag_executions_dag_run_id', 'dag_executions', ['dag_run_id'], unique=True)
    op.create_index('ix_dag_executions_execution_date', 'dag_executions', ['execution_date'])
    op.create_index('ix_dag_executions_state', 'dag_executions', ['state'])


def downgrade() -> None:
    """Drop dag_executions table"""
    op.drop_index('ix_dag_executions_state', table_name='dag_executions')
    op.drop_index('ix_dag_executions_execution_date', table_name='dag_executions')
    op.drop_index('ix_dag_executions_dag_run_id', table_name='dag_executions')
    op.drop_index('ix_dag_executions_dag_id', table_name='dag_executions')
    op.drop_table('dag_executions')
