# Daily Feed - Personalized News Aggregator

An intelligent, AI-powered news aggregator that learns what you care about and delivers personalized content digests.

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Backend](https://img.shields.io/badge/backend-100%25-blue)
![Tests](https://img.shields.io/badge/tests-35%20passing-brightgreen)
![Bun](https://img.shields.io/badge/bun-powered-f9f1e1?logo=bun)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (for backend)
- **Bun** (for frontend) - `curl -fsSL https://bun.sh/install | bash`

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

```
daily-feed/
├── README.md              # This file
├── Makefile              # Build commands
├── backend/              # Python FastAPI backend
│   ├── app/             # Application code
│   │   ├── api/        # API routes
│   │   ├── core/       # Core engine (agent loop, personalization)
│   │   ├── models/     # User models
│   │   └── tools/      # RSS tools, LLM tools
│   ├── scripts/        # Utility scripts
│   │   ├── init_db.py
│   │   ├── seed_demo.py
│   │   └── demo_personalization.py
│   ├── tests/          # Test suite
│   ├── data/           # SQLite database
│   └── main.py         # Entry point
│
├── frontend/            # React + TypeScript + Bun
│   ├── src/
│   │   ├── hooks/     # React Query hooks
│   │   ├── pages/     # Page components
│   │   ├── lib/       # API client, utils
│   │   └── types/     # TypeScript types
│   └── package.json
│
└── docs/               # Documentation
    ├── api/           # API reference & types
    ├── guides/        # User guides
    └── architecture/  # Technical design docs
```

---

## ✨ Features

### 🤖 Core Intelligence

- **Agent Loop Architecture** - Dynamic task execution
- **Multi-LLM Support** - Ollama, OpenAI, Anthropic
- **Smart Summarization** - AI-generated summaries
- **Content Critique** - Quality scoring

### 🎯 Personalization

- **Interest Learning** - Adapts to your reading patterns
- **Topic Preferences** - Weighted interest system
- **Source Ranking** - Prioritize trusted publishers
- **Feedback Loop** - Like/dislike improves recommendations
- **Diversity Protection** - Avoid filter bubbles

### ⚙️ Automation

- **RSS Aggregation** - 7 pre-configured sources
- **Built-in Scheduler** - Cron-based jobs
- **Auto-Delivery** - Daily digests
- **Memory System** - Long-term understanding

---

## 🛠️ Development Commands

```bash
# Backend
make backend-setup    # Install deps, init db, seed data
make backend          # Start server
make backend-test     # Run tests
make backend-demo     # Run personalization demo

# Frontend
make frontend-setup   # Install Bun dependencies
make frontend         # Start dev server
make frontend-build   # Production build

# General
make test            # Run all tests
make clean           # Clean temp files
make info            # Show project info
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

Interactive API docs: `http://localhost:8000/docs`

---

## 🧪 Testing

```bash
# Backend tests
make backend-test

# Frontend type check
make frontend-typecheck
```

**35 tests passing** covering:

- API endpoints
- Personalization engine
- Tool functionality
- Logging system

---

## 🔌 API Overview

### Core Endpoints

```
GET  /api/v1/articles              # List articles
GET  /api/v1/articles/{id}         # Get article
POST /api/v1/articles/{id}/summarize
GET  /api/v1/sources               # List sources
POST /api/v1/pipeline/{task}       # Run pipeline
```

### Personalization Endpoints

```
POST /api/v1/users/onboarding      # Complete onboarding
GET  /api/v1/users/me/stats        # User stats
GET  /api/v1/users/me/preferences  # Get preferences
PATCH /api/v1/users/me/preferences # Update preferences
POST /api/v1/users/me/feedback     # Article feedback
POST /api/v1/users/me/digest/generate # Get personalized digest
```

---

## 🥟 Why Bun?

```bash
# 10x faster than npm
bun install        # ⚡️ ~1 second
npm install        # 🐌 ~10 seconds

# Built-in TypeScript
bun run script.ts  # No ts-node needed!

# Hot reload
bun run dev        # Lightning fast HMR
```

---

## 📊 Project Stats

```
Backend:     ~8,000 LOC, 37 files
Frontend:    React + TypeScript + Tailwind
Tests:       35 tests passing
API:         33 endpoints
Docs:        5 comprehensive guides
```

---

## 🎯 Roadmap

### ✅ Completed

- [x] Core agent loop
- [x] 5 pluggable tools
- [x] Personalization engine
- [x] User preferences
- [x] Feedback learning
- [x] REST API
- [x] Bun frontend template

### 🚧 Next

- [ ] Onboarding wizard UI
- [ ] Stats dashboard
- [ ] Preferences panel
- [ ] Mobile responsive design

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run `make test`
4. Submit PR

---

## 📄 License

MIT License

---

**Built with ❤️ using Python, FastAPI, and Bun** 🥟
