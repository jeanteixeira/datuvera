from app.ai.models import AIStatus
from app.ai.providers.base import AIProvider
from app.core.config import settings


def ai_status() -> AIStatus:
    enabled = bool(settings.DATUVERA_AI_ENABLED and settings.OPENAI_API_KEY and
                   settings.OPENAI_API_KEY.get_secret_value().strip() and settings.DATUVERA_AI_MODEL.strip())
    return AIStatus(enabled=enabled, provider='openai' if enabled else None,
                    model=settings.DATUVERA_AI_MODEL if enabled else None)


def get_ai_provider() -> AIProvider | None:
    if not ai_status().enabled:
        return None
    from app.ai.providers.openai import OpenAIProvider
    return OpenAIProvider(settings.OPENAI_API_KEY.get_secret_value(), settings.DATUVERA_AI_MODEL)
