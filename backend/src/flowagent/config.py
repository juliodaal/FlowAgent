"""Application configuration.

All configuration lives in environment variables and is loaded through
Pydantic Settings. The repository ships a `.env.example` at the project root
(one level above the ``backend/`` directory) which is copied to ``.env`` for
local development.

Importing ``settings`` triggers validation; the application refuses to start
if a required value is missing or malformed.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ``backend/src/flowagent/config.py`` → parents[3] == repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    """Validated runtime configuration.

    Fields are grouped by concern and mirror the ``.env.example`` template
    at the repository root.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- OpenAI --------------------------------------------------------------
    openai_api_key: SecretStr = Field(..., description="OpenAI API key.")
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="Chat model used by the agent's reasoning steps.",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model used by the semantic memory layer.",
    )
    openai_timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)
    openai_max_retries: int = Field(default=3, ge=0, le=10)

    # --- API token (guards the FastAPI endpoints, added in Phase 5) ---------
    flowagent_api_token: SecretStr = Field(
        default=SecretStr("dev-local-token"),
        description=(
            "Bearer token clients must present to reach the agent. "
            "Override in production with a long random value."
        ),
    )

    # --- Logging ------------------------------------------------------------
    log_level: str = Field(default="INFO")
    log_json: bool = Field(
        default=False,
        description="Emit logs as JSON when True; human-readable otherwise.",
    )

    @field_validator("log_level")
    @classmethod
    def _normalize_log_level(cls, v: str) -> str:
        level = v.upper().strip()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if level not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}, got {v!r}")
        return level

    @field_validator("openai_api_key")
    @classmethod
    def _reject_placeholder_key(cls, v: SecretStr) -> SecretStr:
        raw = v.get_secret_value()
        if raw.startswith("your-") or raw == "":
            raise ValueError(
                "OPENAI_API_KEY is unset or still a placeholder. "
                "Copy .env.example to .env and fill in a real key."
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance, building it on first call."""
    return Settings()


__all__ = ["Settings", "get_settings"]
