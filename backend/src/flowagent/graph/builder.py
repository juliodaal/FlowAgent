"""Compose the LangGraph state machine.

Phase 1 graph (linear, no tools yet)::

    START → planner → responder → END

* **planner** asks the LLM to produce a short plan for the user's request.
* **responder** asks the LLM to produce the final answer, conditioned on the
  plan plus the full conversation history.

Phase 3 will branch into a tool-execution loop between these two nodes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.graph import END, START, StateGraph

from flowagent.graph.state import AgentState
from flowagent.llm.openai_client import ChatMessage, OpenAIClient, get_openai_client
from flowagent.logging import get_logger
from flowagent.prompts import load_prompt, render_prompt

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


_log = get_logger(__name__)


def _last_user_message(state: AgentState) -> str:
    """Return the content of the most recent user-role message."""
    messages = state.get("messages") or []
    for msg in reversed(messages):
        if msg["role"] == "user":
            return msg["content"]
    raise ValueError("AgentState has no user message to plan against")


async def planner_node(state: AgentState, *, client: OpenAIClient) -> dict[str, Any]:
    """Generate a 1-3 bullet plan for the user's latest request."""
    user_message = _last_user_message(state)
    prompt = render_prompt("planner", user_message=user_message)
    plan = await client.chat_text(
        [{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=200,
    )
    _log.info("graph.planner.ok", plan_chars=len(plan))
    return {"plan": plan.strip()}


async def responder_node(state: AgentState, *, client: OpenAIClient) -> dict[str, Any]:
    """Produce the final assistant response given the plan and history."""
    history = state.get("messages") or []
    plan = state.get("plan", "").strip()

    system_prompt = load_prompt("system")
    if plan:
        system_prompt = f"{system_prompt}\n\n## Plan for this turn\n{plan}"

    messages: list[ChatMessage] = [{"role": "system", "content": system_prompt}, *history]
    answer = await client.chat_text(messages, temperature=0.3, max_tokens=800)
    _log.info("graph.responder.ok", response_chars=len(answer))
    return {"response": answer.strip()}


def build_graph(client: OpenAIClient | None = None) -> CompiledStateGraph[AgentState, AgentState]:
    """Compile the LangGraph state machine.

    Pass ``client=`` from tests to inject a mocked :class:`OpenAIClient`.
    In production callers use the default and the process-wide client is
    looked up lazily.
    """
    resolved_client = client or get_openai_client()

    async def _planner(state: AgentState) -> dict[str, Any]:
        return await planner_node(state, client=resolved_client)

    async def _responder(state: AgentState) -> dict[str, Any]:
        return await responder_node(state, client=resolved_client)

    graph: StateGraph[AgentState, AgentState] = StateGraph(AgentState)
    graph.add_node("planner", _planner)
    graph.add_node("responder", _responder)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "responder")
    graph.add_edge("responder", END)
    return graph.compile()


__all__ = ["build_graph", "planner_node", "responder_node"]
