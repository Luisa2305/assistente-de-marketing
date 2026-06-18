from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str | None = None
    MYSQL_URL: str | None = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # IA
    AI_PROVIDER: str = "mock"  # "mock" | "claude" | "gemini"
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Upload
    UPLOAD_MAX_SIZE_MB: int = 10

    @property
    def database_url(self) -> str:
        url = (
            self.DATABASE_URL
            or self.MYSQL_URL
            or "mysql+asyncmy://root:root@localhost:3306/assistente_marca"
        )
        if url.startswith("mysql://"):
            return url.replace("mysql://", "mysql+asyncmy://", 1)
        return url


settings = Settings()
