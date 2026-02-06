# Frontend Starter Guide - Daily Feed

Welcome! This guide will get you started building the Daily Feed frontend.

---

## 🚀 Quick Start (5 minutes)

### 1. Start the Backend

```bash
cd backend

# Install dependencies (if not done)
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Seed with demo data
python scripts/seed_demo.py

# Start the server
python main.py
```

Backend will be at: `http://localhost:8000`

API Docs: `http://localhost:8000/docs`

### ⚡ Bun-One-Liner (Frontend)

```bash
# From project root
make frontend-setup && make frontend
```

Then open `http://localhost:5173` 🎉

### 2. Create Your Frontend (with Bun! 🥟)

#### Option A: Use Our Template (Recommended)

The frontend template is already at `frontend/` - just install and run!

```bash
# From project root
cd frontend

# Install with Bun
bun install

# Start!
bun run dev
```

#### Option B: From Scratch

```bash
# Create a new Vite + React + TypeScript project
cd ..
bun create vite@latest my-frontend -- --template react-ts
cd my-frontend

# Install all dependencies in one go (Bun is fast! ⚡️)
bun install @tanstack/react-query axios recharts lucide-react clsx tailwind-merge

# Install dev dependencies
bun install -D tailwindcss postcss autoprefixer
bunx tailwindcss init -p
```

**Why Bun?**
- ⚡️ **10x faster** than npm
- 🥟 **Built-in TypeScript** support
- 📦 **Single binary** - no node_modules bloat
- 🔥 **Hot reload** is blazing fast
- ✨ **Compatible** with all Vite/React tooling

### 3. Copy API Types

```bash
# Copy the TypeScript types (if using Option B from scratch)
cp ../docs/api/API_TYPES.ts src/types/api.ts
```

### 4. Configure API Client

Create `src/lib/api.ts`:

```typescript
import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
```

### 5. Create Query Client

Create `src/lib/queryClient.ts`:

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
    },
  },
});
```

---

## 📁 Recommended Folder Structure

```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Buttons, inputs, cards
│   ├── articles/        # Article card, article list
│   ├── digest/          # Digest view, digest list
│   └── preferences/     # Preference forms
├── hooks/               # Custom React hooks
│   ├── useArticles.ts
│   ├── useDigest.ts
│   ├── usePreferences.ts
│   └── useUser.ts
├── lib/                 # Utilities
│   ├── api.ts          # Axios instance
│   ├── queryClient.ts  # React Query setup
│   └── utils.ts        # Helper functions
├── pages/               # Page components
│   ├── Home.tsx
│   ├── Digest.tsx
│   ├── Preferences.tsx
│   └── Onboarding.tsx
├── types/               # TypeScript types
│   └── api.ts          # From docs/API_TYPES.ts
└── App.tsx
```

---

## 🧪 Test the API

### Get Demo User Stats
```bash
curl http://localhost:8000/api/v1/users/me/stats
```

### Generate Personalized Digest
```bash
curl -X POST http://localhost:8000/api/v1/users/me/digest/generate
```

### Get Articles
```bash
curl http://localhost:8000/api/v1/articles?limit=5
```

---

## 🎨 Key UI Components to Build

### 1. Onboarding Flow (3 steps)

```typescript
// Step 1: Welcome + Name
// Step 2: Interest Selection (chips)
const TOPICS = ['AI', 'Technology', 'Business', 'Science', 'Crypto'];

// Step 3: Source Preferences + Delivery Time
// Sources: TechCrunch, The Verge, Hacker News, etc.
```

### 2. Article Card

```typescript
interface ArticleCardProps {
  article: PersonalizedArticle;
  onLike: () => void;
  onSave: () => void;
  onDismiss: () => void;
}
```

Features:
- Title + source + category badge
- Summary (collapsible)
- Score breakdown (optional tooltip)
- Like ❤️ / Save 🔖 / Dismiss ✕ buttons
- Reading time estimate

### 3. Personalized Feed

```typescript
// Infinite scroll feed
// Group by digest
// Pull-to-refresh
```

### 4. Stats Dashboard

```typescript
// Charts to build:
// - Reading activity (bar chart, last 7 days)
// - Topic distribution (pie/donut chart)
// - Source breakdown (horizontal bar)
// - Open rate metric (big number)
```

### 5. Preferences Panel

```typescript
// Sliders for topic interests (0-100%)
// Toggle switches for sources
// Blocked topics/sources list
// Summary length selector
// Delivery time picker
// Daily limit number input
```

---

## 🔄 React Query Hooks Example

### useArticles.ts

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { ArticleListResponse } from '../types/api';

export function useArticles(limit = 20) {
  return useQuery({
    queryKey: ['articles', limit],
    queryFn: async () => {
      const { data } = await api.get<ArticleListResponse>(
        `/articles?limit=${limit}`
      );
      return data;
    },
  });
}
```

