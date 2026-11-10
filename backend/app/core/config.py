from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Text Secury"
    environment: str = "local"  # local, staging, production
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://secury:secury@localhost:5432/secury"
    redis_url: str = "redis://localhost:6379/0"

    # S3 / MinIO (mesma API; em produção basta apontar para o S3 e remover o endpoint)
    s3_endpoint_url: str | None = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    s3_bucket: str = "documents"

    max_upload_mb: int = 50
    cors_origins: list[str] = ["http://localhost:3000"]

    # Executa o scan na própria requisição (útil para testes e desenvolvimento sem worker).
    scan_eager: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
