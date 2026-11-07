# Depuis la racine : docker build -f demo/Dockerfile .
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-default-groups --group demo --group pipeline

COPY dorsalmatch/ dorsalmatch/
COPY pipeline/ pipeline/
COPY demo/ demo/

# Port attendu par Clever Cloud
ENV PATH="/app/.venv/bin:$PATH" \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=8080
EXPOSE 8080

CMD ["python", "-m", "demo.app"]
