# OS-APOW Application Dockerfile
# Multi-stage build for optimized production image

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.12-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies to a virtual environment
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --no-cache -r pyproject.toml

# ============================================================================
# Stage 2: Production
# ============================================================================
FROM python:3.12-slim AS production

# Create non-root user for security
RUN groupadd --gid 1000 osapow && \
    useradd --uid 1000 --gid osapow --shell /bin/bash --create-home osapow

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY --chown=osapow:osapow src/ ./src/
COPY --chown=osapow:osapow pyproject.toml ./

# Switch to non-root user
USER osapow

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden)
CMD ["uvicorn", "src.notifier_service:app", "--host", "0.0.0.0", "--port", "8000"]
