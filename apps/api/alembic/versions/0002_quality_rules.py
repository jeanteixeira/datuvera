"""Persist dataset quality rules.

Revision ID: 0002_quality_rules
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0002_quality_rules'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('quality_rules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('schema_name', sa.String(), nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('column_name', sa.String(), nullable=False),
        sa.Column('rule_type', sa.String(), nullable=False),
        sa.Column('parameters', postgresql.JSONB(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_quality_rules_dataset', 'quality_rules', ['source_id', 'schema_name', 'table_name'])


def downgrade():
    op.drop_index('ix_quality_rules_dataset', table_name='quality_rules')
    op.drop_table('quality_rules')
