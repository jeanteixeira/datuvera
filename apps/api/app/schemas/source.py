from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class DataSourceCreate(BaseModel):
    name: str
    type: str = Field("postgresql")
    host: str
    port: int = 5432
    database: str
    username: str
    password: str


class DataSourceRead(BaseModel):
    id: int
    name: str
    type: str
    host: str
    port: int
    database: str
    username: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    # Pydantic v2: enable from_attributes to allow model_validate on ORM objects
    model_config = ConfigDict(from_attributes=True)
