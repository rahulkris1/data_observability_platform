"""create schema_versions and schema_drift_history tables

Revision ID: 012_schema_versions
Revises: 011_profiling_results
Create Date: 2026-06-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_schema_versions'
down_revision = '011_profiling_results'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create schema_versions and schema_drift_history tables"""
    
    # Create schema_versions table
    op.create_table(
        'schema_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_hash', sa.String(length=64), nullable=False),
        sa.Column('schema_definition', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),  # e.g., 'ingestion', 'validation', 'manual'
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_schema_versions_dataset_name', 'schema_versions', ['dataset_name'])
    op.create_index('ix_schema_versions_version_hash', 'schema_versions', ['version_hash'])
    op.create_index('ix_schema_versions_detected_at', 'schema_versions', ['detected_at'])
    op.create_index('ix_schema_versions_dataset_version', 'schema_versions', ['dataset_name', 'version_number'], unique=True)
    
    # Create schema_drift_history table
    op.create_table(
        'schema_drift_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('dataset_name', sa.String(length=255), nullable=False),
        sa.Column('previous_version_id', sa.Integer(), nullable=True),
        sa.Column('current_version_id', sa.Integer(), nullable=False),
        sa.Column('drift_type', sa.String(length=50), nullable=False),  # 'column_added', 'column_removed', 'type_changed', 'nullability_changed'
        sa.Column('severity', sa.String(length=20), nullable=False),  # 'info', 'warning', 'critical'
        sa.Column('changes', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, default=False),
        sa.Column('acknowledged_by', sa.String(length=255), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['previous_version_id'], ['schema_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['current_version_id'], ['schema_versions.id'], ondelete='CASCADE')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_schema_drift_history_dataset_name', 'schema_drift_history', ['dataset_name'])
    op.create_index('ix_schema_drift_history_detected_at', 'schema_drift_history', ['detected_at'])
    op.create_index('ix_schema_drift_history_severity', 'schema_drift_history', ['severity'])
    op.create_index('ix_schema_drift_history_acknowledged', 'schema_drift_history', ['acknowledged'])


def downgrade() -> None:
    """Drop schema_versions and schema_drift_history tables"""
    # Drop schema_drift_history table first due to foreign key constraints
    op.drop_index('ix_schema_drift_history_acknowledged', table_name='schema_drift_history')
    op.drop_index('ix_schema_drift_history_severity', table_name='schema_drift_history')
    op.drop_index('ix_schema_drift_history_detected_at', table_name='schema_drift_history')
    op.drop_index('ix_schema_drift_history_dataset_name', table_name='schema_drift_history')
    op.drop_table('schema_drift_history')
    
    # Drop schema_versions table
    op.drop_index('ix_schema_versions_dataset_version', table_name='schema_versions')
    op.drop_index('ix_schema_versions_detected_at', table_name='schema_versions')
    op.drop_index('ix_schema_versions_version_hash', table_name='schema_versions')
    op.drop_index('ix_schema_versions_dataset_name', table_name='schema_versions')
    op.drop_table('schema_versions')
