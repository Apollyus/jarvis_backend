# MCP Agent Chat API

Technická dokumentace pro FastAPI backend systém MCP Agenta.

## 🏗️ Přehled architektury

Toto API poskytuje konverzační rozhraní pro MCP (Model Context Protocol) agenta, který může interagovat s externími nástroji (jako je Notion). Systém je postaven na architektuře založené na session, která udržuje historii konverzace napříč více požadavky.

### Klíčové komponenty

1. **FastAPI Server** ([`src/api.py`](../src/api.py)) - HTTP/WebSocket endpointy
2. **Agent Core** ([`src/lib/agent_core.py`](../src/lib/agent_core.py)) - Logika agenta a správa session
3. **MCP Integration** - Orchestrace nástrojů prostřednictvím Model Context Protocol
4. **LangChain** - Abstrakce LLM a paměť konverzace

### Tok požadavku/odpovědi

```
Client Request
    ↓
FastAPI Endpoint (REST/WebSocket/SSE)
    ↓
AgentService.run_query()
    ↓
Session Management (retrieve/create session)
    ↓
MCPAgent.run() - LLM + MCP Tools
    ↓
Update Session History & Memory
    ↓
Response to Client
```

## 🧠 Design agentního systému

### Architektura založená na sessions

**Proč architektura založená na sessions?**
- **Zachování kontextu**: Každý uživatel udržuje vlastní historii konverzace
- **Podpora více uživatelů**: Různí uživatelé mohou vést nezávislé konverzace
- **Stavové interakce**: Agent si pamatuje předchozí výměny v rámci session

Systém používá slovník sessions (`sessions: Dict[str, Dict[str, Any]]`), který ukládá:
- `memory`: instanci [`ConversationBufferMemory`](../src/lib/agent_core.py:67) pro integraci s LangChain
- `history`: Seznam objektů zpráv pro API odpovědi

**Poznámka pro produkci**: Úložiště session v paměti by mělo být v produkčním prostředí nahrazeno Redis nebo databází pro podporu horizontálního škálování a persistence.

### Paměť konverzace

**Proč ConversationBufferMemory?**

Systém používá [`ConversationBufferMemory`](../src/lib/agent_core.py:67) z LangChain s `return_messages=True`:

- **Jednoduché a efektivní**: Ukládá kompletní historii konverzace bez sumarizace
- **Plný kontext**: LLM má přístup k celé konverzaci pro lepší porozumění
- **Snadná integrace**: Bezproblémově funguje s agentním systémem LangChain
- **Flexibilní**: Snadné rozšíření o jiné typy paměti (summary, window, atd.)

**Kompromisy**:
- ✅ Perfektní zapamatování kontextu konverzace
- ✅ Žádná ztráta informací ze sumarizace
- ❌ Spotřeba tokenů roste s délkou konverzace
- ❌ Může dosáhnout limitů kontextu u velmi dlouhých konverzací

