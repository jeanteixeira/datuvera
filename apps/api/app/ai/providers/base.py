from typing import Protocol
from app.ai.models import AIInsightContext, AIInsightResult


class AIProviderError(Exception):
    """Safe boundary for provider failures; never include provider payloads."""


class AIProvider(Protocol):
    def generate_insights(self, context: AIInsightContext) -> AIInsightResult:
        ...
