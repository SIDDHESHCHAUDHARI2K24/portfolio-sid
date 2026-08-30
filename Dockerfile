# Build context = repo root (Railway root directory covers backend + admin).
# Build: docker build -f backend/Dockerfile -t portfolio-backend .

FROM node:20-alpine AS admin-build
WORKDIR /admin
COPY admin/package.json admin/package-lock.json ./
RUN npm ci
COPY admin/ .
RUN npm run build

FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ .
COPY --from=admin-build /admin/dist ./static
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD sh -c "uv run alembic upgrade head && uvicorn app.app:create_app --factory --host 0.0.0.0 --port \"${PORT:-8000}\""
