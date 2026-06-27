"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Agora
    agora_app_id: str = ""
    agora_app_certificate: str = ""
    agora_token_expiry_seconds: int = 3600

    # Google
    google_api_key: str = ""
    tts_api_key: str = ""
    stt_api_key: str = ""

    # Gemini model
    gemini_model: str = "gemini-2.5-flash"

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_conversation_ttl: int = 86400  # 24 hours

    # Database
    database_url: str = ""

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:5173"

    # Voice Activity Detection
    vad_aggressiveness: int = 2  # 0-3
    silence_threshold_ms: int = 800  # ms of silence before sending to agent

    # Audio
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_chunk_ms: int = 30  # 10, 20, or 30 ms for webrtcvad


@lru_cache
def get_settings() -> Settings:
    return Settings()
