FROM python:3.11-alpine AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install --no-cache-dir poetry==2.2.1
COPY pyproject.toml /app/
RUN poetry config virtualenvs.create false && poetry install --only main --no-interaction --no-ansi

COPY device /app/device

EXPOSE 8003
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://localhost:8003/health || exit 1

CMD ["python", "-m", "device.services.comms_bridge.main"]
