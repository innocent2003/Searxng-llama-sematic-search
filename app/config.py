from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    searxng_url: str = "http://localhost:8080"
    ollama_url: str = "http://localhost:11434"
    chat_model: str = "qwen3:8b"
    embed_model: str = "nomic-embed-text"
    data_dir: str = "./data"
    log_dir: str = "./logs"
    top_k: int = 5
    max_fetch_bytes: int = 1_500_000
    fetch_timeout_seconds: int = 15
    update_queries: str = (
        "latest technology news;"
        "Python release notes;"
        "AI research news;"
        "cybersecurity news;"
        "climate science news"
    )

    @property
    def data_path(self) -> Path:
        p = Path(self.data_dir)
        return p if p.is_absolute() else ROOT / p

    @property
    def log_path(self) -> Path:
        p = Path(self.log_dir)
        return p if p.is_absolute() else ROOT / p


settings = Settings()
settings.data_path.mkdir(parents=True, exist_ok=True)
settings.log_path.mkdir(parents=True, exist_ok=True)