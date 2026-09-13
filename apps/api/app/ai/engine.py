from app.ai.context import build_safe_context
from app.ai.models import AIInsightResult
from app.ai.providers.base import AIProvider, AIProviderError
from app.profiling.models import ProfileResponse
from app.quality.models import QualityResult


def generate_insights(profile: ProfileResponse | dict, quality: QualityResult, provider: AIProvider) -> AIInsightResult:
    context = build_safe_context(profile, quality)
    try:
        result = AIInsightResult.model_validate(provider.generate_insights(context))
        columns = {column.name for column in context.columns}
        if any(finding.column is not None and finding.column not in columns for finding in result.findings):
            raise ValueError('Unknown finding column')
        if any(check.column not in columns for check in result.suggested_checks):
            raise ValueError('Unknown suggested-check column')
        return result
    except Exception:
        # Do not log exception text, context, credentials or the provider response.
        raise AIProviderError('AI provider failed to generate valid insights.') from None
