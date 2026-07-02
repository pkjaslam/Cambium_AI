FROM python:3.11-slim

# curl is used by the HEALTHCHECK below; keep the image minimal otherwise.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create an unprivileged user to run the app; never run as root.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app
COPY web/server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# The app dir (and everything copied into it) is owned by the non-root user.
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Liveness probe hits the unauthenticated /health endpoint.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "web.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
