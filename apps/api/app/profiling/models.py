from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class ColumnTopValue(BaseModel):
    value: Any
    count: int


class ColumnProfile(BaseModel):
    name: str
    data_type: str
    nullable: bool
    null_count: int
    null_percentage: float
    distinct_count: int
    distinct_percentage: float
    min: Optional[Any] = None
    max: Optional[Any] = None
    mean: Optional[float] = None
    stddev: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    true_count: Optional[int] = None
    false_count: Optional[int] = None
    top_values: Optional[List[ColumnTopValue]] = None


class DatasetProfile(BaseModel):
    source_id: int
    schema: str
    table: str
    row_count: int
    column_count: int
    estimated_size_bytes: Optional[int]
    generated_at: datetime


class ProfileResponse(BaseModel):
    dataset: DatasetProfile
    columns: List[ColumnProfile]
