# Dokumentace autentizace API

## Přehled

MCP Agent API používá **autentizaci pomocí API klíče** k ochraně citlivých endpointů. Toto poskytuje jednoduchou, bezstavovou autentizaci vhodnou pro osobní a interní použití.
## Nový: Přihlášení pomocí uživatelského jména a hesla

API nyní podporuje dva způsoby autentizace:

1. **Přímé použití API klíče** - Pro programový přístup (servery, skripty)
2. **Přihlášení přes username/password** - Získání API klíče po úspěšném přihlášení

### Přihlašovací endpoint

**POST /api/auth/login** - Veřejný endpoint pro získání API klíče

Tento endpoint umožňuje uživatelům získat API klíč zadáním uživatelského jména a hesla.

**Požadavek:**
```json
{
  "username": "admin",
  "password": "vase_heslo_zde"
}
```

**Úspěšná odpověď (200):**
```json
{
  "api_key": "nov9_vygenerovany_api_klic_zde",
  "message": "Přihlášení úspěšné. Použijte tento API klíč v hlavičce X-API-Key pro přístup k chráněným endpointům."
}
```

**Příklad použití:**

```bash
# Krok 1: Přihlášení a získání API klíče
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "vase_heslo"
  }'

# Odpověď:
# {
#   "api_key": "vygenerovany_klic_zde",
#   "message": "Přihlášení úspěšné..."
# }

# Krok 2: Použití získaného API klíče
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vygenerovany_klic_zde" \
  -d '{
    "message": "Ahoj!",
    "session_id": "test"
  }'
```

**JavaScript příklad:**
```javascript
// Krok 1: Přihlášení
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'admin',
    password: 'vase_heslo'
  })
});

const loginData = await loginResponse.json();
const apiKey = loginData.api_key;

// Krok 2: Použití API klíče
const chatResponse = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey
  },
  body: JSON.stringify({
    message: 'Ahoj!',
    session_id: 'user123'
  })
});

const chatData = await chatResponse.json();
console.log(chatData);
```

### Konfigurace uživatelských účtů

Přidejte přihlašovací údaje do souboru `.env`:

```env
# Uživatelské přihlašovací údaje (pro endpoint /api/auth/login)
USERNAME=admin
PASSWORD=vase_bezpecne_heslo_zde
```

**Důležité:**
- Heslo je hashováno pomocí SHA-256 před uložením
- Můžete mít pouze jednoho uživatele (v základní konfiguraci)
- Pro více uživatelů implementujte databázové řešení

### Chybové odpovědi přihlášení

**401 Unauthorized - Neplatné přihlašovací údaje:**
```json
{
  "detail": "Neplatné uživatelské jméno nebo heslo"
}
```

**422 Validation Error - Chybějící pole:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**503 Service Unavailable - Nejsou nakonfigurováni uživatelé:**
```json
{
  "detail": "Nejsou nakonfigurováni žádní uživatelé. Nastavte USERNAME a PASSWORD v .env souboru."
}
```


## Stav zabezpečení

### Chráněné endpointy ✅

Následující endpointy vyžadují autentizaci pomocí API klíče:

- **POST /api/chat** - REST chat endpoint
- **GET /api/chat/stream** - Server-Sent Events streaming
- **WS /ws/chat** - WebSocket real-time chat

### Veřejné endpointy 🌐

Tyto endpointy jsou veřejně přístupné:

