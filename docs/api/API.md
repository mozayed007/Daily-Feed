# Daily Feed API Documentation

Complete API reference for the Daily Feed backend.

**Base URL:** `http://localhost:8000/api/v1`

**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)

---

## 🔐 Authentication

The API uses JWT-based authentication with access tokens (30-minute expiry) and refresh tokens (7-day expiry).

### Register
```http
POST /auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Login
```http
POST /auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Refresh Token
```http
POST /auth/refresh
{
  "refresh_token": "eyJ..."
}

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Forgot Password
```http
POST /auth/forgot-password
{
  "email": "user@example.com"
}

# Response (self-hosted mode returns token directly)
{
  "message": "If an account exists with this email, a reset link has been sent.",
  "reset_token": "eyJ..."
}
```

### Reset Password
```http
POST /auth/reset-password
{
  "token": "eyJ...",
  "new_password": "newsecurepassword"
}

# Response
{
  "message": "Password reset successfully. Please log in with your new password."
}
```

### Logout
```http
POST /auth/logout
{
  "refresh_token": "eyJ..."
}
```

Include token in headers for all authenticated endpoints:
```
Authorization: Bearer <access_token>
```

---

## 📰 Articles

### List Articles
```http
GET /articles?page=1&page_size=20&processed=true&category=AI
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| page | int | 1-based page number |
| page_size | int | Items per page (max 100) |
| processed | bool | Filter by processed status |
| category | string | Filter by category |
| source | string | Filter by source |

**Response:**
```json
{
  "articles": [...],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

### Get Single Article
```http
GET /articles/{id}
```

### Summarize Article
```http
POST /articles/{id}/summarize
```

---

## 📡 Sources

### List Sources
```http
GET /sources
```

### Create Source
```http
POST /sources
{
  "name": "TechCrunch",
  "url": "https://techcrunch.com/feed",
  "category": "Technology",
  "enabled": true
}
```

### Update Source
```http
PUT /sources/{id}
```

### Delete Source
```http
DELETE /sources/{id}
```

---

## 👤 Users & Personalization

### Create User
```http
POST /users
{
  "email": "user@example.com",
  "name": "John Doe"
}
```

### Get Current User
```http
GET /users/me
```

Notes:
- PoC mode resolves to the first available user.
- There is currently no `/users/switch/{id}` endpoint.

### Complete Onboarding
```http
POST /users/onboarding
{
  "name": "John Doe",
  "interests": ["AI", "Technology", "Business"],
  "preferred_sources": ["TechCrunch", "The Verge"],
  "summary_length": "medium",
  "delivery_time": "08:00",
  "daily_limit": 10
}
```

### Get User Stats
```http
GET /users/me/stats
```

**Response:**
```json
{
  "total_articles_read": 47,
  "total_articles_saved": 12,
  "average_reading_time": 145,
  "favorite_topics": [{"topic": "AI", "count": 23}],
  "favorite_sources": [{"source": "TechCrunch", "count": 18}],
  "digest_open_rate": 78.5,
  "last_7_days_activity": [5, 3, 7, 4, 6, 8, 5]
}
```

### Get Preferences
```http
GET /users/me/preferences
```

### Update Preferences
```http
PATCH /users/me/preferences
{
  "topic_interests": {"AI": 0.95, "Tech": 0.8},
  "daily_article_limit": 15,
  "exclude_topics": ["Crypto"]
}
```

### Record Interaction
```http
POST /users/me/interactions
{
  "article_id": 123,
  "opened": true,
  "read_duration_seconds": 180,
  "rating": 1
}
```

### Submit Feedback
```http
POST /users/me/feedback
{
  "article_id": 123,
  "feedback": "like"  // or "dislike", "save", "dismiss"
}
```

### Get Reading History
```http
GET /users/me/history?limit=20&saved_only=false
```

### Generate Personalized Digest
```http
POST /users/me/digest/generate
```

**Response:**
```json
{
  "id": "uuid",
  "created_at": "2026-02-04T20:30:00",
  "articles": [
    {
      "id": 1,
      "title": "AI Breakthrough",
      "score": 0.94,
      "score_breakdown": {
        "topic": 0.9,
        "source": 1.0,
        "freshness": 0.92,
        "quality": 0.75,
        "diversity": 0.5
      }
    }
  ],
  "personalization_score": 0.82
}
```

### List User Digests
```http
GET /users/me/digests?limit=10
```

---

## 🤖 Pipeline

### Run Pipeline Task
```http
POST /pipeline/{task_type}
```

Optional request body:
```json
{
  "params": {
    "article_ids": [1, 2, 3]
  }
}
```

**Task Types:**
- `fetch` - Fetch new articles from RSS feeds
- `process` - Summarize and critique articles (via graph)
- `digest` - Generate digest from processed articles (via graph)
- `full` - Run complete pipeline: fetch → process → digest
- `memory_sync` - Sync with memory system
- `trends` - Detect emerging trends
- `cluster` - Cluster articles by topic
- `synthesize` - Synthesize multiple sources on a topic

**Response:**
```json
{
  "success": true,
  "task_type": "fetch",
  "result": {
    "articles_fetched": 25,
    "sources_processed": 7
  }
}
```

---

## 🛠️ Tools

### List Available Tools
```http
GET /tools
```

### Execute Tool
```http
POST /tools/{tool_name}
{
  "source_id": 1,
  "max_articles": 10
}
```

---

## ⏰ Scheduler

### List Jobs
```http
GET /scheduler/jobs
```

### Create Job
```http
POST /scheduler/jobs
{
  "name": "Evening Digest",
  "type": "cron",
  "cron": "0 18 * * *",
  "enabled": true
}
```

### Delete Job
```http
DELETE /scheduler/jobs/{id}
```

### Start Scheduler
```http
POST /scheduler/start
```

### Stop Scheduler
```http
POST /scheduler/stop
```

---

## 🧠 Memory

### Get Memory Stats
```http
GET /memory/stats
```

### Get User Interests
```http
GET /memory/interests
```

### Remember Article
```http
POST /memory/remember/{article_id}
```

### Search Memory
```http
POST /memory/search
{
  "category": "Technology",
  "entities": ["AI", "machine learning"],
  "limit": 10
}
```

---

## 🤖 AI Agents

### List Available Agents
```http
GET /tools
```

### Run Agent
```http
POST /agents/{agent_name}
```

**Supported agents:** `summarize`, `critique`, `cluster`, `synthesize`, `trends`

**Example — Summarize:**
```http
POST /agents/summarize
{
  "article_id": 42,
  "style": "concise"
}
```

**Example — Cluster:**
```http
POST /agents/cluster
{
  "article_ids": [1, 2, 3, 4, 5]
}
```

**Example — Synthesize:**
```http
POST /agents/synthesize
{
  "topic": "AI Regulation",
  "article_ids": [10, 11, 12]
}
```

**Example — Trends:**
```http
POST /agents/trends
{
  "article_ids": [1, 2, 3]
}
```

---

## 🎙️ Voice Assistant

### Speak Text (TTS)
```http
POST /voice/speak
{
  "text": "Good morning. Here are your top stories.",
  "voice": "jarvis"
}
```

### Run Text Command
```http
POST /voice/command
{
  "text": "What are the latest AI headlines?",
  "voice": "jarvis"
}

