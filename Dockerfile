# syntax=docker/dockerfile:1

# --- builder: resolve o venv a partir do lock ------------------------------
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Só o lock e o manifesto: a camada de dependências só invalida quando eles mudam.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --extra anthropic --extra openai --extra groq

# --- runtime: imagem final, não-root --------------------------------------
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS runtime

ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY . .

RUN useradd --uid 1000 --user-group --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
