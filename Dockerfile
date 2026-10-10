FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f

COPY --from=ghcr.io/astral-sh/uv:0.13.0@sha256:cdc6093146eb3ff6a40107b38f008b789e050e77ad87865e381d9917da55a168 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/* \
    && uv pip install --system --no-cache . \
    && useradd --system --uid 10001 --home /app vie \
    && mkdir -p /app/data && chown vie:vie /app/data

ENV DATA_DIR=/app/data TZ=Europe/Paris
USER vie

# Sain si un cycle a réussi récemment (voir vie_bot.__main__.healthcheck)
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
    CMD ["python", "-m", "vie_bot", "healthcheck"]

CMD ["python", "-m", "vie_bot"]
