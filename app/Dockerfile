# ─────────────────────────────────────────────────────────────────────────────
# Elastic Observability Demo — Application Container
# ─────────────────────────────────────────────────────────────────────────────
# Build:   docker build -t elastic-observability-demo ./app
# Run:     docker run -p 8000:8000 elastic-observability-demo
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Metadata
LABEL maintainer="elastic-observability-lab"
LABEL description="FastAPI demo app instrumented with OpenTelemetry"

# Security: run as non-root user
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY main.py .
COPY static ./static

# Own the workdir
RUN chown -R appuser:appgroup /app

USER appuser

# Application port
EXPOSE 8000

# Health check (Docker will mark container unhealthy if this fails)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
