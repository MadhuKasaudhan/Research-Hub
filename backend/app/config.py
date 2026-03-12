"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings populated from environment variables.

    Values are read from a ``.env`` file if present, then overridden by actual
    environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Core ---
    app_name: str = "ResearchHub AI"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- Auth / JWT ---
    secret_key: str = "dev-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./researchhub.db"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"

    # --- File uploads ---
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50

    # --- Groq API ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_tokens: int = 4096

    # --- CORS ---
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        """Return CORS origins as a list, splitting on commas."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """Return the cached singleton :class:`Settings` instance."""
    return Settings()
