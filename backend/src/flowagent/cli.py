"""``flowagent`` console entrypoint — currently a smoke check.

Usage::

    uv run flowagent --help
    uv run flowagent ping

The HTTP server entrypoint is added in a later phase. ``ping`` exists so
``uv run flowagent ping`` can validate the LangGraph wiring end-to-end with
a real OpenAI key during local setup.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from flowagent import __version__
from flowagent.config import get_settings
from flowagent.graph import build_graph, initial_state
from flowagent.logging import configure_logging


async def _run_ping(message: str) -> str:
    state = initial_state(message)
    graph = build_graph()
    result = await graph.ainvoke(state)
    return str(result.get("response", "<no response>"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flowagent", description="FlowAgent CLI")
    parser.add_argument("--version", action="version", version=f"flowagent {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    ping = sub.add_parser("ping", help="Invoke the agent graph with a single message.")
    ping.add_argument("message", nargs="?", default="Hello — say hi back in five words.")

    args = parser.parse_args(argv)

    settings = get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)

    if args.command == "ping":
        response = asyncio.run(_run_ping(args.message))
        print(response)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
