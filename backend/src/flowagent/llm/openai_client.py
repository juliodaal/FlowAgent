"""Thin async wrapper around the OpenAI Python SDK.

Centralises:

* Authentication via :class:`flowagent.config.Settings`.
* Timeout and retry configuration consistent across the codebase.
* Structured logging of every request (model, latency, token usage).

The wrapper intentionally exposes a small surface — adding a method here is
preferable to scattering ``AsyncOpenAI`` calls throughout the codebase.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from openai import AsyncOpenAI

from flowagent.config import Settings, get_settings
from flowagent.logging import get_logger

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion


_log = get_logger(__name__)


class ChatMessage(TypedDict):
    """OpenAI chat message in the simplified shape used across FlowAgent."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str


class OpenAIClient:
    """Async OpenAI client used by every agent node.

    Constructed once per process via :func:`get_openai_client`. Tests inject a
    custom :class:`AsyncOpenAI` (typically a respx-mocked one) by passing
    ``client=`` directly.
    """

    def __init__(self, settings: Settings, *, client: AsyncOpenAI | None = None) -> None:
        self._settings = settings
        self._client = client or AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )

    @property
    def model(self) -> str:
        """Default chat model from settings."""
        return self._settings.openai_model

    async def chat_completion(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> ChatCompletion:
        """Call the chat completions API and return the raw response.

        Errors propagate. The OpenAI SDK transparently retries on transient
        failures (429, 408, 5xx) up to ``settings.openai_max_retries`` times.
        """
        chosen_model = model or self.model
        bound = _log.bind(model=chosen_model, message_count=len(messages))
        bound.info("openai.chat_completion.start")

        started = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(
                model=chosen_model,
                messages=list(messages),  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
                **extra,
            )
        except Exception as exc:
            bound.error(
                "openai.chat_completion.error",
                error_type=type(exc).__name__,
                duration_ms=int((time.perf_counter() - started) * 1000),
            )
            raise

        duration_ms = int((time.perf_counter() - started) * 1000)
        usage = response.usage
        bound.info(
            "openai.chat_completion.ok",
            duration_ms=duration_ms,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            finish_reason=response.choices[0].finish_reason if response.choices else None,
        )
        return response

    async def chat_text(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> str:
        """Convenience helper: return the first choice's text content."""
        response = await self.chat_completion(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not response.choices:
            raise RuntimeError("OpenAI returned no choices")
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("OpenAI returned a choice with empty content")
        return content


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAIClient:
    """Process-wide singleton, built lazily on first call."""
    return OpenAIClient(get_settings())


__all__ = ["ChatMessage", "OpenAIClient", "get_openai_client"]
