# Backend Issues & Missing Components

## 🔴 Critical Issues (Will Break Application)

### 1. StatsResponse Model Mismatch
**Files:** `app/database.py` vs `app/api/routes_v2.py`

- `database.py` defines `StatsResponse` without `memory_units` field
- `routes_v2.py` line 425 tries to return `memory_units=mem_stats.get("total_units", 0)`
- **Fix:** Add `memory_units: Optional[int] = None` to StatsResponse

```python
class StatsResponse(BaseModel):
    total_articles: int
    processed_articles: int
    unprocessed_articles: int
    total_digests: int
    total_sources: int
    active_sources: int
    categories: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    memory_units: Optional[int] = None  # <-- ADD THIS
```

---

### 2. Deprecated SQLAlchemy Syntax
**File:** `app/api/routes_v2.py` lines 379, 384

Using `.from_statement()` with count queries is deprecated/wrong.

**Current (Broken):**
```python
active_result = await db.execute(
    select(func.count())
    .from_statement(select(SourceModel).where(SourceModel.enabled == True))
)
```

**Fix:**
```python
active_result = await db.execute(
    select(func.count()).select_from(SourceModel).where(SourceModel.enabled == True)
)
```

---

### 3. Dual Config System Conflict
**Files:** Multiple files importing from old `app.config`

Files still using old config:
- `app/database.py:16`
- `app/agents/delivery.py:14`
- `app/api/routes.py:22`
- `app/core/llm_client.py:15`
- `app/core/memory.py:14`

**Problem:** Two config systems exist side-by-side:
1. Old: `app.config.Settings` (Pydantic)
2. New: `app.core.config_manager.AppConfig` (Dataclass + JSON)

**Fix:** Migrate all imports to use `app.core.config_manager` or remove old system entirely.

---

### 4. Missing Retry Logic on Critique Tool
**File:** `app/tools/critique_tool.py`

We added retry to `summarize_tool.py` but not to `critique_tool.py`. LLM calls can fail.

**Fix:** Add same tenacity retry decorator as summarize_tool:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def _critique(self, article: ArticleModel) -> Dict[str, Any]:
```

---

## 🟡 Missing Components

### 5. No Tests Directory
**Missing:** `back/tests/` with test files

Should have:
- `tests/test_tools.py` - Test each tool
- `tests/test_api.py` - Test API endpoints
- `tests/test_scheduler.py` - Test job scheduling
- `tests/test_memory.py` - Test memory operations
- `tests/conftest.py` - Test fixtures

---

### 6. Missing CLI/Admin Commands
**Missing:** Command-line interface for:
- Initialize config
- Add/remove sources
- Run pipelines manually
- View logs
- Reset database

**Example:**
```bash
python -m dailyfeed init
python -m dailyfeed sources add "Name" "URL" 
python -m dailyfeed pipeline run fetch
```

---

### 7. Missing Middleware
**Missing:**
- Request ID middleware (for tracing)
- Rate limiting middleware
- Authentication middleware (optional but recommended)
- Logging middleware

---

### 8. No Database Migration System
**Missing:** Alembic migrations

Without migrations, schema changes require dropping tables.

---

### 9. Incomplete Error Handling
**Missing:**
- Custom exception classes
- Proper HTTP status codes for all errors
- Error detail standardization

---

### 10. Missing API Endpoints
**Missing endpoints:**
- `PUT /api/v1/sources/{id}` - Update source (only POST and DELETE exist)
- `GET /api/v1/digests/{id}` - Get single digest with articles
- `POST /api/v1/scheduler/jobs` - Add custom job (defined but not fully implemented)
- `DELETE /api/v1/scheduler/jobs/{id}` - Remove scheduled job
- `POST /api/v1/articles/{id}/summarize` - Single article summarize (exists in routes.py but not routes_v2.py)

---

## 🟢 Nice to Have

### 11. Missing Documentation
**Missing:**
- API documentation (OpenAPI/Swagger is auto-generated but needs descriptions)
- Architecture diagrams
- Deployment guide
- Environment setup guide

---

### 12. Missing Monitoring/Observability
**Missing:**
- Health check with DB connectivity test
- Prometheus metrics
- Structured logging (using structlog)
- Request tracing

---

### 13. Missing Background Task Queue
**Current:** Uses in-memory scheduler only

**Better:** Add Redis + Celery or ARQ for:
- Distributed task processing
- Task persistence across restarts
- Better scalability

---

## 📋 Fix Priority List

### Immediate (Do First)
1. ✅ Fix StatsResponse model (add memory_units)
2. ✅ Fix SQLAlchemy from_statement deprecation
3. ✅ Add retry to critique_tool.py

### This Week
4. Migrate all config imports to new system
5. Add missing API endpoints (PUT sources, GET digest by id)
6. Create tests directory with basic tests

### Next Sprint
7. Add CLI commands
8. Add middleware (request ID, rate limiting)
9. Setup Alembic migrations

---

## 🔧 Quick Fixes Needed

### Fix 1: Update StatsResponse
```python
# app/database.py line 233
class StatsResponse(BaseModel):
    total_articles: int
    processed_articles: int
    unprocessed_articles: int
    total_digests: int
    total_sources: int
    active_sources: int
    categories: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    memory_units: Optional[int] = None  # ADD THIS LINE
```

### Fix 2: Fix SQLAlchemy Queries
```python
# app/api/routes_v2.py line 377-379
active_result = await db.execute(
    select(func.count()).select_from(SourceModel).where(SourceModel.enabled == True)
)

# Line 384
digests_result = await db.execute(
    select(func.count()).select_from(DigestModel)
)
```

### Fix 3: Add Retry to Critique
```python
# app/tools/critique_tool.py - Add imports and decorator
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _critique(self, article: ArticleModel) -> Dict[str, Any]:
```

---

## Summary Table

| Issue | Severity | File(s) | Status |
|-------|----------|---------|--------|
| StatsResponse mismatch | 🔴 Critical | database.py | Not Fixed |
| SQLAlchemy from_statement | 🔴 Critical | routes_v2.py | Not Fixed |
| Missing retry on critique | 🟡 High | critique_tool.py | Not Fixed |
| Dual config system | 🟡 High | Multiple | Not Fixed |
| No tests | 🟡 Medium | - | Missing |
| Missing API endpoints | 🟡 Medium | routes_v2.py | Missing |
| No CLI | 🟢 Low | - | Missing |
| No migrations | 🟢 Low | - | Missing |

**Total Critical Issues:** 2
**Total Missing Components:** 6
