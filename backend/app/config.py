import os
from pydantic_settings import BaseSettings
from typing import List

# Resolve paths relative to this file
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_THIS_DIR)
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)


class Settings(BaseSettings):
    # GitHub Models API
    GITHUB_TOKEN: str = ""

    # GitHub Models endpoint (OpenAI-compatible)
    GITHUB_MODELS_ENDPOINT: str = "https://models.inference.ai.azure.com"

    # Models
    GPT4O_MODEL: str = "gpt-4o"
    GPT4O_MINI_MODEL: str = "gpt-4o-mini"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Data paths
    SESSIONS_DIR: str = os.path.join(_BACKEND_DIR, "data", "sessions")
    UPLOADS_DIR: str = os.path.join(_BACKEND_DIR, "data", "uploads")

    class Config:
        # Look for .env in project root first, then backend/
        env_file = (
            os.path.join(_PROJECT_ROOT, ".env"),
            os.path.join(_BACKEND_DIR, ".env"),
        )
        env_file_encoding = "utf-8"


settings = Settings()

