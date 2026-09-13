from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator
from app.quality.parameters import validate_parameters
from app.quality.types import RuleType


class QualityRuleCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_name: str = Field(alias='schema', min_length=1)
    table_name: str = Field(alias='table', min_length=1)
    column_name: str = Field(alias='column', min_length=1)
    rule_type: RuleType = Field(alias='rule')
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_enabled: StrictBool = True

    @model_validator(mode='after')
    def check_parameters(self):
        validate_parameters(self.rule_type, self.parameters)
        return self


class QualityRulePatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    parameters: dict[str, Any] | None = None
    is_enabled: StrictBool | None = None

    @model_validator(mode='after')
    def non_null_patch(self):
        if not self.model_fields_set or any(getattr(self, name) is None for name in self.model_fields_set):
            raise ValueError('Provide non-null parameters or is_enabled')
        return self


class QualityRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    source_id: int
    schema_name: str = Field(serialization_alias='schema')
    table_name: str = Field(serialization_alias='table')
    column_name: str = Field(serialization_alias='column')
    rule_type: RuleType = Field(serialization_alias='rule')
    parameters: dict[str, Any]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
