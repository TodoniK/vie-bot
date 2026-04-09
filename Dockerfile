FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN uv pip install --system --no-cache .

# IDs connus (fallback: re-importés dans SQLite à chaque démarrage)
RUN mkdir -p /app/data
COPY ids.txt /app/data/ids.txt

ENV DATA_DIR=/app/data

CMD ["python", "-m", "vie_bot"]
