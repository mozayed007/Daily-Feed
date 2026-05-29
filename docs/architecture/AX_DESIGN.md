# AX Architecture: Daily Feed as Agent Engine

## Problem

Daily Feed has a rich REST API, Pydantic-AI agents, personalization, scheduling, and memory — all designed for human UX via a React frontend and voice assistant. But agents (Claude, Codex, OpenCode, Pi, Kilo CLI, etc.) have no clean way to consume it. They'd need to parse HTML, handle auth flows, or make dozens of HTTP calls to assemble a simple briefing.

The goal: make Daily Feed a **background engine** any agent can tap into — a personal AI morning/night routine, a digest generator, a trend detector — with the same quality of experience as the frontend, but shaped for agent consumption.

## Shape

### Layer 1: MCP Server (the bridge)

An MCP server wraps the existing backend as atomic, composable tools. Agents connect via stdio (local) or SSE (remote). This is the primary AX surface.

**Tools (actions agents can call):**

| Tool | Description | Maps to |
|------|-------------|---------|
| `get_briefing` | Get a personalized digest for a time window (morning/evening/custom) | `/users/me/digest/generate` + personalization |
| `list_articles` | List articles with filters (category, source, date, processed) | `/articles` |
| `search_articles` | Full-text search across articles | `/articles/search` |
| `get_article` | Get a single article with full content and metadata | `/articles/{id}` |
| `summarize_article` | Summarize an article with AI | `/articles/{id}/summarize` |
| `detect_trends` | Find emerging topics from recent articles | `/articles/trends` |
| `cluster_articles` | Group articles by topic | `/articles/cluster` |
| `synthesize_topic` | Merge multi-source coverage on a topic | `/articles/synthesize` |
| `explain_relevance` | Why an article matches user interests | `/articles/{id}/reason` |
| `get_user_interests` | Get learned user interests and preferences | `/memory/interests` |
| `get_sources` | List configured RSS sources | `/sources` |
| `trigger_fetch` | Fetch new articles from sources | `/sources/fetch` |
| `get_stats` | System stats (article counts, categories, activity) | `/stats` |
| `run_pipeline` | Execute a pipeline (fetch/process/digest/full) | `/pipeline/{task_type}` |

**Resources (read-only context):**

| Resource | Description |
|----------|-------------|
| `daily://digest/latest` | Most recent digest |
| `daily://digest/{id}` | Specific digest by ID |
| `daily://trends/current` | Current trend snapshot |
| `daily://interests` | User interest profile |
| `daily://config` | Current system configuration |

**Prompts (reusable workflows):**

| Prompt | Description |
|--------|-------------|
| `morning_briefing` | Structured prompt for a morning news briefing |
| `evening_roundup` | Structured prompt for an evening digest |
| `topic_deep_dive` | Deep exploration of a specific topic |
| `trend_analysis` | Analysis of emerging trends |

### Layer 2: Agent Skills (the routines)

Separate from the MCP server. Skills are markdown files that tell agents *how* to use the tools — the sequence, filtering, formatting, and delivery logic.

```
skills/
├── morning-briefing.md    # 7am routine: fetch → digest → summarize → deliver
├── evening-roundup.md     # 7pm routine: trends → highlights → tomorrow preview
├── topic-alert.md         # On-demand: deep dive on a specific topic
└── weekly-synthesis.md    # Weekly: trend analysis + top stories
```

Each skill is a step-by-step playbook the agent follows, calling MCP tools in sequence. This keeps the server atomic and the workflows composable.

### Layer 3: CLI (quick access)

A thin CLI for agents that don't support MCP or need fast one-shot access:

```bash
daily-feed briefing --time morning          # Morning briefing
daily-feed briefing --time evening          # Evening roundup
daily-feed articles --category tech --limit 5  # Top 5 tech articles
daily-feed search "AI regulation"           # Search articles
daily-feed trends                           # Current trends
daily-feed stats                            # System status
```

The CLI calls the same backend API. Stdout is structured JSON by default, human-readable with `--format text`.

### Layer 4: Agent-Friendly API Responses

Existing endpoints get an `Accept: application/vnd.agent+json` header that returns:
- Compact payloads (no HTML, no boilerplate)
- Structured summaries inline (not just IDs)
- Context hints (why this matters, relevance score)
- Token-efficient formatting

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENTS                                    │
│  Claude  │  Codex  │  OpenCode  │  Pi  │  Kilo CLI  │  Any AI   │
└────┬─────┴────┬────┴─────┬──────┴──┬───┴─────┬──────┴──────────┘
     │          │          │         │         │
     ▼          ▼          ▼         ▼         ▼
