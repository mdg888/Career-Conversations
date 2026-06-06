# ── Stage 1: Build React frontend ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ── Stage 2: Python backend + built frontend ───────────────────────────────────
FROM python:3.11-slim

# Tesseract for OCR on image uploads
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built React app from stage 1
# FastAPI serves these as static files at /
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Persist uploaded files and SQLite DB via a volume (see docker-compose.yml)
VOLUME ["/app/backend/data"]

EXPOSE 8000

CMD ["uvicorn", "backend.src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
