from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base import Base


class QualityRun(Base):
    __tablename__ = 'quality_runs'
    __table_args__ = (Index('ix_quality_runs_dataset_created', 'source_id', 'schema_name', 'table_name', 'created_at'),)

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('data_sources.id', ondelete='CASCADE'), nullable=False)
    schema_name = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    overall_score = Column(Float, nullable=False)
    completeness_score = Column(Float, nullable=True)
    uniqueness_score = Column(Float, nullable=True)
    validity_score = Column(Float, nullable=True)
    checks = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