### usePersonalizedDigest.ts

```typescript
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { PersonalizedDigest } from '../types/api';

export function useGenerateDigest() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<PersonalizedDigest>(
        '/users/me/digest/generate'
      );
      return data;
    },
  });
}
```

### useFeedback.ts

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

export function useArticleFeedback() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ 
      articleId, 
      feedback 
    }: { 
      articleId: number; 
      feedback: string 
    }) => {
      await api.post('/users/me/feedback', {
        article_id: articleId,
        feedback,
      });
    },
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['articles'] });
    },
  });
}
```

---

## 🎨 Design System Suggestions

### Colors (Tailwind)

```javascript
// tailwind.config.js
colors: {
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
  },
  // Topic colors
  ai: '#8b5cf6',      // Violet
  tech: '#06b6d4',    // Cyan
  business: '#f59e0b', // Amber
  science: '#10b981',  // Emerald
}
```

### Typography

```css
/* Use Inter or System font */
font-family: 'Inter', system-ui, sans-serif;

/* Scale */
text-xs: 12px   /* Captions */
text-sm: 14px   /* Secondary */
text-base: 16px /* Body */
text-lg: 18px   /* Lead */
text-xl: 20px   /* H3 */
text-2xl: 24px  /* H2 */
text-3xl: 30px  /* H1 */
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile first */
sm: 640px   /* Small tablets */
md: 768px   /* Tablets */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
```

---

## 🥟 Bun Commands Cheat Sheet

```bash
# Development (hot reload)
bun run dev

# Install package
bun install <package>

# Install dev dependency
bun install -D <package>

# Run TypeScript directly (no ts-node needed!)
bun run script.ts

# Run tests
bun test

# Build for production
bun run build

# Format with Prettier
bunx prettier --write .

# Lint with ESLint
bunx eslint src/
```

**Bun-only perks for this project:**
```bash
# Copy types with Bun's fast IO
bun run -e "await Bun.write('src/types/api.ts', await Bun.file('../docs/API_TYPES.ts').text())"

# Quick API test
bun run -e "const res = await fetch('http://localhost:8000/api/v1/health'); console.log(await res.json())"
```

## 🔧 VS Code Extensions

Recommended:
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- TypeScript Importer
- Prettier - Code: formatter
- ESLint

**Bun tip:** Add to your VS Code settings.json:
```json
{
  "npm.packageManager": "bun",
  "typescript.tsdk": "./node_modules/typescript/lib"
}
```

---

## 🐛 Common Issues

### CORS Errors
Backend CORS is configured for:
- `http://localhost:3000` (Create React App)
- `http://localhost:5173` (Vite)

If using a different port, add it in `back/app/core/config_manager.py`:
```python
cors_origins: List[str] = field(default_factory=lambda: [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:YOUR_PORT",
])
```

### TypeScript Errors
Make sure to copy the latest types from `docs/API_TYPES.ts`

---

## 🚀 Deployment

### Build for Production

```bash
cd front

# With Bun (recommended)
bun run build

# Or traditional npm
npm run build
```

### Serve with Backend
The backend can serve the static files:

```python
# In main.py, add:
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="../front/dist", html=True))
```

---

## 📚 Next Steps

1. ✅ Start with the Onboarding flow
2. ✅ Build the Article Card component
3. ✅ Create the Personalized Feed page
4. ✅ Add the Stats Dashboard
5. ✅ Implement Preferences panel
6. ✅ Polish with animations and transitions

---

## 🆘 Getting Help

- API Docs: `http://localhost:8000/docs`
- Backend README: `back/README.md`
- API Types: `docs/API_TYPES.ts`
- Full API Reference: `docs/API.md`

Happy coding! 🎉
