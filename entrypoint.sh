#!/bin/bash

set -e

echo "🚀 Spouštění Jarvis Backend..."

# Check if WhatsApp bridge exists and start it
if [ -d "/app/src/whatsapp-mcp/whatsapp-bridge" ] && [ -f "/app/src/whatsapp-mcp/whatsapp-bridge/main.go" ]; then
    echo "📱 Spouštění WhatsApp bridge..."
    cd /app/src/whatsapp-mcp/whatsapp-bridge
    go run main.go &
    WHATSAPP_PID=$!
    
    # Čekej, až se WhatsApp bridge spustí
    sleep 5
    
    # Cleanup
    trap "kill $WHATSAPP_PID" EXIT
else
    echo "⚠️  WhatsApp bridge nenalezen - pokračuji bez něj..."
fi

# Spusť Jarvis Backend
echo "🤖 Spouštění Jarvis Backend..."
cd /app
python main.py --host 0.0.0.0 --port 8000

📁 Struktura projektu

jarvis_backend/
├── Dockerfile
├── entrypoint.sh          ← Vytvoř tenhle soubor!
├── docker-compose.yml
├── requirements.txt
├── main.py
├── src/
│   └── lib/
│       └── agent_core.py
├── whatsapp-mcp/          ← Tvůj klonovaný repo
│   ├── whatsapp-bridge/
│   │   ├── main.go
│   │   └── ...
│   └── ...
├── ticktick-mcp/          ← Ostatní MCP servery
│   └── ...
└── ...

🐳 docker-compose.yml

version: '3.8'

services:
  jarvis-backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: jarvis-backend
    ports:
      - "8000:8000"      # Jarvis API
      - "5000:5000"      # WhatsApp bridge
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - NOTION_API_KEY=${NOTION_API_KEY}
      - API_KEY=${API_KEY}
      - USERNAME=${USERNAME}
      - PASSWORD=${PASSWORD}
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - LOG_LEVEL=info
    
    volumes:
      - ./tokens:/app/src/lib/tokens
      - ./whatsapp-store:/app/whatsapp-store
    
    restart: unless-stopped
    networks:
      - jarvis-network
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

networks:
  jarvis-network:
    driver: bridge

🚀 Jak to spustit

# 1. Ujisti se, že máš entrypoint.sh v root projektu
ls -la entrypoint.sh

# 2. Dej mu execute permission
chmod +x entrypoint.sh

# 3. Build a spuštění
docker-compose up -d

# 4. Logy
docker-compose logs -f jarvis-backend

# 5. Při prvním spuštění se zobrazí QR kód
# Naskenuj ho WhatsApp na telefonu
