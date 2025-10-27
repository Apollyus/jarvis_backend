# Session Management - Redis Integration

## Přehled

JARVIS backend nyní používá **Redis** pro ukládání konverzací (sessions). To znamená:

✅ Sessions **přežijí restart** serveru
✅ **Automatické mazání** starých sessions (TTL 7 dní)
✅ **Rychlé načítání** z paměti Redis
✅ **Fallback na RAM** pokud Redis není dostupný

---

## Jak to funguje

### 1. Vytvoření nové konverzace

**Frontend NEMUSÍ posílat session_id:**

```javascript
// POST /api/chat
{
  "message": "Ahoj JARVIS!"
  // session_id není nutné
}

// Response
{
  "response": "Ahoj! Jak ti můžu pomoci?",
  "session_id": "sess_a3f2b1c9"  // Backend vytvoří a vrátí
}
```

**Frontend si uloží session_id a používá ho:**

```javascript
// Další zprávy ve stejné konverzaci
{
  "message": "Jaké je počasí?",
  "session_id": "sess_a3f2b1c9"  // Použij stejné ID
}
```

### 2. Nová konverzace ("New Chat")

**Možnost A: Přestaň posílat session_id**
```javascript
{
  "message": "Začínám novou konverzaci"
  // session_id vynech - backend vytvoří nové
}
```

**Možnost B: Použij dedicated endpoint**
```javascript
// POST /api/sessions/new
// Response:
{
  "session_id": "sess_xyz123",
  "message": "Nová session vytvořena"
}
```

---

## API Endpointy

### Chat endpoint (hlavní)

```http
POST /api/chat
Content-Type: application/json
X-API-Key: your-api-key

{
  "message": "Tvoje zpráva",
  "session_id": "sess_abc123"  // VOLITELNÉ
}
```

**Response:**
```json
{
  "response": "Odpověď agenta",
  "session_id": "sess_abc123"
}
```

### Správa sessions

#### Vytvořit novou session
```http
POST /api/sessions/new
X-API-Key: your-api-key
```
**Response:**
```json
{
  "session_id": "sess_xyz789",
  "message": "Nová session vytvořena"
}
```

#### Smazat session
```http
DELETE /api/sessions/{session_id}
X-API-Key: your-api-key
```
**Response:**
```json
{
  "message": "Session sess_xyz789 byla smazána"
}
```

#### Seznam aktivních sessions
```http
GET /api/sessions
X-API-Key: your-api-key
```
**Response:**
```json
{
  "sessions": ["sess_abc123", "sess_xyz789"],
  "count": 2
}
```

#### Info o konkrétní session
```http
GET /api/sessions/{session_id}
X-API-Key: your-api-key
```
**Response:**
```json
{
  "session_id": "sess_abc123",
  "message_count": 10,
  "updated_at": "2025-10-27T14:30:00",
  "expires_in_seconds": 604800
}
```

#### Historie konverzace
```http
GET /api/sessions/{session_id}/history
X-API-Key: your-api-key
```
**Response:**
```json
{
  "session_id": "sess_abc123",
  "history": [
    {"role": "user", "content": "Ahoj"},
    {"role": "assistant", "content": "Ahoj! Jak ti můžu pomoci?"}
  ],
  "message_count": 2
}
```

---

## Redis konfigurace

### Docker Compose
Redis je automaticky spuštěn v Docker Compose:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
```

### Environment proměnné

```bash
# .env
REDIS_URL=redis://redis:6379  # Pro Docker
# nebo
REDIS_URL=redis://localhost:6379  # Pro lokální development
```

### TTL (Time To Live)

Sessions jsou **automaticky mazány** po **7 dnech** neaktivity.

Můžeš to změnit v `session_manager.py`:
```python
SessionManager(ttl_days=14)  # 14 dní místo 7
```

## Fallback mechanismus

Pokud **Redis není dostupný**, backend automaticky:

1. ⚠️ Loguje varování: `"Sessions budou pouze v paměti"`
2. 💾 Ukládá sessions do RAM (stejně jako dřív)
3. ✅ Pokračuje v běhu normálně

**Konverzace pak zmizí po restartu!**

---

## Příklad použití (Frontend)

### React/Next.js

```typescript
import { useState } from 'react';

function ChatComponent() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState([]);

  const sendMessage = async (message: string) => {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
      },
      body: JSON.stringify({
        message,
        session_id: sessionId  // null pro první zprávu
      })
    });

    const data = await response.json();
    
    // Ulož session_id z první odpovědi
    if (!sessionId) {
      setSessionId(data.session_id);
    }
    
    setMessages([...messages, {
      role: 'user',
      content: message
    }, {
      role: 'assistant',
      content: data.response
    }]);
  };

  const startNewChat = () => {
    setSessionId(null);  // Prostě reset - další zpráva vytvoří novou session
    setMessages([]);
  };

  return (
    <div>
      <button onClick={startNewChat}>New Chat</button>
      {/* ... zbytek UI ... */}
    </div>
  );
}
```

---

## Debugging

### Zkontrolovat Redis připojení

```bash
# V containeru
docker exec -it jarvis-redis redis-cli ping
# Očekávaný výstup: PONG

# Seznam sessions
docker exec -it jarvis-redis redis-cli KEYS "jarvis:session:*"
```

### Prohlédnout session data

```bash
# Načti data session
docker exec -it jarvis-redis redis-cli GET "jarvis:session:sess_abc123"
```

### Health check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "authentication": "nakonfigurováno",
  "redis": "connected"  // nebo "disconnected"
}
```