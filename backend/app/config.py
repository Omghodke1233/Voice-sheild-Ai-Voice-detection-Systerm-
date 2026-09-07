"""
Central application configuration.

All settings are read from environment variables (or a local .env file) via
pydantic-settings. Nothing sensitive is hard-coded here. See .env.example for
the full list of supported variables and their defaults.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, populated from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- General ---
    app_name: str = "VoiceShield"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # --- Database ---
    # Local dev defaults to SQLite so the MVP runs with zero external services.
    # Production/Docker overrides this with a PostgreSQL URL, e.g.
    #   postgresql+psycopg://user:pass@db:5432/voiceshield
    database_url: str = "sqlite:///./voiceshield.db"

    # --- WebSocket ---
    websocket_timeout: int = 60  # seconds of inactivity before closing

    # --- Audio contract (see docs; used from Phase 2 onward) ---
    audio_sample_rate: int = 16_000
    audio_channels: int = 1
    audio_chunk_seconds: float = 2.0
    audio_overlap_seconds: float = 1.0

    # --- AI module thresholds (used from Phase 3 onward) ---
    voice_threshold: float = 0.5
    speaker_threshold: float = 0.5

    # --- Risk fusion thresholds (used from Phase 4 onward) ---
    risk_threshold_low: float = 0.25
    risk_threshold_medium: float = 0.50
    risk_threshold_high: float = 0.75

    # --- Model paths (used from Phase 3 onward) ---
    model_path_voice: str = "./models/voice_detector"
    model_path_speaker: str = "./models/speaker"

    # --- CORS (frontend dev server) ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins as a clean list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()
