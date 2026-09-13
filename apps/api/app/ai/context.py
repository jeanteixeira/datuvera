from decimal import Decimal
from math import isfinite
from app.ai.models import (
    AIInsightContext, AIDatasetContext, AIColumnContext, AIQualityContext,
    AIDimensionsContext, AIIssueContext,
)
from app.profiling.models import ProfileResponse
from app.quality.models import QualityResult


def _numeric(value):
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        numeric = float(value)
        return numeric if isfinite(numeric) else None
    return None


def build_safe_context(profile: ProfileResponse | dict, quality: QualityResult) -> AIInsightContext:
    """Explicit allowlist. Never serialize whole profiles, rows, top values or messages."""
    profile = ProfileResponse.model_validate(profile)
    dataset = profile.dataset
    columns = []
    for column in profile.columns:
        numeric_type = any(t in column.data_type.lower() for t in ('int', 'numeric', 'decimal', 'real', 'double', 'float'))
        columns.append(AIColumnContext(
            name=column.name, data_type=column.data_type, nullable=column.nullable,
            null_count=column.null_count, null_percentage=column.null_percentage,
            distinct_count=column.distinct_count, distinct_percentage=column.distinct_percentage,
            min=_numeric(column.min) if numeric_type else None,
            max=_numeric(column.max) if numeric_type else None,
            mean=_numeric(column.mean) if numeric_type else None,
            min_length=column.min_length, max_length=column.max_length, avg_length=column.avg_length,
            true_count=column.true_count, false_count=column.false_count,
        ))
    return AIInsightContext(
        dataset=AIDatasetContext(schema=dataset.schema, table=dataset.table,
                                 row_count=dataset.row_count, column_count=dataset.column_count),
        columns=columns,
        quality=AIQualityContext(
            score=quality.score,
            dimensions=AIDimensionsContext(**{name: quality.dimensions.get(name) for name in ('completeness', 'uniqueness', 'validity')}),
            issues=[AIIssueContext(column=check.column, columns=check.columns, rule=check.rule,
                                   status=check.status, failed_count=check.failed_count,
                                   failed_percentage=check.failed_percentage, score=check.score)
                    for check in quality.checks if check.status != 'passed'],
        ),
    )
