# Testovací dokumentace

Přehled testů pro MCP Agent API backend.

## 📋 Dostupné testy

### 1. Test autentizace (`test/test_authentication.py`)

Komplexní testovací sada pro ověření API key autentizace.

**Co testuje:**
- ✅ Veřejné endpointy jsou přístupné bez autentizace
- ✅ Chráněné endpointy zamítají požadavky bez API klíče (401)
- ✅ Chráněné endpointy zamítají neplatné API klíče (403)
- ✅ Chráněné endpointy akceptují platné API klíče (200)
- ✅ Streaming endpointy fungují s autentizací

**Spuštění:**
```bash
# Ujistěte se, že server běží
python main.py

# V novém terminálu spusťte testy
python test/test_authentication.py
```

**Očekávaný výstup:**
```
============================================================
API Authentication Test Suite
============================================================
Base URL: http://localhost:8000
API Key: your_secur...
============================================================

[TEST 1] Health Endpoint (Public)
------------------------------------------------------------
Status Code: 200
✅ PASSED: Health endpoint accessible without authentication

[TEST 2] Root Endpoint (Public)
------------------------------------------------------------
Status Code: 200
✅ PASSED: Root endpoint accessible without authentication

[TEST 3] POST /api/chat Without Authentication
------------------------------------------------------------
Status Code: 401
✅ PASSED: Chat endpoint correctly rejects unauthenticated requests

[TEST 4] POST /api/chat With Invalid API Key
------------------------------------------------------------
Status Code: 403
✅ PASSED: Chat endpoint correctly rejects invalid API key

[TEST 5] POST /api/chat With Valid API Key
------------------------------------------------------------
Status Code: 200
✅ PASSED: Chat endpoint accessible with valid API key

[TEST 6] GET /api/chat/stream Without Authentication
------------------------------------------------------------
Status Code: 401
✅ PASSED: Stream endpoint correctly rejects unauthenticated requests

[TEST 7] GET /api/chat/stream With Valid API Key
------------------------------------------------------------
Status Code: 200
✅ PASSED: Stream endpoint accessible with valid API key

============================================================
TEST SUMMARY
============================================================
✅ PASS: Health Endpoint
✅ PASS: Root Endpoint
✅ PASS: Chat Without Auth
✅ PASS: Chat With Invalid Key
✅ PASS: Chat With Valid Key
✅ PASS: Stream Without Auth
✅ PASS: Stream With Valid Key
------------------------------------------------------------
Total: 7/7 tests passed (100%)
============================================================
```

### 2. Test konverzace (`test/api_conversation_test.py`)

Testuje základní funkcionalitu chatovacího agenta.

**Co testuje:**
- Jednoduchá konverzace s agentem
- Správa session
- Zachování kontextu

**Spuštění:**
```bash
python test/api_conversation_test.py
```

**Poznámka:** Po implementaci autentizace je nutné aktualizovat tento test, aby zahrnoval API klíč v hlavičkách.

### 3. Test agenta (`test/agent_test.py`)

Testuje základní funkcionalitu MCP agenta.

**Spuštění:**
```bash
python test/agent_test.py
```

## 🔧 Nastavení testů

### Požadavky

```bash
pip install -r requirements.txt
pip install -r test/requirements.txt  # Pokud existují dodatečné závislosti
```

### Konfigurace prostředí

Ujistěte se, že máte správně nakonfigurovaný `.env` soubor:

```env
# API klíče pro služby
OPENROUTER_API_KEY=your_openrouter_key
NOTION_API_KEY=your_notion_key

# API autentizace (POVINNÉ pro testy)
API_KEY=your_secure_api_key_here
```

## 🚀 Spuštění všech testů

```bash
# Spusťte server
python main.py &

# Počkejte 2 sekundy, než se server spustí
sleep 2

# Spusťte testy autentizace
python test/test_authentication.py

# Spusťte testy konverzace (pokud jsou aktualizované)
# python test/api_conversation_test.py

# Spusťte testy agenta
# python test/agent_test.py

# Zastavte server
pkill -f "python main.py"
```

## 📊 Interpretace výsledků

### Úspěšný test
```
✅ PASSED: Test description
```

### Neúspěšný test
```
❌ FAILED: Test description
```

### Chyba testu
```
❌ ERROR: Error message
```

## 🐛 Řešení problémů

### Server není spuštěný
```
❌ ERROR: Server is not running!
Please start the server first: python main.py
```

**Řešení:** Spusťte server v samostatném terminálu:
```bash
python main.py
```

### API klíč není nakonfigurován
```
❌ ERROR: Server configuration error: No API keys configured
```

**Řešení:** Přidejte `API_KEY` do souboru `.env`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))" >> .env
# Poté ručně upravte .env a přidejte: API_KEY=<vygenerovaný_klíč>
```

### Test selhal s 500 chybou
```
❌ FAILED: Chat endpoint returned 500 Internal Server Error
```

**Řešení:**
1. Zkontrolujte logy serveru pro detailní chybovou zprávu
2. Ověřte, že jsou správně nastavené všechny proměnné prostředí
3. Ujistěte se, že MCP servery jsou dostupné

### Autentizační testy selhávají
```
❌ FAILED: Chat endpoint should return 401 without auth
```

**Možné příčiny:**
1. Autentizace není správně implementována
2. Server používá starou verzi kódu (restartujte server)
3. API klíč v `.env` není správně načten

## 📝 Přidání nových testů

### Struktura testu

```python
def test_new_feature():
    """Test description"""
    print("\n[TEST X] Test Name")
    print("-" * 60)
    
    try:
        # Test logic here
        response = requests.get(f"{BASE_URL}/endpoint")
        
        if response.status_code == 200:
            print("✅ PASSED: Test succeeded")
            return True
        else:
            print("❌ FAILED: Test failed")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
```

### Přidání testu do test suite

```python
def run_all_tests():
    tests = [
        ("Test Name", test_new_feature),
        # ... další testy
    ]
    # ... zbytek kódu
```

## 🔍 Best Practices

1. **Izolace testů**: Každý test by měl být nezávislý
2. **Čištění**: Cleanup po testech (smazání testovacích session, atd.)
3. **Jasné zprávy**: Výstup testu by měl jasně indikovat co se testuje
4. **Error handling**: Zachycujte a hlaste všechny výjimky
5. **Dokumentace**: Každý test by měl mít docstring s popisem

## 📚 Další informace

- [API Documentation](README_API.md)
- [Authentication Documentation](README_AUTHENTICATION.md)
- [Docker Documentation](README_DOCKER.md)