FROM node:20-alpine AS build-frontend
WORKDIR /app/frontend
COPY build/web/package*.json ./
RUN npm install
COPY build/web/ ./
RUN npm run build

FROM python:3.12-slim AS build-backend
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app

COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --frozen --no-dev

COPY backend/src/ ./src/
COPY backend/main.py ./
COPY backend/alembic.ini ./
COPY backend/migrations/ ./migrations/

FROM python:3.12-slim
WORKDIR /app

# Copy the environment from the backend builder
COPY --from=build-backend /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

COPY --from=build-backend /app /app
COPY --from=build-frontend /app/frontend/dist /app/static

ENV WEB_BUILD_DIR=/app/static
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
