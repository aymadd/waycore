FROM python:3.11-alpine AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install --no-cache-dir poetry==2.2.1
COPY pyproject.toml /app/
RUN poetry config virtualenvs.create false && poetry install --only main --no-interaction --no-ansi --no-root

COPY device /app/device

# Create sample photo directory and convert sample image (stored separately from data volume)
RUN mkdir -p /app/sample
COPY assets/other/rendering.png /tmp/rendering.png
RUN python -c "from PIL import Image; img = Image.open('/tmp/rendering.png'); img.convert('RGB').save('/app/sample/IMG_20240101_120000_waycore.jpg', 'JPEG', quality=95)" && rm /tmp/rendering.png

# Copy entrypoint script
COPY device/services/camera_service/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8006
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://localhost:8006/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
