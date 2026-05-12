"""OpenAI client wrapper behaviour (no network calls)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from flowagent.llm.openai_client import OpenAIClient


async def test_chat_text_returns_assistant_content(
    openai_client: OpenAIClient,
    fake_openai_sdk: Any,
    make_completion: Any,
) -> None:
    fake_openai_sdk.chat.completions.create.return_value = make_completion("the answer is 42")

    result = await openai_client.chat_text([{"role": "user", "content": "ping"}])

    assert result == "the answer is 42"
    fake_openai_sdk.chat.completions.create.assert_awaited_once()
    call_kwargs = fake_openai_sdk.chat.completions.create.await_args.kwargs
    assert call_kwargs["model"] == "gpt-test"
    assert call_kwargs["messages"] == [{"role": "user", "content": "ping"}]
    assert call_kwargs["temperature"] == 0.2


async def test_chat_text_uses_explicit_model_override(
    openai_client: OpenAIClient,
    fake_openai_sdk: Any,
    make_completion: Any,
) -> None:
    fake_openai_sdk.chat.completions.create.return_value = make_completion("hi")

    await openai_client.chat_text(
        [{"role": "user", "content": "x"}],
        model="gpt-override",
        temperature=0.9,
        max_tokens=50,
    )

    kwargs = fake_openai_sdk.chat.completions.create.await_args.kwargs
    assert kwargs["model"] == "gpt-override"
    assert kwargs["temperature"] == 0.9
    assert kwargs["max_tokens"] == 50


async def test_chat_text_raises_on_empty_choices(
    openai_client: OpenAIClient,
    fake_openai_sdk: Any,
) -> None:
    empty = MagicMock()
    empty.choices = []
    fake_openai_sdk.chat.completions.create.return_value = empty

    with pytest.raises(RuntimeError, match="no choices"):
        await openai_client.chat_text([{"role": "user", "content": "x"}])


async def test_chat_text_raises_on_null_content(
    openai_client: OpenAIClient,
    fake_openai_sdk: Any,
) -> None:
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = None
    response.choices[0].finish_reason = "content_filter"
    response.usage = None
    fake_openai_sdk.chat.completions.create.return_value = response

    with pytest.raises(RuntimeError, match="empty content"):
        await openai_client.chat_text([{"role": "user", "content": "x"}])


async def test_chat_completion_propagates_errors(
    openai_client: OpenAIClient,
    fake_openai_sdk: Any,
) -> None:
    fake_openai_sdk.chat.completions.create.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await openai_client.chat_completion([{"role": "user", "content": "x"}])