- **GET /** - Informace o API
- **GET /health** - Health check

## Konfigurace

### 1. Vygenerování bezpečného API klíče

API klíč můžete vygenerovat pomocí jedné z těchto metod:

**Možnost A: Použití Pythonu**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Možnost B: Použití OpenSSL**
```bash
openssl rand -base64 32
```

**Možnost C: Online generátor**
Navštivte: https://www.uuidgenerator.net/ nebo https://randomkeygen.com/

### 2. Konfigurace proměnných prostředí

Přidejte svůj API klíč do souboru `.env`:

```env
# Jeden API klíč
API_KEY=vas_bezpecny_api_klic_zde

# NEBO více API klíčů (oddělených čárkami)
API_KEYS=klic1,klic2,klic3
```

**Důležité:** 
- Nahraďte `vas_bezpecny_api_klic_zde` svým skutečným vygenerovaným klíčem
- Udržujte své API klíče v tajnosti a nikdy je necommitujte do verzovacího systému
- Soubor `.env` je již v `.gitignore`

### 3. Restart serveru

Po aktualizaci souboru `.env` restartujte server:

```bash
python main.py
```

Nebo s uvicornem:

```bash
uvicorn main:app --reload
```

## Použití

### REST API (POST /api/chat)

Zahrňte API klíč v hlavičce `X-API-Key`:

**cURL příklad:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vas_api_klic_zde" \
  -d '{
    "message": "Ahoj, jak se máš?",
    "session_id": "uzivatel123"
  }'
```

**JavaScript/Fetch příklad:**
```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'vas_api_klic_zde'
  },
  body: JSON.stringify({
    message: 'Ahoj, jak se máš?',
    session_id: 'uzivatel123'
  })
});

const data = await response.json();
console.log(data);
```

**Python/Requests příklad:**
```python
import requests

headers = {
    'X-API-Key': 'vas_api_klic_zde'
}

data = {
    'message': 'Ahoj, jak se máš?',
    'session_id': 'uzivatel123'
}

response = requests.post(
    'http://localhost:8000/api/chat',
    headers=headers,
    json=data
)

print(response.json())
```

### Server-Sent Events (GET /api/chat/stream)

Zahrňte API klíč v hlavičce `X-API-Key`:

**cURL příklad:**
```bash
curl -N http://localhost:8000/api/chat/stream?message=Ahoj \
  -H "X-API-Key: vas_api_klic_zde"
```

**JavaScript/EventSource příklad:**
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/chat/stream?message=Ahoj',
  {
    headers: {
      'X-API-Key': 'vas_api_klic_zde'
    }
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### WebSocket (WS /ws/chat)

Poskytněte API klíč přes **parametr dotazu** nebo **hlavičku**:

**Možnost A: Parametr dotazu (doporučeno pro WebSocket)**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat?api_key=vas_api_klic_zde');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: 'Ahoj, jak se máš?'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

**Možnost B: Hlavička (pokud ji váš WebSocket klient podporuje)**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat', {
  headers: {
    'X-API-Key': 'vas_api_klic_zde'
  }
});
```

**Python/WebSockets příklad:**
```python
import asyncio
import websockets
import json

async def chat():
    uri = "ws://localhost:8000/ws/chat?api_key=vas_api_klic_zde"
    
    async with websockets.connect(uri) as websocket:
        # Odeslat zprávu
        await websocket.send(json.dumps({
            "message": "Ahoj, jak se máš?"
        }))
        
        # Přijmout odpověď
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(chat())
```

## Chybové odpovědi

### 401 Unauthorized - Chybí API klíč

```json
{
  "detail": "Chybí API klíč. Poskytněte hlavičku X-API-Key."
}
```

**Řešení:** Přidejte hlavičku `X-API-Key` do vašeho požadavku.

### 403 Forbidden - Neplatný API klíč

```json
{
  "detail": "Neplatný API klíč"
}
```

**Řešení:** Ověřte, že váš API klíč je správný a odpovídá tomu v `.env`.

### 500 Internal Server Error - Žádné API klíče nejsou nakonfigurovány

```json
{
  "detail": "Chyba konfigurace serveru: Žádné API klíče nejsou nakonfigurovány. Nastavte API_KEY nebo API_KEYS v proměnných prostředí."
}
```

**Řešení:** Přidejte `API_KEY` nebo `API_KEYS` do souboru `.env` a restartujte server.

## Specifické chyby WebSocket

WebSocket připojení budou uzavřena s kódem porušení zásad (1008) a před uzavřením obdrží chybovou zprávu:

```json
{
  "type": "error",
  "message": "Vyžadována autentizace: Chybí API klíč. Poskytněte přes 'api_key' parametr dotazu nebo 'X-API-Key' hlavičku"
}
```

## Bezpečnostní best practices

1. **Udržujte API klíče v tajnosti**
   - Nikdy necommitujte API klíče do verzovacího systému
   - Nesdílejte klíče na veřejných fórech nebo v dokumentaci
   - Používejte proměnné prostředí (soubor `.env`)

2. **Používejte HTTPS v produkci**
   - API klíče odeslané přes HTTP jsou zranitelné vůči odposlechu
   - Vždy používejte HTTPS/WSS v produkčních prostředích

3. **Pravidelně rotujte klíče**
   - Periodicky generujte nové API klíče
   - Odvolejte staré klíče, když již nejsou potřeba

4. **Používejte různé klíče pro různá prostředí**
   - Vývoj: `API_KEY=dev_klic_zde`
   - Produkce: `API_KEY=prod_klic_zde`

5. **Monitorujte přístup**
   - Kontrolujte serverové logy pro pokusy o neautorizovaný přístup
   - Implementujte rate limiting (zvažte přidání v budoucnu)

6. **Omezte odhalení klíčů**
   - Používejte serverový kód pro volání API, když je to možné
   - Vyhněte se odhalení klíčů v klientském JavaScriptu v produkci

## Testování autentizace

### Kontrola Health endpointu (autentizace není vyžadována)

```bash
curl http://localhost:8000/health
```

Očekávaná odpověď:
```json
{
  "status": "healthy",
  "authentication": "nakonfigurováno"
}
```

### Test chráněného endpointu bez autentizace (měl by selhat)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "test"}'
```

Očekávaná odpověď (401):
```json
{
  "detail": "Chybí API klíč. Poskytněte hlavičku X-API-Key."
}
```

### Test chráněného endpointu s autentizací (měl by uspět)

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vas_api_klic_zde" \
  -d '{"message": "test", "session_id": "test"}'
```

Očekávaná odpověď (200):
```json
{
  "response": "...",
  "session_id": "test"
}
```
## Testování přihlašovacího endpointu

### Test přihlášení

```bash
# Spusťte testovací skript
python test/test_login.py
```

Tento test ověří:
- ✅ Přihlášení s platnými údaji vrací API klíč
- ✅ Přihlášení s neplatnými údaji je zamítnuto (401)
- ✅ Vygenerovaný API klíč funguje pro přístup k chráněným endpointům
- ✅ Chybějící pole jsou správně validována (422)

### Manuální test přihlášení

```bash
# Test přihlášení
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "vase_heslo"}'

# Očekávaná odpověď (200):
# {
#   "api_key": "vygenerovany_klic",
#   "message": "Přihlášení úspěšné..."
# }

# Test s neplatnými údaji
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "spatny", "password": "spatne"}'

# Očekávaná odpověď (401):
# {
#   "detail": "Neplatné uživatelské jméno nebo heslo"
# }
```


## Řešení problémů

### Chyba "Žádné API klíče nejsou nakonfigurovány"

1. Ověřte, že soubor `.env` existuje v kořenovém adresáři projektu
2. Zkontrolujte, že `API_KEY` nebo `API_KEYS` je nastaven v `.env`
3. Restartujte server po úpravě `.env`
4. Ujistěte se, že je nainstalován `python-dotenv`: `pip install python-dotenv`

### Autentizace funguje lokálně, ale ne v Dockeru

1. Ujistěte se, že je `.env` připojen v `docker-compose.yml`:
   ```yaml
   volumes:
     - .env:/app/.env
   ```
2. Nebo použijte `env_file` v `docker-compose.yml`:
   ```yaml
   env_file:
     - .env
   ```
3. Znovu sestavte kontejner: `docker-compose up --build`

### WebSocket připojení zamítnuto

1. Ověřte, že API klíč je předán jako parametr dotazu: `?api_key=vas_klic`
2. Zkontrolujte, že URL WebSocket obsahuje klíč
3. Ujistěte se, že klíč je URL-encodovaný, pokud obsahuje speciální znaky

## Průvodce migrací

Pokud upgradujete z verze bez autentizace:

1. **Aktualizujte závislosti**
   ```bash
   pip install -r requirements.txt
   ```

2. **Vygenerujte API klíč a nastavte uživatelské údaje**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Aktualizujte soubor `.env`**
   ```env
   # Přímý API klíč (pro programový přístup)
   API_KEY=<vygenerovany_klic>
   
   # Uživatelské přihlašovací údaje (pro endpoint /api/auth/login)
   USERNAME=admin
   PASSWORD=<vase_bezpecne_heslo>
   ```

4. **Aktualizujte kód klienta**
   
   **Možnost A: Použití existujícího API klíče**
   - Přidejte hlavičku `X-API-Key` do všech požadavků
   - Pro WebSocket: Přidejte `?api_key=<klic>` do URL připojení
   
   **Možnost B: Získání API klíče přes přihlášení**
   - Implementujte flow: přihlášení → získání klíče → použití klíče
   - Vhodné pro webové aplikace s uživatelským rozhraním

5. **Otestujte všechny endpointy**
   - Ověřte, že chráněné endpointy zamítají požadavky bez klíčů
   - Ověřte, že chráněné endpointy přijímají požadavky s platnými klíči
   - Ověřte, že veřejné endpointy stále fungují bez autentizace
   - Otestujte přihlašovací endpoint: `python test/test_login.py`

## Podpora

Pro problémy nebo otázky:
1. Zkontrolujte chybové zprávy v serverových logách
2. Ověřte konfiguraci `.env`
3. Testujte s příklady uvedenými výše
4. Prostudujte [API Dokumentaci](README_API.md)