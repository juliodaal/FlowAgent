# FlowAgent

> Autonomous AI agent with persistent memory and custom tools — web search,
> email reading, and Notion task creation — orchestrated with **LangGraph**
> and **n8n**.

[![CI](https://github.com/juliodaal/FlowAgent/actions/workflows/ci.yml/badge.svg)](https://github.com/juliodaal/FlowAgent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Next.js 15](https://img.shields.io/badge/next.js-15-black.svg)](https://nextjs.org/)

FlowAgent is a portfolio project showcasing a production-shaped autonomous
agent: durable conversation + semantic memory in Postgres/pgvector, tool use
driven by an LLM, and an integration layer with n8n so the agent participates
in real automations (inbound email, outbound Notion tasks).

> **Status — Phase 0 / 7.** Project scaffolding only. Subsequent phases add
> the agent, memory, tools, n8n bridge, and the Next.js UI built on
> [`nyxis`](https://github.com/juliodaal/nyxis). See [Roadmap](#roadmap).

---

## Architecture

```
┌────────────────────┐      ┌──────────────────────┐      ┌──────────────────┐
│  Next.js + nyxis   │ ───► │  FastAPI  (SSE)      │ ───► │  LangGraph       │
│  useChat / UI      │      │  /chat /conversations│      │  state machine   │
└────────────────────┘      └──────────┬───────────┘      └────────┬─────────┘
                                       │                           │
                                       ▼                           ▼
                            ┌──────────────────┐         ┌────────────────────┐
                            │  Supabase        │         │  Tools             │
                            │  Postgres +      │         │  • web_search      │
                            │  pgvector memory │         │  • read_emails     │
                            └──────────────────┘         │  • notion_task     │
                                                         └─────────┬──────────┘
                                                                   │
                                                          ┌────────▼──────────┐
                                                          │  n8n workflows    │
                                                          │  Gmail ↔ agent ↔  │
                                                          │  Notion / Slack   │
                                                          └───────────────────┘
```

## Tech stack

| Layer       | Choice                                        |
| ----------- | --------------------------------------------- |
| LLM         | OpenAI (`gpt-4o-mini` default, configurable)  |
| Agent       | LangGraph (Python)                            |
| API         | FastAPI + SSE streaming                       |
| Memory      | Supabase (Postgres + pgvector)                |
| UI          | Next.js + [nyxis](https://github.com/juliodaal/nyxis) |
| Automation  | n8n (self-hosted via Docker)                  |
| Tools       | DuckDuckGo / Tavily, Gmail IMAP, Notion API   |
| Tests       | pytest (backend), Vitest (web)                |
| Quality     | ruff, mypy, eslint, prettier, gitleaks        |

## Quickstart

> Detailed step-by-step setup (Supabase, Gmail App Password, Notion
> integration) lands in Phase 6. For now this section covers cloning the
> repo and running the safety checks.

```powershell
git clone https://github.com/juliodaal/FlowAgent.git
cd FlowAgent
cp .env.example .env   # fill in real values; .env is git-ignored
python scripts/verify_env_safety.py
```

Install the pre-commit hook so leaked secrets are caught locally:

```bash
pip install pre-commit
pre-commit install
```

## Roadmap

- [x] **Phase 0** — Repo bootstrap, CI, secret scanning, env template
- [ ] **Phase 1** — Backend core: LangGraph + OpenAI + FastAPI
- [ ] **Phase 2** — Persistent memory: Supabase + pgvector
- [ ] **Phase 3** — Tools: web search, email reading, Notion task creation
- [ ] **Phase 4** — n8n integration: Gmail trigger and Notion writer workflows
- [ ] **Phase 5** — Web UI on `nyxis` (`useChat` + chat thread components)
- [ ] **Phase 6** — Full setup guide, demo scenarios, troubleshooting
- [ ] **Phase 7** — Final security audit + `v1.0.0` release

## Security

See [SECURITY.md](SECURITY.md). Short version: no secrets in the repo, ever.
CI runs [`gitleaks`](https://github.com/gitleaks/gitleaks) on every push.

## License

MIT © Julio César Daal — see [LICENSE](LICENSE).
