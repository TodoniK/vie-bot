FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vie.py entrypoint.sh ./
RUN chmod +x entrypoint.sh

RUN mkdir -p /app/data

ENV DATA_DIR=/app/data
ENV CHECK_INTERVAL=60

VOLUME ["/app/data"]

ENTRYPOINT ["./entrypoint.sh"]
