# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Modular App"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/myapp_db"

    # Auth Security
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SUPER_SECRET_RANDOM_KEY_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()