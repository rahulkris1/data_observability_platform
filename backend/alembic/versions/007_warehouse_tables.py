"""create warehouse tables

Revision ID: 007_warehouse_tables
Revises: 006_freshness_metrics
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_warehouse_tables'
down_revision = '006_freshness_metrics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create warehouse tables"""
    
    # Create warehouse_staging_data table
    op.create_table(
        'warehouse_staging_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('batch_id', sa.String(length=100), nullable=False),
        sa.Column('source_system', sa.String(length=255), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('record_hash', sa.String(length=64), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for warehouse_staging_data
    op.create_index('ix_warehouse_staging_data_id', 'warehouse_staging_data', ['id'])
    op.create_index('ix_warehouse_staging_data_dataset_name', 'warehouse_staging_data', ['dataset_name'])
    op.create_index('ix_warehouse_staging_data_batch_id', 'warehouse_staging_data', ['batch_id'])
    op.create_index('ix_warehouse_staging_data_record_hash', 'warehouse_staging_data', ['record_hash'])
    op.create_index('ix_warehouse_staging_data_is_processed', 'warehouse_staging_data', ['is_processed'])
    
    # Create warehouse_processed_data table
    op.create_table(
        'warehouse_processed_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('batch_id', sa.String(length=100), nullable=False),
        sa.Column('source_system', sa.String(length=255), nullable=True),
        sa.Column('source_record_id', sa.String(length=255), nullable=True),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('record_hash', sa.String(length=64), nullable=True),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=True),
        sa.Column('load_timestamp', sa.DateTime(), nullable=False),
        sa.Column('partition_key', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('record_hash')
    )
    
    # Create indexes for warehouse_processed_data
    op.create_index('ix_warehouse_processed_data_id', 'warehouse_processed_data', ['id'])
    op.create_index('ix_warehouse_processed_data_dataset_name', 'warehouse_processed_data', ['dataset_name'])
    op.create_index('ix_warehouse_processed_data_batch_id', 'warehouse_processed_data', ['batch_id'])
    op.create_index('ix_warehouse_processed_data_source_record_id', 'warehouse_processed_data', ['source_record_id'])
    op.create_index('ix_warehouse_processed_data_record_hash', 'warehouse_processed_data', ['record_hash'])
    op.create_index('ix_warehouse_processed_data_validation_status', 'warehouse_processed_data', ['validation_status'])
    op.create_index('ix_warehouse_processed_data_load_timestamp', 'warehouse_processed_data', ['load_timestamp'])
    op.create_index('ix_warehouse_processed_data_partition_key', 'warehouse_processed_data', ['partition_key'])
    
    # Create warehouse_load_history table
    op.create_table(
        'warehouse_load_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('batch_id', sa.String(length=100), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('source_system', sa.String(length=255), nullable=True),
        sa.Column('load_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('records_attempted', sa.Integer(), nullable=False),
        sa.Column('records_loaded', sa.Integer(), nullable=False),
        sa.Column('records_failed', sa.Integer(), nullable=False),
        sa.Column('records_duplicate', sa.Integer(), nullable=False),
        sa.Column('execution_duration_ms', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_summary', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('load_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_id')
    )
    
    # Create indexes for warehouse_load_history
    op.create_index('ix_warehouse_load_history_id', 'warehouse_load_history', ['id'])
    op.create_index('ix_warehouse_load_history_batch_id', 'warehouse_load_history', ['batch_id'])
    op.create_index('ix_warehouse_load_history_dataset_name', 'warehouse_load_history', ['dataset_name'])
    op.create_index('ix_warehouse_load_history_load_type', 'warehouse_load_history', ['load_type'])
    op.create_index('ix_warehouse_load_history_status', 'warehouse_load_history', ['status'])
    op.create_index('ix_warehouse_load_history_started_at', 'warehouse_load_history', ['started_at'])


def downgrade() -> None:
    """Drop warehouse tables"""
    
    # Drop warehouse_load_history indexes and table
    op.drop_index('ix_warehouse_load_history_started_at', table_name='warehouse_load_history')
    op.drop_index('ix_warehouse_load_history_status', table_name='warehouse_load_history')
    op.drop_index('ix_warehouse_load_history_load_type', table_name='warehouse_load_history')
    op.drop_index('ix_warehouse_load_history_dataset_name', table_name='warehouse_load_history')
    op.drop_index('ix_warehouse_load_history_batch_id', table_name='warehouse_load_history')
    op.drop_index('ix_warehouse_load_history_id', table_name='warehouse_load_history')
    op.drop_table('warehouse_load_history')
    
    # Drop warehouse_processed_data indexes and table
    op.drop_index('ix_warehouse_processed_data_partition_key', table_name='warehouse_processed_data')
    op.drop_index('ix_warehouse_processed_data_load_timestamp', table_name='warehouse_processed_data')
    op.drop_index('ix_warehouse_processed_data_validation_status', table_name='warehouse_processed_data')
    op.drop_index('ix_warehouse_processed_data_record_hash', table_name='warehouse_processed_data')
    op.drop_index('ix_warehouse_processed_data_source_record_id', table_name='warehouse_processed_data')
    op.drop_index('ix_warehouse_processed_data_batch_id', table_name='warehouse_processed_data')
    op.drop_index('ix_warehouse_processed_data_dataset_name', table_name='warehouse_processed_data')
    op.drop_index('ix_warehouse_processed_data_id', table_name='warehouse_processed_data')
    op.drop_table('warehouse_processed_data')
    
    # Drop warehouse_staging_data indexes and table
    op.drop_index('ix_warehouse_staging_data_is_processed', table_name='warehouse_staging_data')
    op.drop_index('ix_warehouse_staging_data_record_hash', table_name='warehouse_staging_data')
    op.drop_index('ix_warehouse_staging_data_batch_id', table_name='warehouse_staging_data')
    op.drop_index('ix_warehouse_staging_data_dataset_name', table_name='warehouse_staging_data')
    op.drop_index('ix_warehouse_staging_data_id', table_name='warehouse_staging_data')
    op.drop_table('warehouse_staging_data')
