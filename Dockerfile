# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Build arguments for optional features
ARG ENABLE_WHATSAPP=false
ARG ENABLE_N8N=true

# Set working directory
WORKDIR /app

# Set environment variables (including build args as env vars for runtime)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENABLE_WHATSAPP=${ENABLE_WHATSAPP} \
    ENABLE_N8N=${ENABLE_N8N}

# Install base system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    wget \
    tar \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (needed for n8n-mcp and other npm packages)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Conditionally install Go (only if WhatsApp is enabled)
RUN if [ "$ENABLE_WHATSAPP" = "true" ]; then \
        wget https://go.dev/dl/go1.23.2.linux-amd64.tar.gz && \
        tar -C /usr/local -xzf go1.23.2.linux-amd64.tar.gz && \
        rm go1.23.2.linux-amd64.tar.gz; \
    fi

# Add Go to PATH
ENV PATH="/usr/local/go/bin:${PATH}"

# Add npm global bin to PATH (both common locations)
ENV PATH="/usr/local/bin:/usr/lib/node_modules/.bin:${PATH}"

# Conditionally install n8n-mcp (only if n8n is enabled)
RUN if [ "$ENABLE_N8N" = "true" ]; then \
        npm install -g n8n-mcp && \
        npm list -g n8n-mcp && \
        echo "=== N8N-MCP Installation Verification ===" && \
        which n8n-mcp && \
        n8n-mcp --version || echo "n8n-mcp --version failed" && \
        ls -la $(npm root -g)/n8n-mcp/ || true; \
    fi

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Conditionally update Go dependencies for WhatsApp bridge
RUN if [ "$ENABLE_WHATSAPP" = "true" ] && [ -d "/app/src/whatsapp-mcp/whatsapp-bridge" ] && [ -f "/app/src/whatsapp-mcp/whatsapp-bridge/go.mod" ]; then \
        cd /app/src/whatsapp-mcp/whatsapp-bridge && \
        go mod download && \
        go mod tidy; \
    fi

# Create a non-root user to run the application
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/src/lib/tokens && \
    mkdir -p /app/whatsapp-store && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/src/lib/tokens && \
    chmod -R 755 /app/whatsapp-store

USER appuser

# Expose the application port
EXPOSE 8000 5000

# Health check
HEALTHCHECK --interval=300s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["/app/entrypoint.sh"]