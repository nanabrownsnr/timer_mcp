FROM python:3.12-slim

LABEL org.opencontainers.image.title="Timer MCP"
LABEL org.opencontainers.image.description="Timer MCP - Unauthenticated Twynity MCP for scheduling waits and delayed callbacks"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY requirements.txt ./
COPY src/ ./src/

# Install Python dependencies and the package itself
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Create non-root user
RUN groupadd -r timer && useradd -r -g timer -d /app -s /sbin/nologin timer
RUN chown -R timer:timer /app
USER timer

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Run the server
ENTRYPOINT ["timer-mcp"]
