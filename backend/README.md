# FlowAgent — Backend

Python 3.12 service that runs the LangGraph agent and exposes it over a
FastAPI HTTP API with Server-Sent Events streaming.

## Layout

```
backend/
├── pyproject.toml           # deps, ruff, mypy, pytest config
├── src/flowagent/
│   ├── __init__.py
│   ├── cli.py               # `flowagent` console entrypoint (smoke check)
│   ├── config.py            # Pydantic Settings (reads .env from repo root)
│   ├── logging.py           # structlog setup
│   ├── llm/openai_client.py # OpenAI client w/ retry + structured logging
│   ├── prompts/             # markdown prompt templates
│   │   ├── system.md
│   │   └── planner.md
│   └── graph/
│       ├── state.py         # AgentState (typed dict)
│       └── builder.py       # build_graph() → compiled LangGraph
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_openai_client.py
    └── test_graph.py
```

## Develop

```powershell
# from repo root
cd backend
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy src
```

Environment variables are read from `../.env` at the repo root (see
`.env.example`).

## Run the smoke CLI

```powershell
uv run flowagent --help
uv run flowagent ping        # builds the graph, runs one cycle on fake input
```

The HTTP server is added in a later phase.
