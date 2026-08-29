FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# camada de deps (cacheável): instala base + todos os extras (http, worker, mcp),
# sem dev e sem o próprio projeto
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --all-extras --no-install-project

COPY . .

RUN uv sync --frozen --no-dev --all-extras

ENV PATH="/app/.venv/bin:/app:$PATH"

EXPOSE 8000

CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000"]
