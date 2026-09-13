from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base


class DatasetQualityRule(Base):
    __tablename__ = 'quality_rules'
    __table_args__ = (Index('ix_quality_rules_dataset', 'source_id', 'schema_name', 'table_name'),)

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False)
    schema_name = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    column_name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)
    parameters = Column(JSONB, nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True, server_default='true')
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
