FROM python:3.12-slim

# Security & performance environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install dumb-init for proper signal handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends dumb-init && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install python dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root system user and group
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy application code
COPY blindspot/ ./blindspot/

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8080

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Run Gunicorn binding to $PORT as required by Google Cloud Run
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --timeout 120 "blindspot.app:create_app()"
