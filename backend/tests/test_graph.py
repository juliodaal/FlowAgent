"""End-to-end LangGraph execution with a mocked OpenAI client."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from flowagent.graph import AgentState, build_graph, initial_state
from flowagent.graph.builder import _last_user_message, planner_node, responder_node


def test_initial_state_appends_user_message() -> None:
    state = initial_state("hello")
    assert state["messages"] == [{"role": "user", "content": "hello"}]


def test_initial_state_preserves_history() -> None:
    history: list = [
        {"role": "user", "content": "earlier"},
        {"role": "assistant", "content": "ok"},
    ]
    state = initial_state("now", history=history)
    assert len(state["messages"]) == 3
    assert state["messages"][-1] == {"role": "user", "content": "now"}


@pytest.mark.parametrize("bad", ["", "   "])
def test_initial_state_rejects_empty_message(bad: str) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        initial_state(bad)


def test_last_user_message_returns_latest_user_turn() -> None:
    state: AgentState = AgentState(
        messages=[
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "second"},
        ]
    )
    assert _last_user_message(state) == "second"


def test_last_user_message_raises_when_none_present() -> None:
    state: AgentState = AgentState(messages=[{"role": "assistant", "content": "hi"}])
    with pytest.raises(ValueError, match="no user message"):
        _last_user_message(state)


async def test_planner_node_returns_plan(
    openai_client: Any,
    fake_openai_sdk: Any,
    make_completion: Any,
) -> None:
    fake_openai_sdk.chat.completions.create.return_value = make_completion(
        "- search the web\n- summarise"
    )
    state = initial_state("what is the weather in Tokyo")

    out = await planner_node(state, client=openai_client)

    assert out == {"plan": "- search the web\n- summarise"}
    kwargs = fake_openai_sdk.chat.completions.create.await_args.kwargs
    assert "Tokyo" in kwargs["messages"][0]["content"]
    assert kwargs["temperature"] == 0.0


async def test_responder_node_embeds_plan_in_system_prompt(
    openai_client: Any,
    fake_openai_sdk: Any,
    make_completion: Any,
) -> None:
    fake_openai_sdk.chat.completions.create.return_value = make_completion("Tokyo is sunny.")
    state = initial_state("what is the weather in Tokyo")
    state["plan"] = "- answer directly"

    out = await responder_node(state, client=openai_client)

    assert out == {"response": "Tokyo is sunny."}
    kwargs = fake_openai_sdk.chat.completions.create.await_args.kwargs
    system_msg = kwargs["messages"][0]
    assert system_msg["role"] == "system"
    assert "FlowAgent" in system_msg["content"]
    assert "answer directly" in system_msg["content"]


async def test_graph_runs_end_to_end(
    openai_client: Any,
    fake_openai_sdk: Any,
    make_completion: Any,
) -> None:
    # Two sequential LLM calls (planner then responder).
    fake_openai_sdk.chat.completions.create.side_effect = [
        make_completion("- answer directly"),
        make_completion("hi back"),
    ]
    graph = build_graph(client=openai_client)

    result = await graph.ainvoke(initial_state("say hi"))

    assert result["plan"] == "- answer directly"
    assert result["response"] == "hi back"
    assert fake_openai_sdk.chat.completions.create.await_count == 2


async def test_graph_propagates_openai_errors(
    openai_client: Any,
    fake_openai_sdk: Any,
) -> None:
    fake_openai_sdk.chat.completions.create.side_effect = RuntimeError("rate limited")
    graph = build_graph(client=openai_client)

    with pytest.raises(RuntimeError, match="rate limited"):
        await graph.ainvoke(initial_state("hi"))


def test_build_graph_uses_singleton_client_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When no client is passed, build_graph resolves the singleton."""
    sentinel = MagicMock(name="singleton-client")
    monkeypatch.setattr("flowagent.graph.builder.get_openai_client", lambda: sentinel)
    # Just calling build_graph must not raise even without OPENAI_API_KEY here.
    graph = build_graph()
    assert graph is not None
