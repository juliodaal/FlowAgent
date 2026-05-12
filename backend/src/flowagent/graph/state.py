"""Typed state shared between LangGraph nodes.

A ``TypedDict`` is used (instead of :class:`pydantic.BaseModel`) because
LangGraph's reducer machinery prefers plain dicts and the state is internal
to the graph — external callers go through the public API instead.
"""

from __future__ import annotations

from typing import TypedDict

from flowagent.llm.openai_client import ChatMessage


class AgentState(TypedDict, total=False):
    """Working memory for a single ``invoke`` of the graph.

    Fields:
        messages: Full conversation history, oldest first. The latest item is
            the user message the agent must answer.
        plan: Short plan produced by the planner node.
        response: Final assistant text emitted by the responder node.
    """

    messages: list[ChatMessage]
    plan: str
    response: str


def initial_state(user_message: str, history: list[ChatMessage] | None = None) -> AgentState:
    """Build a fresh :class:`AgentState` seeded with one user turn.

    ``history`` may carry prior turns (e.g. loaded from persistent memory in
    Phase 2). The user message is always appended last so the planner reads
    the newest turn from the same position regardless of history length.
    """
    if not user_message or not user_message.strip():
        raise ValueError("user_message must be a non-empty string")

    messages: list[ChatMessage] = list(history or [])
    messages.append({"role": "user", "content": user_message})
    return AgentState(messages=messages)


__all__ = ["AgentState", "initial_state"]
