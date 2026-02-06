# Daily Feed - Makefile
# Run these commands from the project root

.PHONY: help backend frontend test clean

help: ## Show this help
	@echo "Daily Feed - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Backend commands
backend-setup: ## Setup backend (install deps, init db)
	cd backend && pip install -r requirements.txt
	cd backend && python scripts/init_db.py
	cd backend && python scripts/seed_demo.py

backend: ## Start backend server
	cd backend && python main.py

backend-test: ## Run backend tests
	cd backend && python -m pytest tests/ -v

backend-db-init: ## Initialize database
	cd backend && python scripts/init_db.py

backend-db-seed: ## Seed database with demo data
	cd backend && python scripts/seed_demo.py

backend-demo: ## Run personalization demo
	cd backend && python scripts/demo_personalization.py

# Frontend commands (using Bun! 🥟)
frontend-setup: ## Setup frontend from template
	@if [ -d "frontend/node_modules" ]; then \
		echo "✓ Frontend already set up"; \
	else \
		echo "→ Installing frontend dependencies..."; \
		cd frontend && bun install; \
	fi

frontend: ## Start frontend dev server
	cd frontend && bun run dev

frontend-build: ## Build frontend for production
	cd frontend && bun run build

frontend-lint: ## Lint frontend code
	cd frontend && bun run lint

frontend-typecheck: ## Type check frontend
	cd frontend && bun run typecheck

# Combined
dev: ## Show how to start both servers
	@echo "🚀 Start both servers:"
	@echo ""
	@echo "Terminal 1 - Backend:"
	@echo "  make backend"
	@echo ""
	@echo "Terminal 2 - Frontend:"
	@echo "  make frontend"
	@echo ""
	@echo "Then open: http://localhost:5173"

# Testing
test: ## Run all tests
	cd backend && python -m pytest tests/ -v

test-frontend: ## Run frontend typecheck
	cd frontend && bun run typecheck 2>/dev/null || echo "No tests yet"

# Cleanup
clean: ## Clean generated files
	rm -rf backend/__pycache__ backend/**/__pycache__ backend/.pytest_cache
	rm -rf frontend/node_modules frontend/dist
	rm -rf backend/data/*.db

# Quick start
quickstart: ## Complete setup from scratch
	@echo "🚀 Setting up Daily Feed..."
	@echo ""
	@echo "1. Setting up backend..."
	$(MAKE) backend-setup
	@echo ""
	@echo "2. Setting up frontend..."
	$(MAKE) frontend-setup
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Start the servers:"
	@echo "  Terminal 1: make backend"
	@echo "  Terminal 2: make frontend"

# Full reset
reset: clean ## Full reset - clean everything
	@echo "⚠️  This will delete the database and node_modules"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf backend/data; \
		rm -rf frontend/node_modules; \
		echo "✅ Reset complete. Run 'make quickstart' to reinitialize."; \
	fi

# Project info
info: ## Show project information
	@echo "Daily Feed Project Structure:"
	@echo ""
	@echo "📁 backend/      - Python FastAPI backend"
	@echo "📁 frontend/     - React + TypeScript + Bun frontend"
	@echo "📁 docs/         - Documentation"
	@echo "   ├── api/      - API docs & TypeScript types"
	@echo "   ├── guides/   - User guides"
	@echo "   └── architecture/ - Technical designs"
	@echo "📁 archive/      - Development notes (old)"
	@echo ""
	@echo "Key files:"
	@echo "  Makefile       - Build commands"
	@echo "  README.md      - Project overview"
