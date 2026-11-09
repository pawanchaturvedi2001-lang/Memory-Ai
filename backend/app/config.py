import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Project Memory AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database
    DATABASE_URL: str = "sqlite:///./memory_ai.db"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "memory-ai-super-secret-jwt-hackathon-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Storage
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    MAX_FILE_SIZE_BYTES: int = 30 * 1024 * 1024  # 30MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]

    # AI Configuration (OpenAI / Gemini)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")  # or "openai"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
