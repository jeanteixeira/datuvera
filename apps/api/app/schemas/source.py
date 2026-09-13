from pydantic import BaseModel, Field
from typing import Optional


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
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        orm_mode = True
