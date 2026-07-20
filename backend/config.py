from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    outputs_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs")
    sample_images_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "sample_images"
    )
    frontend_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "frontend" / "remotion"
    )
    remotion_generated_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "frontend" / "remotion" / "src" / "generated"
    )
    docs_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent / "docs")
    vector_store_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / ".chromadb"
    )
    use_vector_store: bool = False
    fallback_to_offline_on_quota: bool = True

    llm_provider: str = Field(
        default="gemini",
        validation_alias=AliasChoices("LLM_PROVIDER", "MODEL_PROVIDER"),
    )
    ollama_base_url: str = "http://localhost:11434"
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    text_model: str = "gemini-2.5-flash"
    vision_model: str = "gemini-2.5-flash"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    max_selected_images: int = 8
    max_analyzed_images: int = 4
    max_uploaded_images: int = 4
    max_compile_retries: int = 3
    default_fps: int = 30
    default_scene_duration_seconds: float = 3.0
    render_codec: str = "h264"
    render_crf: int = 28
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
