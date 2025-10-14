# Jarvis Backend - MCP Agent API

Inteligentní backend s podporou Model Context Protocol (MCP) pro Notion a TickTick.

## 🚀 Quick Start

```bash
# Instalace
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# První spuštění
python main.py

# API dostupné na http://localhost:8000
```

## 📚 Dokumentace

### Základní

- [API Dokumentace](docs/README_API.md) - REST a WebSocket endpointy
- [Autentizace](docs/README_AUTENTIZACE.md) - API klíče a zabezpečení
- [Testy](docs/README_TESTY.md) - Jak spustit testy
- [Docker](docs/README_DOCKER.md) - Containerizace

### OAuth a Deployment

- **[🔥 VPS Deployment (headless)](docs/QUICKSTART_VPS.md)** - Jak nasadit na VPS **BEZ GUI**
- [OAuth na VPS - Podrobný návod](docs/README_VPS_DEPLOYMENT.md) - Kompletní deployment guide
- [OAuth Headless řešení](docs/README_OAUTH_HEADLESS.md) - Jak funguje OAuth s MCP
- [OAuth Integrace](docs/oauth.md) - TickTick OAuth flow

### Nástroje

- **`oauth_cache_manager.py`** - Export/import OAuth tokenů pro VPS

## ❓ FAQ - OAuth na VPS

**Q: Proč callback URL `localhost:8080` funguje lokálně, ale nefunguje na VPS?**

A: `mcp-use` knihovna automaticky spouští dočasný lokální HTTP server na portu 8080 pro zachycení OAuth callbacku. Po získání tokenu se server vypne. Na VPS bez GUI nemůžeš otevřít prohlížeč pro autorizaci.

**Q: Jak to vyřešit?**

A: **Autorizuj na lokálním PC, exportuj tokeny, importuj na VPS.**

```bash
# 1. Na PC
python oauth_cache_manager.py export --output tokens.zip

# 2. Zkopíruj na VPS
scp tokens.zip user@vps:/tmp/

# 3. Na VPS
python oauth_cache_manager.py import --input /tmp/tokens.zip
```

**Q: Kde se tokeny ukládají?**

A: 
- Windows: `%LOCALAPPDATA%\mcp-use\`
- Linux: `~/.cache/mcp-use/` nebo `$MCP_USE_CACHE_DIR`

**Q: Jak dlouho tokeny platí?**

A: Refresh tokeny obvykle 90 dní. `mcp-use` automaticky obnovuje access tokeny. Po expiraci refresh tokenu musíš zopakovat autorizaci.

**Q: Můžu to zautomatizovat?**

A: Ano, můžeš implementovat vlastní OAuth flow bez `mcp-use`, ale je to složitější. Pro většinu případů stačí periodické obnovení tokenů (každých 60-80 dní).

Viz [QUICKSTART_VPS.md](docs/QUICKSTART_VPS.md) pro podrobný postup.

## 🛠️ Technologie

- **FastAPI** - Web framework
- **LangChain** - LLM framework
- **MCP (Model Context Protocol)** - Komunikace s Notion, TickTick
- **OpenRouter** - LLM provider (Gemini 2.5 Flash Lite)

## 📋 Funkce

- ✅ REST API a WebSocket pro chat
- ✅ Session management s historií konverzací
- ✅ Notion integrace (vytváření stránek, databází, atd.)
- ✅ TickTick integrace (úkoly, projekty)
- ✅ OAuth 2.0 autentizace
- ✅ API klíče pro zabezpečení
- ✅ Docker support
- ✅ **Headless deployment na VPS**

## 🔧 Konfigurace

Vytvoř `.env` soubor:

```env
# OpenRouter API
OPENROUTER_API_KEY=your_key

# API Security (optional)
API_KEY=your_secure_key

# TickTick OAuth (optional)
TICKTICK_CLIENT_ID=your_client_id
TICKTICK_CLIENT_SECRET=your_client_secret
TICKTICK_CALLBACK_URL=http://localhost:8000/api/ticktick/callback

# MCP Cache (optional, pro custom lokaci)
MCP_USE_CACHE_DIR=/path/to/cache
```

## 📦 Struktura projektu

```
jarvis_backend/
├── main.py                      # Entrypoint
├── src/
│   ├── api.py                   # FastAPI routes
│   ├── auth.py                  # Autentizace
│   └── lib/
│       ├── agent_core.py        # MCP Agent service
│       └── tokens/              # Uložené tokeny
│           └── ticktick_tokens.json
├── test/                        # Unit testy
├── docs/                        # Dokumentace
│   ├── QUICKSTART_VPS.md        # 🔥 START HERE pro VPS
│   ├── README_VPS_DEPLOYMENT.md # Detailní VPS guide
│   └── ...
├── oauth_cache_manager.py       # 🛠️ Utility pro správu tokenů
├── Dockerfile
└── docker-compose.yml
```

## 🧪 Testování

```bash
# Všechny testy
pytest

# Konkrétní test
pytest test/api_conversation_test.py -v

# S coverage
pytest --cov=src
```

## 🐳 Docker

```bash
# Build
docker-compose build

# Spustit
docker-compose up -d

# Logy
docker-compose logs -f
```

**Pro VPS deployment s OAuth viz [QUICKSTART_VPS.md](docs/QUICKSTART_VPS.md)**

## 📝 Příklady použití

### REST API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "vytvoř mi úkol v TickTick: nakoupit mleko",
    "session_id": "user123"
  }'
```

### WebSocket

```python
import asyncio
import websockets
import json

async def chat():
    uri = "ws://localhost:8000/ws/chat?api_key=your_key"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "message": "vytvoř stránku v Notionu",
            "session_id": "user123"
        }))
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(chat())
```

## 🤝 Contributing

Pull requesty vítány! Pro větší změny nejdřív otevři issue.

## 📄 Licence

MIT

## 🆘 Support

Problémy s OAuth na VPS? → [QUICKSTART_VPS.md](docs/QUICKSTART_VPS.md)

Další otázky? → Otevři issue

---

Made with ❤️ and a bit of sarcasm 😏
