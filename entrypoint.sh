#!/bin/bash

set -e

echo "🚀 Spouštění Jarvis Backend..."

# Check if WhatsApp is enabled and bridge exists
if [ "$ENABLE_WHATSAPP" = "true" ] && [ -d "/app/src/whatsapp-mcp/whatsapp-bridge" ] && [ -f "/app/src/whatsapp-mcp/whatsapp-bridge/main.go" ]; then
    echo "📱 Spouštění WhatsApp bridge..."
    cd /app/src/whatsapp-mcp/whatsapp-bridge
    go run main.go &
    WHATSAPP_PID=$!
    
    # Čekej, až se WhatsApp bridge spustí
    sleep 5
    
    # Cleanup při ukončení
    trap "echo '🛑 Zastavuji WhatsApp bridge...'; kill $WHATSAPP_PID 2>/dev/null || true" EXIT
else
    if [ "$ENABLE_WHATSAPP" != "true" ]; then
        echo "⚠️  WhatsApp je zakázán (ENABLE_WHATSAPP=$ENABLE_WHATSAPP)"
    else
        echo "⚠️  WhatsApp bridge nenalezen - pokračuji bez něj..."
    fi
fi

# Info o n8n-mcp
if [ "$ENABLE_N8N" = "true" ]; then
    echo "✅ n8n-mcp je povolen"
else
    echo "⚠️  n8n-mcp je zakázán (ENABLE_N8N=$ENABLE_N8N)"
fi

# Spusť Jarvis Backend
echo "🤖 Spouštění Jarvis Backend API..."
cd /app
exec python main.py --host 0.0.0.0 --port 8000