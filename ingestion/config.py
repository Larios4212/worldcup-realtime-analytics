from pydantic_settings import BaseSettings


class IngestionConfig(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql+asyncpg://wc_user:wc_pass@localhost:5432/worldcup"
    BACKEND_URL: str = "http://backend:8000"

    FOOTBALL_DATA_API_KEY: str = ""
    API_SPORTS_KEY: str = ""

    POLL_INTERVAL_SECONDS: int = 30
    COMPETITION_ID: int = 2000  # FIFA World Cup on football-data.org

    model_config = {"env_file": ".env"}
