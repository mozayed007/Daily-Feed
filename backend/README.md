# Daily Feed - News Aggregator Backend

FastAPI-based backend for local news aggregation with LLM-powered summarization.

## Features

- 🤖 **Multi-Agent Architecture** - Feed Retriever, Summarizer, Quality Critic, Delivery
- 🧠 **Local LLM Support** - Ollama integration (llama3.2, qwen2.5, mistral, etc.)
- 📰 **RSS Aggregation** - Fetch from multiple news sources
- 💾 **SQLite Database** - Zero-config local storage
- 💬 **Telegram Delivery** - Bot API integration
- 🚀 **FastAPI** - Modern, fast web framework

## Quick Start

### 1. Install Dependencies

```bash
cd back
pip install -r requirements.txt
```

### 2. Install Ollama (for local LLMs)

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.2
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health
- `GET /api/v1/health` - System health check

### Articles
- `GET /api/v1/articles` - List articles with filtering
- `GET /api/v1/articles/{id}` - Get single article
- `POST /api/v1/articles/{id}/summarize` - Summarize article

### Sources
- `GET /api/v1/sources` - List RSS sources
- `POST /api/v1/sources` - Create new source
- `PUT /api/v1/sources/{id}` - Update source
- `DELETE /api/v1/sources/{id}` - Delete source
- `POST /api/v1/sources/{id}/fetch` - Fetch from source

### Pipeline
- `POST /api/v1/pipeline/fetch` - Run fetch pipeline
- `POST /api/v1/pipeline/process` - Run AI processing pipeline
- `POST /api/v1/pipeline/digest` - Create digest

### Digests
- `GET /api/v1/digests` - List digests
- `GET /api/v1/digests/{id}` - Get digest details

### Stats
- `GET /api/v1/stats` - System statistics

### Settings
- `GET /api/v1/settings` - Get current settings

## Project Structure

```
back/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── database.py        # Database models and operations
│   ├── main.py            # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py      # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── llm_client.py  # LLM client implementations
│   └── agents/
│       ├── __init__.py
│       ├── retriever.py   # Feed Retriever Agent
│       ├── summarizer.py  # Summarizer Agent
│       ├── critic.py      # Quality Critic Agent
│       └── delivery.py    # Delivery Agent
├── data/                  # SQLite database
├── requirements.txt
├── .env.example
└── README.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (ollama/openai/anthropic) | ollama |
| `OLLAMA_URL` | Ollama server URL | http://localhost:11434 |
| `OLLAMA_MODEL` | Model to use | llama3.2 |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | - |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | - |
| `DATABASE_URL` | Database connection string | sqlite+aiosqlite:///data/dailyfeed.db |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1️⃣ FEED RETRIEVER AGENT                                     │
│     - Fetches RSS feeds                                      │
│     - Extracts content                                       │
│     - Deduplicates                                           │
│                                                              │
│  2️⃣ SUMMARIZER AGENT                                         │
│     - Calls Ollama API                                       │
│     - Generates summaries                                    │
│     - Categorizes & analyzes sentiment                       │
│                                                              │
│  3️⃣ QUALITY CRITIC AGENT                                     │
│     - Checks accuracy                                        │
│     - Validates facts                                        │
│     - Scores 1-10, rejects low quality                       │
│                                                              │
│  4️⃣ DELIVERY AGENT                                           │
│     - Formats digest                                         │
│     - Sends via Telegram                                     │
│     - Tracks delivery                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## License

MIT
