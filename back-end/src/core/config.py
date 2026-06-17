from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Interview Copilot"
    debug: bool = True
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000"

    secret_key: str = "dev-secret-key"
    access_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_interview"
    )

    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "ai_interview_docs"

    llm_api_key: str = ""
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode"
    llm_model: str = "qwen3.7-plus"

    embedding_model: str = "tongyi-embedding-vision-plus-2026-03-06"
    rerank_model: str = "qwen3-rerank"

    upload_dir: str = "uploads"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
