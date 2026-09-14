from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.quality.models import CheckResult


class QualityRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    source_id: int
    schema_name: str = Field(serialization_alias='schema')
    table_name: str = Field(serialization_alias='table')
    overall_score: float
    completeness_score: float | None
    uniqueness_score: float | None
    validity_score: float | None
    created_at: datetime


class QualityRunDetail(QualityRunSummary):
    checks: list[CheckResult]