Pro produkci zvažte [`ConversationBufferWindowMemory`](https://python.langchain.com/docs/modules/memory/types/buffer_window) pro efektivnější využití tokenů nebo [`ConversationSummaryMemory`](https://python.langchain.com/docs/modules/memory/types/summary) pro velmi dlouhé konverzace.

### Životní cyklus agenta

**Proč vytvářet nového agenta pro každý požadavek?**

V [`AgentService.run_query()`](../src/lib/agent_core.py:81) je pro každý dotaz vytvořena nová instance [`MCPAgent`](../src/lib/agent_core.py:81):

```python
agent = MCPAgent(llm=self.llm, client=self.client, max_steps=30)
result = await agent.run(message)
```

**Zdůvodnění**:
- **Bezstavový agent**: Každé spuštění agenta je nezávislé, zabraňuje úniku stavu
- **Bezpečnost vláken**: Žádný sdílený měnitelný stav mezi souběžnými požadavky
- **Čisté provedení**: Čerstvý stav agenta zajišťuje předvídatelné chování
- **Paměť v session**: Kontext konverzace je zachován v objektu session, ne v agentovi

Paměť session je poté aktualizována po každém úspěšném spuštění pro zachování kontinuity.

## 🔧 Technologický stack

### Hlavní knihovny

| Knihovna | Verze | Účel | Proč tato volba? |
|---------|---------|---------|------------------|
| **FastAPI** | Latest | Web framework | Moderní asynchronní podpora, automatické OpenAPI dokumenty, typová bezpečnost |
| **LangChain** | 0.3.27 | LLM orchestrace | Průmyslový standard pro agentní workflow, rozsáhlé integrace |
| **LangChain-OpenAI** | 0.3.34 | OpenAI LLM wrapper | Jednotné rozhraní pro OpenAI-kompatibilní API |
| **MCP** | 1.16.0 | Model Context Protocol | Standardizovaný protokol pro integraci nástrojů |
| **mcp-use** | 1.3.11 | MCP agent implementace | Vysokoúrovňová abstrakce agenta nad MCP |
| **Uvicorn** | 0.37.0 | ASGI server | Produkčně připravený asynchronní server pro FastAPI |
| **python-dotenv** | 1.1.1 | Konfigurace prostředí | Bezpečná správa API klíčů |

### LLM poskytovatel: OpenRouter

Systém používá [**OpenRouter**](https://openrouter.ai) jako poskytovatele LLM:

```python
llm = ChatOpenAI(
    model="google/gemini-2.5-flash-lite-preview-09-2025",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=OPENROUTER_API_KEY,
    temperature=0,
)
```

**Proč OpenRouter?**
- **Jednotné API**: Přístup k více poskytovatelům LLM (OpenAI, Anthropic, Google, atd.) přes jedno rozhraní
- **Flexibilita modelů**: Snadné přepínání mezi modely bez změn kódu
- **Optimalizace nákladů**: Výběr nákladově efektivních modelů podle požadavků úlohy
- **Možnosti fallbacku**: Lze implementovat automatický fallback na alternativní modely
- **Kompatibilní s OpenAI**: Funguje s wrapperem `ChatOpenAI` z LangChain

**Aktuální model**: `google/gemini-2.5-flash-lite-preview-09-2025`
- Rychlé doby odezvy
- Nákladově efektivní pro konverzační úlohy
- Dobrá rovnováha mezi schopnostmi a rychlostí

### MCP (Model Context Protocol)

**Co je MCP?**
MCP je protokol, který umožňuje LLM interagovat s externími nástroji a datovými zdroji standardizovaným způsobem.

**Aktuální konfigurace**:
```python
config = {
    "mcpServers": {
        "Notion": {
            "url": "https://mcp.notion.com/mcp"
        }
    }
}
```

**Proč MCP?**
- **Standardizované volání nástrojů**: Konzistentní rozhraní pro různé nástroje
- **Automatické zjišťování**: Nástroje vystavují své schopnosti pomocí protokolu
- **Typová bezpečnost**: Strukturovaná validace vstupu/výstupu
- **Rozšiřitelné**: Snadné přidávání nových integrací nástrojů

## 📡 API Endpointy

### 1. REST API - `/api/chat` (POST)

**Nejlepší pro**: Jednoduché interakce požadavek/odpověď, není potřeba streaming

**Požadavek**:
```json
{
  "message": "Create a new Notion page called 'Meeting Notes'",
  "session_id": "user-123"
}
```

**Odpověď**:
```json
{
  "response": "I've created a new page titled 'Meeting Notes' in your Notion workspace.",
  "session_id": "user-123"
}
```

**Implementace**: [`src/api.py:29-32`](../src/api.py:29-32)

**Příklad**:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What tasks do I have?", "session_id": "user-123"}'
```

### 2. WebSocket - `/ws/chat`

**Nejlepší pro**: Real-time obousměrná komunikace, interaktivní chatové aplikace

**Připojení klienta**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "List my Notion pages",
    session_id: "user-123"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**Typy zpráv**:
- `status`: Notifikace o zpracování
- `response`: Odpověď agenta (s `done: true`)
- `error`: Chybová zpráva

**Implementace**: [`src/api.py:35-73`](../src/api.py:35-73)

**Proč WebSocket?**
- Perzistentní připojení snižuje latenci
- Umožňuje indikátory psaní a aktualizace průběhu
- Skutečně obousměrná komunikace
- Lepší pro chatová rozhraní

### 3. Server-Sent Events - `/api/chat/stream` (GET)

**Nejlepší pro**: Jednosměrný streaming ze serveru na klienta

**Požadavek**:
```bash
curl -N http://localhost:8000/api/chat/stream?message=Hello
```

**Stream odpovědi**:
```
data: {"type": "status", "message": "Processing..."}

data: {"type": "response", "message": "Hi! How can I help?", "done": true}
```

**Implementace**: [`src/api.py:76-102`](../src/api.py:76-102)

**JavaScript příklad**:
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/chat/stream?message=Hello'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**Proč SSE?**
- Jednodušší než WebSocket pro jednosměrný streaming
- Funguje přes standardní HTTP
- Automatická podpora opětovného připojení
- Lepší kompatibilita s firewallem

### 4. Pomocné endpointy

**Health Check** - `GET /health`
```json
{"status": "healthy"}
```

**Root** - `GET /`
```json
{"message": "MCP Agent API is running"}
```

## 🚀 Spuštění API

### Předpoklady

1. **Python 3.8+**
2. **Proměnné prostředí**:
   ```bash
   # .env soubor
   OPENROUTER_API_KEY=your_api_key_here
   ```

### Instalace

```bash
# Instalace závislostí
pip install -r requirements.txt
```

### Spuštění serveru

**Základní spuštění**:
```bash
python main.py
```

**S možnostmi**:
```bash
# Vlastní port
python main.py --port 8080

# Zapnutí auto-reload pro vývoj
python main.py --reload

# Debug logování
python main.py --log-level debug

# Vlastní host (produkce)
python main.py --host 0.0.0.0 --port 8000
```

**Proměnné prostředí**:
```bash
export API_HOST=0.0.0.0
export API_PORT=8080
export RELOAD=true
export LOG_LEVEL=debug
python main.py
```

### Produkční nasazení

**Použití Gunicorn**:
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api:app --bind 0.0.0.0:8000
```

**Docker**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 🧪 Testování

### Manuální testování

**REST API**:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-1"}'
```

**WebSocket** (použití `websocat`):
```bash
websocat ws://localhost:8000/ws/chat
# Poté odeslat: {"message": "Hello", "session_id": "test-1"}
```

### Automatizované testování

Spuštění testovacího skriptu konverzace:
```bash
python test/api_conversation_test.py
```

Tento skript ([`test/api_conversation_test.py`](../test/api_conversation_test.py)) demonstruje:
- Vícetahové konverzace
- Správu session
- Zachování kontextu napříč požadavky

### API dokumentace

FastAPI automaticky generuje interaktivní API dokumentaci:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Bezpečnostní aspekty

### Aktuální implementace
- CORS povolen pro localhost:3000 a localhost:3001
- Není implementována autentizace

### Doporučení pro produkci

1. **Autentizace pomocí API klíče**:
```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials
```

2. **Rate Limiting**:
```bash
pip install slowapi
```

3. **Pouze HTTPS** v produkci
4. **CORS podle prostředí**:
```python
allow_origins = os.getenv("CORS_ORIGINS", "").split(",")
```

## 🎯 Souhrn návrhových rozhodnutí

| Rozhodnutí | Zdůvodnění |
|----------|-----------|
| **Architektura založená na sessions** | Udržuje kontext konverzace pro každého uživatele |
| **ConversationBufferMemory** | Jednoduchá, kompletní historie pro lepší kontext |
| **Nový agent pro každý požadavek** | Bezpečné pro vlákna, bezstavové provádění |
| **OpenRouter** | Flexibilní poskytovatel LLM s více možnostmi modelů |
| **Více typů endpointů** | Podpora různých klientských architektur (REST/WS/SSE) |
| **Sessions v paměti** | Jednoduché pro vývoj; nahradit Redis pro produkci |
| **FastAPI** | Moderní asynchronní framework s vynikající vývojářskou zkušeností |
| **MCP protokol** | Standardizovaná integrace nástrojů |

## 📚 Struktura kódu

```
.
├── main.py                      # Vstupní bod s CLI možnostmi
├── src/
│   ├── api.py                   # FastAPI endpointy
│   └── lib/
│       └── agent_core.py        # Logika agenta a správa session
├── test/
│   └── api_conversation_test.py # Skript pro testování konverzace
├── docs/
│   └── README_API.md           # Tento soubor
└── requirements.txt            # Python závislosti
```

## 🔄 Rozšiřování systému

### Přidání nových MCP nástrojů

Upravit [`agent_core.py`](../src/lib/agent_core.py:39-45):
```python
config = {
    "mcpServers": {
        "Notion": {"url": "https://mcp.notion.com/mcp"},
        "GitHub": {"url": "https://github-mcp.example.com/mcp"}
    }
}
```

### Změna LLM modelu

Upravit [`agent_core.py`](../src/lib/agent_core.py:31-36):
```python
self.llm = ChatOpenAI(
    model="anthropic/claude-3.5-sonnet",  # Změnit model
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=OPENROUTER_API_KEY,
    temperature=0.7,  # Upravit kreativitu
)
```

### Implementace perzistentních sessions

Nahradit úložiště v paměti Redis:
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_session(session_id: str):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

def save_session(session_id: str, session_data: dict):
    redis_client.set(f"session:{session_id}", json.dumps(session_data))
```

## 📊 Aspekty výkonu

- **Max Steps**: Agent má `max_steps=30` pro prevenci nekonečných smyček
- **Temperature**: Nastavena na `0` pro deterministické odpovědi
- **Souběžné požadavky**: FastAPI efektivně zpracovává souběžné požadavky
- **Růst paměti**: Sledovat úložiště sessions, implementovat čištění starých sessions

## 🐛 Řešení problémů

**Agent neodpovídá**:
- Zkontrolujte `OPENROUTER_API_KEY` v `.env`
- Ověřte, že URL MCP serverů jsou přístupné
- Zkontrolujte logy pro podrobné chybové zprávy

**Session se neuchovává**:
- Sessions jsou v paměti; restart je vymaže
- Implementujte Redis pro perzistenci

**CORS chyby**:
- Přidejte URL vašeho frontendu do `allow_origins` v [`api.py`](../src/api.py:18)

## 📝 Další zdroje

- [FastAPI dokumentace](https://fastapi.tiangolo.com/)
- [LangChain dokumentace](https://python.langchain.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [OpenRouter dokumentace](https://openrouter.ai/docs)
