"""Settings validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from flowagent.config import Settings, get_settings


def test_settings_loads_from_env() -> None:
    settings = Settings()  # type: ignore[call-arg]
    assert settings.openai_api_key.get_secret_value() == "test-only-fake-openai-key-do-not-use"
    assert settings.openai_model == "gpt-test"
    assert settings.log_level == "DEBUG"


def test_settings_defaults_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    settings = Settings()  # type: ignore[call-arg]
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.openai_embedding_model == "text-embedding-3-small"
    assert settings.log_level == "INFO"
    assert settings.log_json is False


def test_placeholder_openai_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "your-openai-api-key-here")
    with pytest.raises(ValidationError, match="placeholder"):
        Settings()  # type: ignore[call-arg]


def test_empty_openai_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(ValidationError, match="placeholder"):
        Settings()  # type: ignore[call-arg]


def test_log_level_is_uppercased(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "warning")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.log_level == "WARNING"


def test_log_level_rejects_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "verbose")
    with pytest.raises(ValidationError, match="log_level"):
        Settings()  # type: ignore[call-arg]


def test_openai_timeout_bounds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "0")
    with pytest.raises(ValidationError, match="openai_timeout_seconds"):
        Settings()  # type: ignore[call-arg]


def test_get_settings_caches() -> None:
    a = get_settings()
    b = get_settings()
    assert a is b
