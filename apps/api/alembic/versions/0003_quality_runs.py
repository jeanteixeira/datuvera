"""Persist immutable quality result snapshots."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003_quality_runs'
down_revision = '0002_quality_rules'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('quality_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schema_name', sa.String(), nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('uniqueness_score', sa.Float(), nullable=True),
        sa.Column('validity_score', sa.Float(), nullable=True),
        sa.Column('checks', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_quality_runs_dataset_created', 'quality_runs', ['source_id', 'schema_name', 'table_name', 'created_at'])


def downgrade():
    op.drop_index('ix_quality_runs_dataset_created', table_name='quality_runs')
    op.drop_table('quality_runs')
