# ==============================================================================
# Production-grade Container Image for UAMS Gateway Service
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Expose standard gateway port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy requirements file and install dependencies directly
COPY gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Create an unprivileged user to secure container boundaries
RUN groupadd -g 1000 appgroup && \
    useradd -r -u 1000 -g appgroup -d /app -s /sbin/nologin appuser

# Mount persistent log folder and configure rights
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

# Copy application source code into a package subdirectory 'gateway'
# to support standard package-level relative/absolute imports (e.g. from gateway.xxx)
COPY --chown=appuser:appgroup gateway/ ./gateway/

# Switch container process user
USER appuser

# Launch the FastAPI application using standard, production-grade Uvicorn parameters
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
