import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Main Settings configurations manager.
    Reads values from OS environment or local .env files.
    """
    # API Settings
    GATEWAY_PORT: int = Field(default=8000)
    API_SECRET_KEY: str = Field(default="devsecretkey123")
    LOG_LEVEL: str = Field(default="INFO")

    # Embeddings
    EMBEDDING_PROVIDER: str = Field(default="openai")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    EMBEDDING_DIMENSIONS: int = Field(default=1536)
    OPENAI_API_KEY: str = Field(default="")
    OLLAMA_URL: str = Field(default="http://host.docker.internal:11434")

    # PostgreSQL
    DATABASE_URL: str = Field(default="postgresql+asyncpg://memory_user:DevSecurePassword123@localhost:5432/memory_db")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_PASSWORD: str = Field(default="DevSecureRedisPassword123")

    # Qdrant
    QDRANT_HOST: str = Field(default="localhost")
    QDRANT_PORT: int = Field(default=6333)
    QDRANT_COLLECTION: str = Field(default="ai_memories")

    # Memory Heuristics
    DEDUP_SIMILARITY_THRESHOLD: float = Field(default=0.92)
    MIN_IMPORTANCE_SCORE_TO_STORE: float = Field(default=0.3)
    MAX_CONTEXT_TOKENS: int = Field(default=4000)

    # Allow custom values via env loading override
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings singleton
settings = Settings()
