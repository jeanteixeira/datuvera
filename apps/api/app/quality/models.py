from pydantic import BaseModel, Field
from app.quality.types import RuleType
from typing import List, Optional, Any, Dict, Literal


class CheckResult(BaseModel):
    column: Optional[str] = None
    columns: Optional[List[str]] = None
    rule: RuleType
    status: Literal['passed', 'warning', 'failed']
    passed: bool
    failed_count: int
    failed_percentage: float
    score: float = Field(ge=0, le=100)
    message: Optional[str]


class DimensionResult(BaseModel):
    name: str
    score: float
    checks: List[CheckResult] = []


class QualityResult(BaseModel):
    dataset: Dict[str, Any]
    score: float
    dimensions: Dict[str, Optional[float]]
    summary: Dict[str, int]
    checks: List[CheckResult]
