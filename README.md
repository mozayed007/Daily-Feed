# Daily Feed - Personalized News Aggregator

An intelligent, AI-powered news aggregator that learns what you care about and delivers personalized content digests.

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Backend](https://img.shields.io/badge/backend-100%25-blue)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue?logo=python)
![Bun](https://img.shields.io/badge/bun-powered-f9f1e1?logo=bun)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (for backend)
- **Bun** (for frontend) - `curl -fsSL https://bun.sh/install | bash`
- **Ollama** (optional, for local LLM) - `curl -fsSL https://ollama.com/install.sh | sh`
- **Alembic** (included in backend requirements, used for migrations)

### One-Command Setup

```bash
# Clone/navigate to project, then:
make quickstart

# Start both servers:
make backend    # Terminal 1
make frontend   # Terminal 2

# Open http://localhost:5173
```

---

## 📁 Project Structure

```text
daily-feed/
├── README.md              # This file
├── Makefile               # Build commands
├── backend/               # Python FastAPI backend
│   ├── app/               # Application code
│   │   ├── api/           # API routes
│   │   ├── agents/        # LLM-powered agents (summarizer, etc.)
│   │   ├── core/          # Core engine (agent loop, personalization, scheduler)
│   │   ├── models/        # User models
│   │   └── tools/         # RSS tools, fetch tools
│   ├── tests/             # Test suite
│   ├── data/              # SQLite database
│   └── main.py            # Entry point
│
├── frontend/              # React + TypeScript + Bun (web dashboard)
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── hooks/         # React Query hooks
│   │   ├── pages/         # Page components
│   │   ├── lib/           # API client, utils
│   │   └── types/         # TypeScript types
│   └── package.json
│
├── companion/             # Tauri v2 desktop voice assistant (NEW)
│   ├── src-tauri/         # Rust core (audio, tray, shortcuts, WebSocket)
│   └── src/               # React + Tailwind webview UI
│
└── docs/                  # Documentation
    ├── api/               # API reference & types
    ├── guides/            # User guides
    └── architecture/      # Technical design docs
```

---

## ✨ Features

### 🤖 Core Intelligence

- **Pydantic-AI Agent System** - Type-safe AI agents with structured outputs (SummaryResult, CritiqueResult, ClusterList, etc.)
- **LiteLLM Universal Routing** - Single interface to 100+ LLM providers (Ollama, OpenAI, Anthropic, Gemini, Azure, Bedrock, Cohere, Mistral, Groq, and more)
- **Pydantic-Graph Workflows** - Parallel execution graphs for article processing, digest generation, and full pipeline
- **Smart Summarization** - AI-generated summaries with structured Pydantic output models
- **Content Critique** - Quality scoring with structured multi-factor evaluation
- **Multi-Source Synthesis** - AI merges coverage from multiple sources into unified narratives
- **Article Clustering** - AI groups related articles by topic with confidence scores
- **Trend Detection** - AI identifies rising topics, breaking stories, and emerging narratives

### 🎙️ Voice Assistant (Jarvis / Friday) — 100% Local AI

- **Local STT** — `distil-whisper/distil-large-v3` via faster-whisper (CTranslate2)
  - 49% faster than Whisper large-v3, ~1% WER difference
  - Apache 2.0 weights on Hugging Face, runs offline on CPU/GPU
- **Local TTS** — `Kokoro-82M` via ONNX Runtime
  - 82M param open-weight model, ~300 MB, real-time on CPU
  - Apache 2.0 weights: `hexgrad/Kokoro-82M` / `onnx-community/Kokoro-82M-v1.0-ONNX`
  - Voices: `am_adam` (Jarvis), `af_heart` (Friday)
- **Wake-Word Detection** — "Hey Jarvis" / "Hey Friday" activation
- **Push-to-Talk** — Alternative hold-to-speak mode
- **Tool Calling** — pydantic-ai agents call backend tools via natural voice commands
- **Web Search** — DuckDuckGo integration for live information (no API key)
- **Dashboard Launcher** — Voice command opens the web frontend when visuals needed
- **Tauri Desktop Companion** — Standalone always-on-top app with system tray, global shortcuts, and voice interaction

### 🎯 Personalization Engine

- **Interest Learning** - Adapts to your reading patterns
- **Topic Preferences** - Weighted interest system (0-1 scores)
- **Source Ranking** - Prioritize trusted publishers
- **Feedback Loop** - Like/dislike improves recommendations
- **Diversity Protection** - Avoid filter bubbles with diversity scoring
- **Freshness Scoring** - Prioritize recent content

### ⚙️ Automation

- **RSS Aggregation** - 7+ pre-configured news sources
- **Built-in Scheduler** - Cron-based jobs with no external dependencies
- **Auto-Delivery** - Daily personalized digests
- **Memory System** - Long-term user understanding

### 🔧 Technical Features

- **FastAPI Backend** - Async, high-performance REST API
- **Pydantic-AI + LiteLLM** - Type-safe AI agents with universal LLM provider routing
- **Pydantic-Graph** - Parallel graph-based workflow execution (Beta API)
- **SQLite Database** - Zero-config local storage with SQLAlchemy
- **React Frontend** - Modern UI with TanStack Query
- **Tailwind CSS** - Beautiful, responsive design
- **Full Type Safety** - TypeScript frontend, Pydantic backend

---

## 🛠️ Development Commands

```bash
# Backend
make backend-setup    # Install deps, init db, seed data
make backend          # Start server (http://localhost:8000)
make backend-test     # Run pytest tests
make backend-demo     # Run personalization demo

# Frontend
make frontend-setup   # Install Bun dependencies
make frontend         # Start dev server (http://localhost:5173)
make frontend-build   # Production build
make frontend-lint    # Lint frontend
make frontend-typecheck # Type-check frontend

# Companion App (Tauri Desktop)
cd companion
npm install           # Install deps
npm run tauri dev     # Dev mode with hot reload
npm run tauri build   # Release build (creates .msi / .dmg)

# General
make test             # Run all tests
make clean            # Clean temp files
make info             # Show project info
```

### Code Quality

```bash
# Backend formatting
cd backend && black app/ && isort app/

# Backend type checking (optional in current setup)
cd backend && mypy app/

# Frontend lint/format
make frontend-lint
cd frontend && bun run format
```

---

## 📚 Documentation

| Document         | Location                                | Description               |
| ---------------- | --------------------------------------- | ------------------------- |
| API Reference    | `docs/api/API.md`                       | Complete REST API docs    |
| TypeScript Types | `docs/api/API_TYPES.ts`                 | Frontend type definitions |
| Frontend Guide   | `docs/guides/FRONTEND_STARTER_GUIDE.md` | Getting started with Bun  |
| Personalization  | `docs/guides/PERSONALIZATION_GUIDE.md`  | How personalization works |
| Architecture     | `docs/architecture/`                    | Technical design          |

**Interactive API docs:** `http://localhost:8000/docs` (Swagger UI)

---

## 🧪 Testing

```bash
# Backend tests (pytest)
make backend-test

# Or directly
cd backend && pytest -v
cd backend && pytest --cov
# Frontend quality checks
make frontend-typecheck
make frontend-lint
```

Frontend unit/integration tests are not implemented yet in this repository; use type-checking and linting as the current frontend quality gates.

**Backend Coverage Includes:**

- API endpoints
- Personalization engine
- Scheduler & cron parser
- Tool functionality
- Logging system

---

## 🔌 API Overview

### Core Endpoints

```text
GET  /api/v1/health                    # Health check
GET  /api/v1/articles                  # List articles (with filters)
GET  /api/v1/articles/{id}             # Get article
POST /api/v1/articles/{id}/summarize   # Summarize article
GET  /api/v1/sources                   # List sources
POST /api/v1/pipeline/{task_type}      # Run pipeline (fetch/process/digest/full/memory_sync)
```

### Personalization Endpoints

```text
POST /api/v1/users/onboarding          # Complete onboarding
GET  /api/v1/users/me                  # Get current user
GET  /api/v1/users/me/stats            # User statistics
GET  /api/v1/users/me/preferences      # Get preferences
PATCH /api/v1/users/me/preferences     # Update preferences
POST /api/v1/users/me/feedback         # Like/dislike article
POST /api/v1/users/me/digest/generate  # Generate personalized digest
```

### Scheduler Endpoints

```text
GET  /api/v1/scheduler/jobs            # List scheduled jobs
POST /api/v1/scheduler/jobs            # Create job
POST /api/v1/scheduler/start           # Start scheduler
POST /api/v1/scheduler/stop            # Stop scheduler
```

### Voice Assistant Endpoints

```text
POST /api/v1/voice/speak               # TTS: speak text aloud
POST /api/v1/voice/command             # Run a text command through Jarvis
GET  /api/v1/voice/status              # Assistant status
POST /api/v1/voice/stop                # Stop active voice loop
WS   /api/v1/ws/voice                  # WebSocket for real-time voice chat (used by companion app)
```

---

## 🏗️ Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│                    DAILY FEED ARCHITECTURE                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Frontend   │────│   FastAPI   │────│  SQLite DB  │         │
│  │  React/Vite │    │   Backend   │    │  + Models   │         │
│  └─────────────┘    └──────┬──────┘    └─────────────┘         │
│                            │                                   │
│  ┌─────────────────────────┼─────────────────────────┐         │
│  │              PYDANTIC-AI AGENTS                   │         │
│  ├─────────────────────────┼─────────────────────────┤         │
│  │  ┌──────────┐  ┌────────┴───────┐  ┌──────────┐   │         │
│  │  │Summarize │  │   Critique     │  │  Cluster │   │         │
│  │  │  Agent   │  │    Agent       │  │  Agent   │   │         │
│  │  └──────────┘  └────────────────┘  └──────────┘   │         │
│  │  ┌──────────┐  ┌────────┴───────┐  ┌──────────┐   │         │
│  │  │ Synthe-  │  │ Digest Reason  │  │  Trend   │   │         │
│  │  │  size    │  │    Agent       │  │  Agent   │   │         │
│  │  └──────────┘  └────────────────┘  └──────────┘   │         │
│  └───────────────────────────────────────────────────┘         │
│                            │                                   │
│  ┌─────────────────────────┼─────────────────────────┐         │
│  │            PYDANTIC-GRAPH WORKFLOWS               │         │
│  ├─────────────────────────┼─────────────────────────┤         │
│  │  ┌──────────┐  ┌────────┴───────┐  ┌──────────┐   │         │
│  │  │ Article  │  │   Digest       │  │   Full   │   │         │
│  │  │Processing│  │  Generation    │  │ Pipeline │   │         │
│  │  │  Graph   │  │    Graph       │  │  Graph   │   │         │
│  │  └──────────┘  └────────────────┘  └──────────┘   │         │
│  └───────────────────────────────────────────────────┘         │
│                                                                │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              PERSONALIZATION ENGINE                 │       │
│  │  • Interest scoring    • Diversity protection       │       │
│  │  • Source ranking      • Feedback learning          │       │
│  │  • Freshness decay     • Topic weighting            │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                   SCHEDULER                         │       │
│  │  • Cron expressions    • Interval jobs              │       │
│  │  • Daily digest        • Auto-fetch                 │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              LITELLM LLM ROUTING                    │       │
│  │  • 100+ Providers      • Structured Outputs         │       │
│  │  • Type-Safe Agents    • Universal API              │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              VOICE ASSISTANT (JARVIS/FRIDAY)        │       │
│  │  • Distil-Whisper STT   • Kokoro-82M TTS (ONNX)     │       │
│  │  • Wake-word activation   • Push-to-talk mode         │       │
│  │  • pydantic-ai brain      • WebSocket companion       │       │
│  │  • HuggingFace weights    • 100% offline              │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 📊 Project Stats

```text
Backend:     ~12,000 LOC, 50+ files
Frontend:    React + TypeScript + Tailwind + Vite
AI Stack:    Pydantic-AI + Pydantic-Graph + LiteLLM
Tests:       Comprehensive pytest + Vitest + Playwright E2E
API:         40+ endpoints
Docs:        5 comprehensive guides
```

---

## 🎯 Roadmap

### ✅ Completed

- [x] Core agent loop with memory
- [x] 5+ pluggable tools (fetch, summarize, critique, memory, delivery)
- [x] Personalization engine with diversity protection
- [x] User preferences & feedback learning
- [x] Built-in cron scheduler
- [x] Full REST API (35+ endpoints)
- [x] React + Bun frontend
- [x] Comprehensive test suite

### 🚧 Completed (Finalized)

- [x] Onboarding wizard UI
- [x] Stats dashboard with charts
- [x] Preferences panel
- [x] Mobile responsive design
- [x] Production-ready auth (password reset, change password, email verification)
- [x] OAuth login (Google, GitHub)
- [x] Article search (backend + frontend)
- [x] Article detail page with interaction tracking
- [x] Empty states and confirmation dialogs
- [x] Frontend nginx serving in Docker
- [x] Frontend unit tests (Vitest + RTL)
- [x] Backend auth & scheduler tests
- [x] Playwright E2E smoke tests
- [x] **Pydantic-AI agents** with structured outputs (summarize, critique, cluster, synthesize, reason, trend)
- [x] **LiteLLM universal LLM routing** (100+ providers via single interface)
- [x] **Pydantic-Graph parallel workflows** (article processing, digest generation, full pipeline)
- [x] **Multi-source synthesis** - AI merges coverage from multiple sources
- [x] **Article clustering** - AI groups related articles by topic
- [x] **Trend detection** - AI identifies emerging topics and breaking stories
- [x] **Smart digest reasoning** - AI explains why articles match user interests
- [x] **Trends page** - Frontend for AI trend detection
- [x] **Voice Assistant (Jarvis/Friday)** - Local STT/TTS, wake-word, push-to-talk, tool calling, web search, dashboard launcher
- [x] **Tauri Desktop Companion** - Standalone Rust + React app with system tray, global shortcuts, CPAL audio, WebSocket backend connection

---

## 🔧 Configuration

### Environment Variables

| Variable            | Description                                   | Default                               |
| ------------------- | --------------------------------------------- | ------------------------------------- |
| `DAILYFEED_LLM_PROVIDER` | LLM provider (ollama/openai/anthropic/gemini) | ollama                           |
| `DAILYFEED_OLLAMA_URL`   | Ollama server URL                             | `http://localhost:11434`         |
| `DAILYFEED_OLLAMA_MODEL` | Model to use                                  | llama3.2                           |
| `OPENAI_API_KEY`         | OpenAI API key                                | -                                  |
| `ANTHROPIC_API_KEY`      | Anthropic API key                             | -                                  |
| `GEMINI_API_KEY`         | Google Gemini API key                         | -                                  |
| `DAILYFEED_DATABASE_URL` | SQLite connection string                      | sqlite+aiosqlite:///data/dailyfeed.db |

Most runtime config keys use the `DAILYFEED_` prefix. API keys are read directly without that prefix.

## 🗄️ Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "describe_change"

# Apply migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Make your changes
4. Run tests (`make test`)
5. Commit (`git commit -m 'feat: add amazing feature'`)
6. Push (`git push origin feature/amazing`)
7. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ using Python, FastAPI, React, and Bun** 🥟