# Response
{
  "success": true,
  "thought": "User wants latest AI news",
  "response": "Here are the top AI stories today...",
  "action": "search_web",
  "tool_calls": [
    { "tool": "search_web", "params": { "query": "latest AI headlines" } }
  ]
}
```

### Get Assistant Status
```http
GET /voice/status
```

### Start/Stop Voice Loop
```http
POST /voice/start
POST /voice/stop
```

### Real-Time WebSocket
```
WS /ws/voice
```

Connect for real-time audio streaming (used by the Tauri companion app).

---

## 📊 Stats & Config

### Get App Stats
```http
GET /stats
```

**Response:**
```json
{
  "total_articles": 1250,
  "processed_articles": 980,
  "unprocessed_articles": 270,
  "total_sources": 7,
  "active_sources": 7,
  "total_digests": 45,
  "memory_units": 320
}
```

### Get Config
```http
GET /config
```

### Initialize Config
```http
POST /config/init
```

---

## 🏥 Health

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.1.0",
  "ai_providers": {
    "ollama": { "available": true, "models": ["llama3.2"] },
    "openai": { "available": false },
    "anthropic": { "available": false },
    "gemini": { "available": false }
  },
  "litellm_available": true,
  "agents": ["summarize", "critique", "cluster", "synthesize", "digest_reason", "trend"],
  "graphs": ["article_processing", "digest_generation", "full_pipeline"],
  "scheduler_running": true
}
```

---

## 📦 Digests (Legacy)

### List Digests
```http
GET /digests
```

### Get Digest
```http
GET /digests/{id}
```

---

## 🔴 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Article not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error"
    }
  ]
}
```

### 500 Internal Error
```json
{
  "detail": "Internal server error"
}
```

---

## 📱 Frontend Integration Examples

### React Hook: Use Articles
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

function useArticles(filters?: ArticleFilterParams) {
  return useQuery({
    queryKey: ['articles', filters],
    queryFn: async () => {
      const params = new URLSearchParams(filters as any);
      const res = await fetch(`/api/v1/articles?${params}`);
      return res.json() as Promise<ArticleListResponse>;
    }
  });
}

function usePersonalizedDigest() {
  return useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/v1/users/me/digest/generate', {
        method: 'POST'
      });
      return res.json() as Promise<PersonalizedDigest>;
    }
  });
}

function useArticleFeedback() {
  return useMutation({
    mutationFn: async ({ articleId, feedback }: ArticleFeedbackRequest) => {
      await fetch('/api/v1/users/me/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: articleId, feedback })
      });
    }
  });
}
```

### Vue Composable: Use User Stats
```typescript
import { ref, onMounted } from 'vue';

export function useUserStats() {
  const stats = ref<UserStats | null>(null);
  const loading = ref(false);
  
  async function fetchStats() {
    loading.value = true;
    const res = await fetch('/api/v1/users/me/stats');
    stats.value = await res.json();
    loading.value = false;
  }
  
  onMounted(fetchStats);
  
  return { stats, loading, refresh: fetchStats };
}
```

---

## 🧪 Testing with curl

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Get articles
curl http://localhost:8000/api/v1/articles?limit=5

# Complete onboarding
curl -X POST http://localhost:8000/api/v1/users/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "interests": ["AI", "Technology"],
    "preferred_sources": ["TechCrunch"]
  }'

# Generate digest
curl -X POST http://localhost:8000/api/v1/users/me/digest/generate

# Like an article
curl -X POST http://localhost:8000/api/v1/users/me/feedback \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "feedback": "like"}'
```
