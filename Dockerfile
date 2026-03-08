FROM python:3.12-slim

WORKDIR /app

# Copy project and install (excludes .venv, .git, etc. via .dockerignore)
COPY . .
RUN pip install --no-cache-dir -e .

# OTLP endpoint set at runtime via docker-compose
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318

CMD ["python", "-m", "src.main"]