┌──────────────────────────────────────────────────────────────────┐
│                     AX LAYER                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  MCP Server  │  │ Agent Skills │  │         CLI            │  │
│  │  (FastMCP)   │  │  (markdown)  │  │  (daily-feed command)  │  │
│  │  stdio/SSE   │  │              │  │                        │  │
│  └──────┬───────┘  └──────────────┘  └───────────┬────────────┘  │
│         │                                        │               │
│         ▼                                        ▼               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Agent-Friendly API Layer                        │ │
│  │    Accept: application/vnd.agent+json                       │ │
│  │    Compact payloads · Inline summaries · Context hints      │ │
│  └─────────────────────────────┬───────────────────────────────┘ │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
┌────────────────────────────────┼─────────────────────────────────┐
│                     EXISTING BACKEND                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ FastAPI  │  │Pydantic  │  │ Personal-│  │   Scheduler      │ │
│  │  Routes  │──│  Agents  │──│ ization  │──│   + Memory       │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ LiteLLM  │  │Pydantic  │  │  SQLite  │  │   Voice          │ │
│  │ Routing  │──│  Graph   │──│    DB    │──│   Assistant      │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Key design decisions

**MCP server is a thin wrapper, not a reimplementation.** It calls the existing FastAPI backend via HTTP. This means:
- No duplicate business logic
- Changes to the backend automatically flow through to agents
- The MCP server can run separately or embedded

**Skills are external to the server.** The morning briefing logic lives in a markdown file, not in `generate_briefing()`. Agents compose atomic tools differently for different routines. This is the GeoFeeds pattern: server = API, skill = assembly.

**CLI shares the same API layer.** One codebase, three surfaces (MCP, CLI, REST). The CLI is a thin wrapper around `httpx` calls to the backend.

**Agent-friendly responses are an overlay, not a fork.** The `Accept` header pattern means existing frontend/voice consumers are unaffected. Agents get compact, structured data; humans get the rich UI.

## Tradeoffs accepted

- **MCP server calls HTTP, not direct function calls.** Slight latency overhead (~10ms) in exchange for clean separation and no import coupling.
- **Skills are markdown, not code.** Agents must interpret them. But this makes routines editable without deploying code, and any agent (not just Python ones) can follow them.
- **CLI is a separate entrypoint.** Not every agent supports MCP. The CLI ensures universal access.
- **Agent-friendly responses add a code path.** The `Accept` header branching is a maintenance surface. But it's localized to response serialization, not business logic.

## Alternatives considered

**Embedded MCP server (direct function calls).** Would eliminate HTTP overhead but couples the MCP server to the Python backend internals. Rejected because it breaks the "one codebase, three surfaces" principle — changes to models/services would need coordinated updates.

**All-in-one tool (one `get_briefing` that does everything).** Rejected because it hides the steps from the agent. An agent can't inspect intermediate results, adjust filtering, or retry a failed step. Atomic tools give agents composability and transparency.

**GraphQL for agent queries.** Rejected because MCP is the emerging standard for agent-tool communication, and GraphQL adds schema complexity without solving the agent-specific concerns (structured prompts, tool descriptions, resource URIs).

## Open questions

1. **Auth for MCP:** Should the MCP server use API keys, or should it assume local-only access (stdio)? For remote deployments, how do agents authenticate?
2. **Streaming:** Should `get_briefing` stream partial results as they're generated, or return a complete response? Streaming is better for long-running pipelines but adds complexity.
3. **Multi-user:** The current MCP design assumes a single user. Should it support multiple user profiles (e.g., one for morning briefings, one for work context)?
4. **Notification push:** Should the backend push new digest/trend notifications to agents via webhooks, or should agents poll?

## Next implementation step

Build the MCP server as `backend/app/mcp/server.py` using FastMCP, wrapping the 14 tools above via `httpx` calls to the existing FastAPI endpoints. Add a `morning-briefing.md` skill as the first routine. Add a `daily-feed` CLI entry point.

## File structure

```
backend/
├── app/
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py          # FastMCP server with tools
│   │   ├── resources.py       # MCP resources (digest, trends, config)
│   │   └── prompts.py         # MCP prompts (briefing templates)
│   └── ...

skills/                         # Agent skills (top-level, not inside backend)
├── morning-briefing.md
├── evening-roundup.md
├── topic-deep-dive.md
└── weekly-synthesis.md

cli/
├── __init__.py
├── main.py                    # CLI entry point
├── commands/                  # Subcommands
│   ├── briefing.py
│   ├── articles.py
│   └── trends.py
└── api_client.py              # HTTP client to backend

mcp.json                        # MCP server config for agents
```
