# backend/app/core/config.py

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "MediaMind AI"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Gemini
    GEMINI_API_KEY: str

    # Database
    DATABASE_URL: str

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = ["pdf", "mp3", "mp4", "wav", "m4a", "avi", "mov"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()