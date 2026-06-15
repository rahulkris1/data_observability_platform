"""create failed loads and load audit tables

Revision ID: 008_failed_loads_audit
Revises: 007_warehouse_tables
Create Date: 2026-06-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_failed_loads_audit'
down_revision = '007_warehouse_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create failed_loads and load_audit_logs tables"""
    
    # Create failed_loads table
    op.create_table(
        'failed_loads',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('batch_id', sa.String(length=100), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('source_system', sa.String(length=255), nullable=True),
        sa.Column('load_started_at', sa.DateTime(), nullable=True),
        sa.Column('load_failed_at', sa.DateTime(), nullable=False),
        sa.Column('failure_reason', sa.String(length=500), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('source_record_count', sa.Integer(), nullable=True),
        sa.Column('warehouse_record_count', sa.Integer(), nullable=True),
        sa.Column('failed_record_count', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('can_retry', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('retry_validated_at', sa.DateTime(), nullable=True),
        sa.Column('retry_validated_by', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_id')
    )
    
    # Create indexes for failed_loads
    op.create_index('ix_failed_loads_id', 'failed_loads', ['id'])
    op.create_index('ix_failed_loads_batch_id', 'failed_loads', ['batch_id'])
    op.create_index('ix_failed_loads_dataset_name', 'failed_loads', ['dataset_name'])
    
    # Create load_audit_logs table
    op.create_table(
        'load_audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('batch_id', sa.String(length=100), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('source_system', sa.String(length=255), nullable=True),
        sa.Column('load_status', sa.String(length=50), nullable=False),
        sa.Column('load_started_at', sa.DateTime(), nullable=False),
        sa.Column('load_completed_at', sa.DateTime(), nullable=True),
        sa.Column('source_record_count', sa.Integer(), nullable=True),
        sa.Column('warehouse_record_count', sa.Integer(), nullable=True),
        sa.Column('records_inserted', sa.Integer(), nullable=True),
        sa.Column('records_updated', sa.Integer(), nullable=True),
        sa.Column('records_failed', sa.Integer(), nullable=True),
        sa.Column('execution_time_seconds', sa.Integer(), nullable=True),
        sa.Column('triggered_by', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for load_audit_logs
    op.create_index('ix_load_audit_logs_id', 'load_audit_logs', ['id'])
    op.create_index('ix_load_audit_logs_batch_id', 'load_audit_logs', ['batch_id'])
    op.create_index('ix_load_audit_logs_dataset_name', 'load_audit_logs', ['dataset_name'])
    op.create_index('ix_load_audit_logs_load_status', 'load_audit_logs', ['load_status'])


def downgrade() -> None:
    """Drop failed_loads and load_audit_logs tables"""
    
    # Drop indexes for load_audit_logs
    op.drop_index('ix_load_audit_logs_load_status', table_name='load_audit_logs')
    op.drop_index('ix_load_audit_logs_dataset_name', table_name='load_audit_logs')
    op.drop_index('ix_load_audit_logs_batch_id', table_name='load_audit_logs')
    op.drop_index('ix_load_audit_logs_id', table_name='load_audit_logs')
    
    # Drop load_audit_logs table
    op.drop_table('load_audit_logs')
    
    # Drop indexes for failed_loads
    op.drop_index('ix_failed_loads_dataset_name', table_name='failed_loads')
    op.drop_index('ix_failed_loads_batch_id', table_name='failed_loads')
    op.drop_index('ix_failed_loads_id', table_name='failed_loads')
    
    # Drop failed_loads table
    op.drop_table('failed_loads')
