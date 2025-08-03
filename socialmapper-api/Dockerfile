# Multi-stage build for production optimization
# Stage 1: Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install --no-cache-dir .

# Stage 2: Runtime stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal32 \
    libgeos3.11.1 \
    libproj22 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
WORKDIR /app
COPY --from=builder /app .

# Create results directory and set permissions
RUN mkdir -p /app/results && \
    chown -R appuser:appuser /app

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV SOCIALMAPPER_API_HOST=0.0.0.0
ENV SOCIALMAPPER_API_PORT=8000
ENV SOCIALMAPPER_API_WORKERS=4
ENV SOCIALMAPPER_API_LOG_LEVEL=info

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check using curl for better reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with production settings
CMD ["uvicorn", "api_server.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info", \
     "--access-log", \
     "--loop", "uvloop"]