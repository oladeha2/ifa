"""Typed application configuration, loaded from the environment / `.env`.

Missing required values (notably the OpenRouter API key) fail fast at load
time with a clear, actionable message rather than surfacing deep in a call.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration for the application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = Field(..., description="OpenRouter API key.")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "anthropic/claude-3.5-sonnet"

    embedding_model: str = "all-MiniLM-L6-v2"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    leads_path: Path = Path("leads.json")
    chroma_path: Path = Path(".chroma")
    collection_name: str = "leads"

    top_k: int = 5
    overfetch: int = 20
    rerank_threshold: float = 0.0

    summarize_every_n_turns: int = 6
    memory_path: Path = Path("memory/session.json")


class ConfigError(RuntimeError):
    """Raised when the application is misconfigured (e.g. missing API key)."""


def load_settings() -> Settings:
    """Load settings, converting validation failures into a clear message.

    Raises:
        ConfigError: if required configuration is missing or invalid.
    """
    try:
        return Settings()  # type: ignore[call-arg]
    except Exception as exc:  # pydantic ValidationError and friends
        raise ConfigError(
            "Failed to load configuration. Ensure a `.env` file exists with a "
            "valid `OPENROUTER_API_KEY` (see `.env.example`).\n"
            f"Underlying error: {exc}"
        ) from exc
