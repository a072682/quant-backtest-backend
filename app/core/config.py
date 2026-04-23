from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/backtest_system"

    class Config:
        env_file = ".env"


settings = Settings()
