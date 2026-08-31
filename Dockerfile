# Backend API — now API-only. Admin SPA lives in its own `admin` service
# (admin/Dockerfile + nginx) and proxies /api+ /media to the Railway private
# network. This Dockerfile no longer bundles the Vite admin.
FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ .
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD sh -c "uv run alembic upgrade head && uvicorn app.app:create_app --factory --host 0.0.0.0 --port \"${PORT:-8000}\""
