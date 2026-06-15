from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://wc_user:wc_pass@localhost:5432/worldcup"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Sports APIs
    FOOTBALL_DATA_API_KEY: str = ""
    API_SPORTS_KEY: str = ""

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    # Ingestion
    POLL_INTERVAL_SECONDS: int = 30

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
