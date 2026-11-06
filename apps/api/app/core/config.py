# app/core/config.py
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Scalable AI Agent API"
    ENVIRONMENT: str = "development"
    
    # Database - High Concurrency Connection Pool (AsyncPG)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/simple_ai_agent",
        description="Async PostgreSQL connection string"
    )
    DB_POOL_SIZE: int = Field(default=20, description="Baseline connection pool size per worker")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Max burst connections beyond pool size")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Seconds to wait before timing out getting a connection")
    DB_POOL_RECYCLE: int = Field(default=1800, description="Recycle connections every 30 minutes to prevent stale sockets")

    # Redis - Cache & Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_PER_MINUTE: int = 30

    # Authentication & Security
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SUPER_SECRET_RANDOM_KEY_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # LLM Strategy Configuration ('gemini' or 'ollama')
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    CHAT_MEMORY_WINDOW_SIZE: int = 10

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:4200"]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        extra="ignore"
    )


settings = Settings()
