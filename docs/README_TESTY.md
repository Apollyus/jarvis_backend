# Dokumentace Testů

Tento dokument popisuje testovací skripty projektu Jarvis Backend a poskytuje kompletní průvodce pro jejich použití, pochopení a rozšiřování.

---

## 📋 Obsah

1. [Přehled testů](#přehled-testů)
2. [Test agenta (`agent_test.py`)](#test-agenta-agent_testpy)
3. [Test API konverzací (`api_conversation_test.py`)](#test-api-konverzací-api_conversation_testpy)
4. [Jak spustit testy](#jak-spustit-testy)
5. [Předpoklady a nastavení](#předpoklady-a-nastavení)
6. [Výstup testů](#výstup-testů)
7. [Jak přidat nové testy](#jak-přidat-nové-testy)
8. [Architektura testování](#architektura-testování)
9. [Nejčastější problémy](#nejčastější-problémy)

---

## Přehled testů

Projekt obsahuje dva hlavní testovací skripty:

| Soubor | Účel | Typ testu |
|--------|------|-----------|
| [`test/agent_test.py`](../test/agent_test.py) | Testuje základní funkcionalitu MCP agenta | Integrační test |
| [`test/api_conversation_test.py`](../test/api_conversation_test.py) | Testuje API konverzační schopnosti | E2E test |

### Proč máme dva různé testy?

- **`agent_test.py`** - Testuje **jádro systému** (agent s MCP nástroji) izolovaně
- **`api_conversation_test.py`** - Testuje **kompletní API** včetně session managementu a vícenásobných konverzací

Tato rozdílnost umožňuje odhalit problémy na různých úrovních aplikace.

---

## Test agenta (`agent_test.py`)

### Co tento test dělá?

Test [`agent_test.py`](../test/agent_test.py) je **základní integrační test**, který ověřuje, že:

1. MCP agent se dokáže správně inicializovat
2. Může se připojit k externím MCP serverům (např. Notion)
3. Dokáže zpracovat příkazy a vyvolat nástroje
4. LLM model správně komunikuje s MCP klientem

### Architektura testu

```python
┌─────────────────┐
│   LLM Model     │ ← Google Gemini přes OpenRouter
│  (Gemini 2.5)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Agent     │ ← Propojuje LLM s nástroji
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MCP Client    │ ← Komunikuje s MCP servery
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Notion MCP     │ ← Skutečný Notion server
│    Server       │
└─────────────────┘
```

### Kód s vysvětlením

```python
# 1. Inicializace LLM modelu
llm = ChatOpenAI(
    model="google/gemini-2.5-flash-lite-preview-09-2025",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=OPENROUTER_API_KEY,
    temperature=0,  # Deterministické odpovědi pro testování
)
```

**Proč Gemini přes OpenRouter?**
- OpenRouter poskytuje jednotné API pro různé modely
- Gemini 2.5 Flash je rychlý a levný pro testy
- Používá OpenAI SDK, takže je kompatibilní s LangChain

```python
# 2. Konfigurace MCP serverů
config = {
    "mcpServers": {
        "Notion": {
            "url": "https://mcp.notion.com/mcp"
        }
    }
}
```

**Proč tato struktura?**
- Umožňuje snadné přidávání dalších MCP serverů
- Každý server může mít vlastní konfiguraci
- Oficiální Notion MCP server je hostovaný na mcp.notion.com

```python
# 3. Vytvoření agenta
agent = MCPAgent(llm=llm, client=client, max_steps=30)
```

**Parametr `max_steps=30`:**
- Omezuje maximální počet kroků agenta
- Zabraňuje nekonečným smyčkám
- 30 kroků je dostatečné pro většinu operací

```python
# 4. Spuštění testu
result = await agent.run("Vytvoř novou stránku...")
```

**Co se děje při spuštění?**
1. Agent pošle prompt LLM modelu
2. LLM rozhodne, jaké nástroje použít
3. MCP Client vykoná požadované akce
4. Výsledky se vrátí zpět do LLM
5. LLM zformuluje finální odpověď

### Co test ověřuje?

✅ **Správná integrace komponent:**
- LLM komunikuje s MCP agentem
- Agent správně volá MCP nástroje
- Notion MCP server je dostupný

✅ **Funkčnost základního workflow:**
- Vytvoření stránky v Notion
- Zápis obsahu na stránku

❌ **Co test NEOVĚŘUJE:**
- API endpointy
- Session management
- Vícenásobné konverzace
- Error handling na API úrovni

---

## Test API konverzací (`api_conversation_test.py`)

### Co tento test dělá?

Test [`api_conversation_test.py`](../test/api_conversation_test.py) je **komplexní E2E (end-to-end) test**, který ověřuje:

1. ✅ HTTP API endpointy fungují správně
2. ✅ Session management udržuje kontext
3. ✅ Vícenásobné session běží nezávisle
4. ✅ Konverzační kontext se zachovává napříč zprávami
5. ✅ API zvládá timeout a chybové stavy

### Architektura testu

```
┌──────────────┐         HTTP POST         ┌──────────────┐
│ Test Script  │ ───────────────────────▶  │  FastAPI     │
│              │                            │  Server      │
│ (requests)   │ ◀───────────────────────   │ (:8000)      │
└──────────────┘         JSON Response      └──────┬───────┘
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │ Session      │
                                            │ Manager      │
                                            └──────┬───────┘
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │ MCP Agent    │
                                            └──────────────┘
```

### Struktura testů

Test obsahuje **5 hlavních testovacích scénářů**, každý s jiným účelem:

#### 🧪 Test 1: Jednoduchá konverzace

**Soubor:** [`test_single_conversation()`](../test/api_conversation_test.py:102)

**Co testuje:**
- Základní funkčnost API
- Jeden požadavek → jedna odpověď
- Správné formátování JSON

**Příklad:**
```python
send_message("Hello! What can you help me with?", "test-single")
```

**Očekávaný výstup:**
```json
{
  "response": "I'm an AI assistant...",
  "session_id": "test-single"
}
```

**Proč tento test?**
- Je to nejjednodušší test - pokud selže, něco je špatně na základní úrovni
- Rychle odhalí problémy s připojením nebo konfigurací

---

#### 🔄 Test 2: Vícenásobná konverzace s kontextem

**Soubor:** [`test_multi_turn_conversation()`](../test/api_conversation_test.py:119)

**Co testuje:**
- Zachování kontextu mezi zprávami
- Session management
- Schopnost navázat na předchozí zprávu

**Scénář:**
```python
# 1. První zpráva
send_message("Hi! Can you tell me what you can do?", session_id)

# 2. Navazující otázka (používá kontext!)
send_message("Can you give me a specific example?", session_id)

# 3. Další navazování
send_message("That's interesting, thank you!", session_id)
```

**Proč je to důležité?**
- **Skutečné konverzace vyžadují kontext** - uživatel neříká vše v jedné zprávě
- Test ověřuje, že "Can you give me a specific example?" se vztahuje k předchozí zprávě
- Bez kontextu by agent nevěděl, na co má dát příklad

**Co by se mělo stát:**
- Agent si pamatuje předchozí zprávy
- Odpovědi jsou relevantní k celé konverzaci
- Není potřeba opakovat informace

---

#### 🔀 Test 3: Více nezávislých session

**Soubor:** [`test_multiple_sessions()`](../test/api_conversation_test.py:153)

**Co testuje:**
- Izolace session
- Paralelní konverzace
- Správné přepínání mezi kontexty

**Scénář:**
```python
# Session 1: O Notion
send_message("I want to create a new page in Notion", "session-1")

# Session 2: Úplně jiné téma
send_message("What's the weather like today?", "session-2")

# Zpět do Session 1: Měl by pamatovat Notion kontext
send_message("What information do you need from me?", "session-1")
```

**Proč je to kritické?**
- V produkci může API obsluhovat **stovky uživatelů současně**
- Každý uživatel má vlastní session
- Kontext jednoho uživatele **nesmí ovlivnit** kontext jiného uživatele

**Očekávané chování:**
- Session 1 si pamatuje kontext o Notion
- Session 2 je nezávislá
- Návrat do Session 1 pokračuje tam, kde konverzace skončila

---

#### 💾 Test 4: Persistence kontextu

**Soubor:** [`test_session_persistence()`](../test/api_conversation_test.py:189)

**Co testuje:**
- Dlouhodobé uložení informací v session
- Schopnost vybavit si fakta z historie

**Scénář:**
```python
# Nastavení kontextu
send_message("My favorite color is blue", session_id)

time.sleep(2)  # Simulace časového odstupu

# Test vzpomínky
send_message("What's my favorite color?", session_id)
```

**Proč to testujeme?**
- Ověřuje, že session management skutečně funguje
- Kontext musí přežít i časový odstup
- V reálné aplikaci by uživatel mohl pokračovat i po hodinách

**Očekávaný výsledek:**
- Agent správně odpoví "blue"
- Prokáže, že session drží data napříč časem

---

#### 🎯 Test 5: Notion workflow

**Soubor:** [`test_notion_workflow()`](../test/api_conversation_test.py:215)

**Co testuje:**
- Reálný use-case s MCP nástroji
- Komplexní workflow
- Integrace s externími službami

**Scénář:**
```python
# 1. Zjištění schopností
send_message("Can you help me work with Notion?", session_id)

# 2. Konkrétní akce
send_message("Create a new page called 'Test Page'...", session_id)

# 3. Verifikace
send_message("Was the page created successfully?", session_id)
```

**Proč tento test?**
- Testuje **skutečnou funkčnost**, kterou uživatelé budou používat
- Ověřuje integraci API s MCP nástroji
- Odhalí problémy v celém stacku

**Poznámka:**
- Tento test vyžaduje správně nakonfigurovaný Notion MCP server
- Bez konfigurace může selhat, ale to je OK

---

### Pomocné funkce

#### `check_api_health()`

**Účel:** Ověřit, že API server běží před spuštěním testů

```python
def check_api_health() -> bool:
    response = requests.get(HEALTH_ENDPOINT, timeout=5)
    return response.status_code == 200
```

**Proč je to důležité?**
- Zabraňuje ztrátě času, pokud server neběží
- Poskytuje jasnou chybovou zprávu
- Testy by jinak selhaly s matoucími chybami

---

#### `send_message()`

**Účel:** Centralizovaná funkce pro posílání zpráv do API

```python
def send_message(message: str, session_id: str = "default") -> Dict[str, Any]:
    payload = {
        "message": message,
        "session_id": session_id
    }
    response = requests.post(CHAT_ENDPOINT, json=payload, timeout=60)
    return response.json()
```

**Proč timeout=60?**
- Agent může zpracovávat komplexní požadavky
- Volání MCP nástrojů trvá čas
- 60 sekund je rozumný limit pro většinu operací

**Proč centralizovaná funkce?**
- DRY princip (Don't Repeat Yourself)
- Konzistentní error handling
- Snadné debugování všech requestů

---

## Jak spustit testy

### Test agenta

```bash
# 1. Ujistěte se, že máte správné .env soubor s OPENROUTER_API_KEY
# 2. Nainstalujte závislosti
pip install -r requirements.txt

# 3. Spusťte test
python test/agent_test.py
```

**Očekávaný výstup:**
```
=== Výsledek ===
Stránka 'Poznatky' byla úspěšně vytvořena s textem: 
Růže jsou rudé a fialky modré.
```

---

### Test API konverzací

```bash
# 1. Spusťte API server v jednom terminálu
python src/api.py

# 2. V druhém terminálu spusťte test
python test/api_conversation_test.py
```

**Očekávaný výstup:**
```
╔════════════════════════════════════════════════╗
║   MCP Agent API - Conversation Test Script    ║
╚════════════════════════════════════════════════╝

--- Checking API Health ---
✓ API is healthy and running

======================================================================
  TEST 1: Single Message Conversation
======================================================================

[18:30:15] [Session: test-single] USER:
  Hello! What can you help me with?

[18:30:17] [Session: test-single] AGENT:
  I'm an AI assistant that can help with...

✓ Single message test passed

...
```

---

## Předpoklady a nastavení

### Požadavky

1. **Python 3.8+**
2. **Nainstalované balíčky:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment proměnné** (soubor `.env`):
   ```env
   OPENROUTER_API_KEY=your_api_key_here
   NOTION_API_KEY=your_notion_key_here  # Pro Notion testy
   ```

4. **Běžící API server** (pro `api_conversation_test.py`):
   ```bash
   python src/api.py
   ```

### Nastavení Notion MCP

Pro plnou funkčnost Notion testů:

1. Zaregistrujte se na [mcp.notion.com](https://mcp.notion.com)
2. Získejte API klíč
3. Přidejte do `.env`:
   ```env
   NOTION_API_KEY=your_key_here
   ```

---

## Výstup testů

### Úspěšný test

```
✓ API is healthy and running
✓ Single message test passed
✓ Multi-turn conversation test completed
✓ Multiple sessions test completed
✓ Context persistence test completed
✓ Notion workflow test completed

✓ All tests executed successfully!

Key Observations:
  • Sessions maintain independent conversation contexts
  • Multi-turn conversations preserve context within sessions
  • The API supports concurrent sessions
```

### Neúspěšný test

```
✗ Cannot connect to API at http://localhost:8000
  Make sure the API server is running: python src/api.py

❌ API is not available. Please start the server first
```

**Co dělat:**
1. Zkontrolujte, že API server běží
2. Ověřte port (výchozí: 8000)
3. Zkontrolujte firewall

---

## Jak přidat nové testy

### Přidání testu do `agent_test.py`

```python
async def test_new_feature():
    """Test nové funkcionality"""
    # 1. Nastavení
    llm = ChatOpenAI(...)
    config = {...}
    client = MCPClient.from_dict(config)
    agent = MCPAgent(llm=llm, client=client)
    
    # 2. Spuštění
    result = await agent.run("Tvůj testovací prompt")
    
    # 3. Ověření
    assert "očekávaný text" in result
    print("✓ Test prošel")

# Přidání do main()
if __name__ == "__main__":
    asyncio.run(test_new_feature())
```

---

### Přidání testu do `api_conversation_test.py`

```python
def test_new_scenario():
    """Test 6: Tvůj nový scénář"""
    print_section("TEST 6: Nový Scénář")
    
    session_id = "test-new"
    
    # Tvoje testovací kroky
    send_message("První zpráva", session_id)
    time.sleep(1)
    send_message("Druhá zpráva", session_id)
    
    print("\n✓ Nový test dokončen")

# Přidání do run_all_tests()
def run_all_tests():
    ...
    test_new_scenario()  # Přidat sem
    ...
```

---

## Architektura testování

### Proč tyto přístupy?

#### 1. **Integrační test (`agent_test.py`)**

```
[Test] → [Agent] → [MCP] → [Notion]
   ↓         ↓        ↓        ↓
 Rychlý   Logika  Nástroje  Služba
```

**Výhody:**
- ✅ Rychlý setup
- ✅ Testuje core logiku
- ✅ Izolovaný od API vrstvy

**Nevýhody:**
- ❌ Netestuje API endpoints
- ❌ Netestuje session management

---

#### 2. **E2E test (`api_conversation_test.py`)**

```
[Test] → [HTTP] → [API] → [Sessions] → [Agent] → [MCP]
   ↓       ↓       ↓         ↓           ↓         ↓
Requests FastAPI Routes  Memory     LangChain  Notion
```

**Výhody:**
- ✅ Testuje celý stack
- ✅ Reálné HTTP requesty
- ✅ Session management

**Nevýhody:**
- ❌ Pomalejší
- ❌ Vyžaduje běžící server
- ❌ Složitější debug

---

### Test Pyramid

```
        /\
       /  \
      / E2E \         ← api_conversation_test.py (1 soubor)
     /________\
    /          \
   / Integration \    ← agent_test.py (1 soubor)
  /______________\
 /                \
/   Unit Tests     \  ← Zatím nemáme
/____________________\
```

**Současný stav:**
- ✅ Integration tests
- ✅ E2E tests
- ⚠️ Unit tests - můžeme přidat v budoucnu

---

## Nejčastější problémy

### ❌ "Cannot connect to API"

**Příčina:** API server neběží

**Řešení:**
```bash
python src/api.py
```

---

### ❌ "Request timed out"

**Příčina:** Agent zpracovává komplexní požadavek

**Řešení:**
- Počkejte déle (timeout je 60s)
- Zkontrolujte OPENROUTER_API_KEY
- Zkontrolujte připojení k internetu

---

### ❌ "Notion MCP server not configured"

**Příčina:** Chybí NOTION_API_KEY

**Řešení:**
```bash
# Přidejte do .env
NOTION_API_KEY=your_key_here
```

---

### ❌ "Module not found"

**Příčina:** Chybí závislosti

**Řešení:**
```bash
pip install -r requirements.txt
```

---

## Best Practices pro testování

### ✅ DO - Doporučené praktiky

1. **Vždy kontroluj health před testy**
   ```python
   if not check_api_health():
       sys.exit(1)
   ```

2. **Používej pauzy mezi requesty**
   ```python
   time.sleep(1)  # Dej agentovi čas na odpověď
   ```

3. **Používej unikátní session ID**
   ```python
   session_id = f"test-{test_name}-{timestamp}"
   ```

4. **Loguj vše**
   ```python
   print_message("USER", message, session_id)
   ```

5. **Testuj edge cases**
   - Prázdné zprávy
   - Velmi dlouhé zprávy
   - Neplatné session ID

### ❌ DON'T - Nedoporučené praktiky

1. ❌ **Nespouštěj testy bez health checku**
2. ❌ **Nepoužívej stejné session ID pro různé testy**
3. ❌ **Nepředpokládej pořadí testů**
4. ❌ **Nevynechávej error handling**
5. ❌ **Netestuj v produkci**

---

## Shrnutí

### Co testy dělají?

| Test | Účel | Co ověřuje |
|------|------|------------|
| `agent_test.py` | Testuje MCP agenta | ✅ LLM integrace<br>✅ MCP nástroje<br>✅ Základní workflow |
| `api_conversation_test.py` | Testuje API | ✅ HTTP endpoints<br>✅ Sessions<br>✅ Kontext<br>✅ Vícenásobné konverzace |

### Kdy použít který test?

- **Vyvíjíš novou MCP funkci?** → `agent_test.py`
- **Měníš API endpoints?** → `api_conversation_test.py`
- **Přidáváš session management?** → `api_conversation_test.py`
- **Debuguješ LLM chování?** → `agent_test.py`

### Další kroky

1. ✅ Přidej unit testy pro jednotlivé komponenty
2. ✅ Přidej performance testy
3. ✅ Automatizuj testy v CI/CD
4. ✅ Přidej code coverage reporting

---

## Kontakt a podpora

Máš-li otázky ohledně testů:

1. Zkontroluj tuto dokumentaci
2. Projdi kód testů s komentáři
3. Podívej se na [API dokumentaci](README_API.md)
4. Vytvoř issue v repozitáři

---

**Poslední aktualizace:** Říjen 2025  
**Verze dokumentace:** 1.0  
**Jazyk:** Čeština