# Build stage for frontend
FROM oven-sh/bun:1 AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN bun install

COPY frontend/ ./
RUN bun run build

# Production stage
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start command
WORKDIR /app/backend
CMD ["python", "-c", "
    import uvicorn
    from main import app
    uvicorn.run(app, host='0.0.0.0', port=8000)
"]
