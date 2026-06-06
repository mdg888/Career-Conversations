from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    data_dir: Path = Path("backend/data")
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    max_upload_size_mb: int = 20
    max_context_chunks: int = 5


settings = Settings()
