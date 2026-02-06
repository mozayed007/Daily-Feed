# Daily Feed - Frontend Template

A modern, fast frontend for Daily Feed built with **Bun** + **Vite** + **React** + **TypeScript**.

## 🚀 Quick Start

### Prerequisites
- [Bun](https://bun.sh/) installed (`curl -fsSL https://bun.sh/install | bash`)
- Backend running on `http://localhost:8000`

### Install & Run

```bash
# Install dependencies
bun install

# Copy environment variables
cp .env.example .env

# Start development server
bun run dev
```

Open `http://localhost:5173` 🎉

---

## 📁 Project Structure

```
src/
├── components/          # UI components
│   ├── ui/             # Buttons, cards, inputs
│   ├── articles/       # Article card, article list
│   ├── digest/         # Digest view
│   └── preferences/    # Preference forms
├── hooks/              # React Query hooks
│   ├── useArticles.ts
│   ├── useUser.ts
│   └── ...
├── lib/                # Utilities
│   ├── api.ts         # Axios instance
│   └── queryClient.ts # React Query setup
├── pages/              # Page components
│   └── Home.tsx
├── types/              # TypeScript types
│   └── api.ts         # From backend API
└── App.tsx
```

---

## 🥟 Bun Commands

```bash
# Development (with hot reload)
bun run dev

# Type check
bun run typecheck

# Lint
bun run lint

# Format code
bun run format

# Build for production
bun run build

# Preview production build
bun run preview
```

---

## 🔌 API Integration

The app uses **TanStack Query** (React Query) for data fetching:

```typescript
import { useArticles, useGenerateDigest } from './hooks/useArticles';

function MyComponent() {
  const { data: articles, isLoading } = useArticles({ limit: 10 });
  const generateDigest = useGenerateDigest();
  
  return (
    <div>
      {articles?.articles.map(article => (
        <ArticleCard key={article.id} article={article} />
      ))}
      
      <button onClick={() => generateDigest.mutate()}>
        Generate Digest
      </button>
    </div>
  );
}
```

---

## 🎨 Styling

Uses **Tailwind CSS** with custom topic colors:

```html
<!-- Topic badges -->
<span class="bg-ai text-white">AI</span>
<span class="bg-tech text-white">Tech</span>
<span class="bg-business text-white">Business</span>
```

---

## 📝 Key Features Implemented

- ✅ **Article Feed** - List recent articles
- ✅ **Personalized Digest** - Generate and display
- ✅ **Feedback Buttons** - Like/dislike/save
- ✅ **User Stats** - Reading metrics
- ✅ **TypeScript** - Full type safety
- ✅ **React Query** - Caching & synchronization

---

## 🚧 Next Steps

Build these features:

1. **Onboarding Wizard**
   ```bash
   mkdir -p src/pages/onboarding
   # Create: Welcome.tsx, Interests.tsx, Preferences.tsx
   ```

2. **Stats Dashboard**
   ```bash
   bun install recharts  # Already installed!
   # Create: src/pages/Stats.tsx
   ```

3. **Preferences Panel**
   ```bash
   # Create: src/pages/Preferences.tsx
   ```

---

## 🔧 Configuration

### API URL
Edit `.env`:
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### Proxy (during development)
Already configured in `vite.config.ts`:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

---

## 🐛 Troubleshooting

### Port already in use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port
bun run dev -- --port 3000
```

### API not connecting
1. Check backend is running: `curl http://localhost:8000/api/v1/health`
2. Verify `VITE_API_URL` in `.env`
3. Check CORS settings in backend

---

## 📦 Tech Stack

| Technology | Purpose |
|------------|---------|
| Bun | Runtime & package manager |
| Vite | Build tool |
| React 18 | UI library |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| TanStack Query | Data fetching |
| Axios | HTTP client |
| Lucide React | Icons |
| Recharts | Charts |

---

## 🎉 Start Hacking!

The template is ready to go. Start building your features!

```bash
# Quick API test
bun run -e "const res = await fetch('http://localhost:8000/api/v1/health'); console.log(await res.json())"
```

Happy coding! 🚀
