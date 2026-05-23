# ==============================================================================
# STAGE 1: Dependency Builder
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system dependencies needed for compiling python libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file to compile wheels
COPY requirements.txt .

# Build wheels in a cache-mounted local directory
RUN pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# STAGE 2: Lightweight Runtime Runner
# ==============================================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Expose standard gateway port
EXPOSE 8000

# Set environment paths to access pre-compiled packages
COPY --from=builder /usr/local /usr/local
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create an unprivileged user to secure container boundaries
RUN groupadd -g 1000 appgroup && \
    useradd -r -u 1000 -g appgroup -d /app -s /sbin/nologin appuser

# Mount persistent log folder and configure rights
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

# Copy application source code
COPY --chown=appuser:appgroup . .

# Switch container process user
USER appuser

# Launch the FastAPI application using standard, production-grade Uvicorn parameters
CMD ["uvicorn", "main.py", "--host", "0.0.0.0", "--port", "8000"]
