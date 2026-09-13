from pydantic import SecretStr
try:
    # pydantic v2.13+ moved BaseSettings to pydantic-settings
    from pydantic import BaseSettings
except Exception:
    from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Datuvera"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Open-source data profiling and quality platform for modern data stacks, enhanced with AI."

    DATABASE_URL: str = "postgresql+psycopg://datuvera:datuvera@datuvera-db:5432/datuvera"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    APP_ENV: str = "development"

    DATUVERA_AI_ENABLED: bool = False
    OPENAI_API_KEY: SecretStr | None = None
    DATUVERA_AI_MODEL: str = "gpt-5.4-mini"

    class Config:
        env_file = ".env"


settings = Settings()
