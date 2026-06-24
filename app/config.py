"""Application configuration — local-first defaults."""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Ward application settings."""

    app_name: str = "The Ward"
    app_version: str = "1.0.0"
    tagline: str = "ADN Nursing Study Suite"
    institution: str = "New River Community and Technical College"

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    content_dir: Path = data_dir / "content"
    static_dir: Path = base_dir / "static"
    templates_dir: Path = base_dir / "app" / "templates"
    uploads_dir: Path = data_dir / "uploads"

    database_url: str = ""

    # AI layer hooks (placeholder — wire to Ollama or API later)
    ai_enabled: bool = False
    ai_provider: str = "placeholder"  # "ollama" | "openai" | "placeholder"
    ai_base_url: str = "http://localhost:11434"
    ai_model: str = "llama3"

    class Config:
        env_prefix = "WARD_"


settings = Settings()
settings.database_url = f"sqlite+aiosqlite:///{settings.data_dir / 'ward.db'}"
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.content_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)