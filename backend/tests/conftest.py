"""Shared pytest fixtures.

Sets up a sane environment for tests so importing :mod:`flowagent.config`
never fails because of a missing ``OPENAI_API_KEY``. Also provides helpers
for building fake OpenAI chat completion responses.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from flowagent.config import Settings, get_settings
from flowagent.llm.openai_client import OpenAIClient


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide deterministic env vars for the duration of each test."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-1234567890abcdef")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_JSON", "false")
    monkeypatch.setenv("FLOWAGENT_API_TOKEN", "test-token-please-rotate")
    # Reset the lru_cache so each test gets a fresh Settings instance.
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    """Fresh :class:`Settings` built from the patched environment."""
    return Settings()  # type: ignore[call-arg]


@pytest.fixture
def make_completion() -> Any:
    """Factory returning a duck-typed ``ChatCompletion``-shaped response."""

    def _build(text: str, *, finish_reason: str = "stop") -> Any:
        message = MagicMock()
        message.content = text
        choice = MagicMock()
        choice.message = message
        choice.finish_reason = finish_reason
        response = MagicMock()
        response.choices = [choice]
        usage = MagicMock()
        usage.prompt_tokens = 12
        usage.completion_tokens = 7
        response.usage = usage
        return response

    return _build


@pytest.fixture
def fake_openai_sdk() -> Any:
    """A stand-in for :class:`openai.AsyncOpenAI` with the methods we use."""
    sdk = MagicMock()
    sdk.chat = MagicMock()
    sdk.chat.completions = MagicMock()
    sdk.chat.completions.create = AsyncMock()
    return sdk


@pytest.fixture
def openai_client(settings: Settings, fake_openai_sdk: Any) -> OpenAIClient:
    """An :class:`OpenAIClient` wired to ``fake_openai_sdk``."""
    return OpenAIClient(settings, client=fake_openai_sdk)
