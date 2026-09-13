from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

RiskLevel = Literal['low', 'medium', 'high']
SupportedRule = Literal['not_null', 'unique', 'email_format', 'allowed_values', 'min_value', 'max_value']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class AIInsightFinding(StrictModel):
    severity: RiskLevel
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=800)
    column: str | None


class AISuggestedCheckParameters(StrictModel):
    value: float | None
    values: list[str] | None


class AISuggestedCheck(StrictModel):
    column: str
    rule: SupportedRule
    reason: str = Field(min_length=1, max_length=600)
    parameters: AISuggestedCheckParameters

    @model_validator(mode='after')
    def validate_parameters(self):
        if self.rule in ('min_value', 'max_value'):
            if self.parameters.value is None or self.parameters.values is not None:
                raise ValueError('Value-bound suggestions require only a numeric value')
        elif self.rule == 'allowed_values':
            if self.parameters.values is None or self.parameters.value is not None:
                raise ValueError('Allowed-values suggestions require only a values list')
        elif self.parameters.value is not None or self.parameters.values is not None:
            raise ValueError('This rule takes no parameters')
        return self


class AIInsightResult(StrictModel):
    summary: str = Field(min_length=1, max_length=1200)
    risk_level: RiskLevel
    findings: list[AIInsightFinding] = Field(max_length=5)
    suggested_checks: list[AISuggestedCheck] = Field(max_length=5)


class AIDatasetContext(StrictModel):
    schema_name: str = Field(alias='schema')
    table: str
    row_count: int
    column_count: int


class AIColumnContext(StrictModel):
    name: str
    data_type: str
    nullable: bool
    null_count: int
    null_percentage: float
    distinct_count: int
    distinct_percentage: float
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    avg_length: float | None = None
    true_count: int | None = None
    false_count: int | None = None


class AIDimensionsContext(StrictModel):
    completeness: float | None
    uniqueness: float | None
    validity: float | None


class AIIssueContext(StrictModel):
    column: str | None
    columns: list[str] | None
    rule: SupportedRule
    status: Literal['warning', 'failed']
    failed_count: int
    failed_percentage: float
    score: float


class AIQualityContext(StrictModel):
    score: float
    dimensions: AIDimensionsContext
    issues: list[AIIssueContext]


class AIInsightContext(StrictModel):
    dataset: AIDatasetContext
    columns: list[AIColumnContext]
    quality: AIQualityContext


class AIStatus(StrictModel):
    enabled: bool
    provider: Literal['openai'] | None
    model: str | None


class AIInsightRequest(StrictModel):
    schema_name: str = Field(alias='schema', min_length=1)
    table: str = Field(min_length=1)
