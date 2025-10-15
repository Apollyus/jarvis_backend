# Automatické obnovování Notion tokenů

## Problém

Notion OAuth tokeny mají omezenou životnost (obvykle 1 hodina). Když token vyprší, API vrací 401 Unauthorized a aplikace přestane fungovat.

## Řešení

Implementovali jsme **automatické obnovování tokenů** na několika úrovních:

### 1. Proaktivní refresh při získání tokenu

**Soubor:** `src/notion-mcp/notion_client.py`

Když zavoláš `get_notion_access_token()`, automaticky:
- Zkontroluje, zda token brzy expiruje (< 5 minut)
- Pokud ano, automaticky ho obnoví pomocí refresh tokenu
- Uloží nový token včetně `expires_at` timestamp

```python
# Při každém volání se kontroluje expiration
token = get_notion_access_token()  # Auto-refresh pokud je potřeba
```

### 2. Retry při auth chybě

**Soubor:** `src/lib/agent_core.py`

Když agent dostane 401 chybu:
1. Detekuje authentication error
2. Reinicializuje MCP klienta s novým tokenem
3. Zopakuje dotaz automaticky

```python
async def run_query(self, message: str, session_id: str = "default", retry_on_auth_error: bool = True):
    try:
        result = await agent.run(message)
    except Exception as e:
        if '401' in str(e) or 'unauthorized' in str(e).lower():
            await self.reinitialize_client()  # Načte fresh token
            return await self.run_query(message, session_id, retry_on_auth_error=False)
```

### 3. Správné ukládání expiration info

**Soubor:** `src/api.py`, `src/notion-mcp/notion_client.py`

Tokeny se ukládají s expiration timestamps:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 3600,
  "expires_at": 1729012345,
  "obtained_at": 1729008745
}
```

## Jak to funguje

### Časová osa

```
Token získán:     expires_at = now + 3600s (1 hodina)
                  |
                  v
Po 55 minutách:   get_notion_access_token() detekuje
                  že expiruje za < 5 min
                  |
                  v
Automatický       _refresh_access_token()
refresh:          -> nový access_token
                  -> nový expires_at
                  -> uloženo do JSON
                  |
                  v
Agent pokračuje   Bez přerušení služby!
```

### Fallback při chybě

```
Request → MCP server
          |
          v
    401 Unauthorized?
          |
     ┌────┴────┐
     |         |
    Ano       Ne
     |         |
     v         v
Reinit     Pokračuj
+ Retry    normálně
```

## Manuální refresh

Pokud potřebuješ manuálně obnovit token:

```python
from notion_client import get_notion_client

client = get_notion_client()
success = client._refresh_access_token()
if success:
    print("Token obnoven!")
```

## Získání nových tokenů

Když refresh token expiruje (obvykle po 90 dnech), musíš zopakovat autorizaci:

```bash
python get_notion_token.py
```

Token se automaticky nahraje na VPS.

## Logování

V logách uvidíš:

```
Token brzy expiruje (285s), obnovuji...
✓ Notion access token úspěšně obnoven
✓ Token automaticky obnoven
```

Nebo při chybě:

```
⚠️  Detekována auth chyba, pokouším se reinicializovat s novými tokeny...
✓ Notion tokeny načteny z ...
```

## Troubleshooting

### Token se pořád neobnovuje

1. **Zkontroluj, že máš refresh_token:**
   ```bash
   cat src/lib/tokens/notion_tokens.json
   ```
   Měl by obsahovat `refresh_token` field.

2. **Zkontroluj logs:**
   ```
   2025-10-15 17:01:50 - mcp_use - ERROR - HTTP Request: POST https://mcp.notion.com/mcp "HTTP/1.1 401 Unauthorized"
   ```
   Tato chyba by měla automaticky spustit reinit.

3. **Pokud refresh selže:**
   - Refresh token možná expiroval (90 dní)
   - Spusť `python get_notion_token.py` pro nové tokeny

### "No such file or directory: notion_tokens.json"

Složka `src/lib/tokens/` neexistuje. Vytvoř ji a nahraj tokeny:

```bash
mkdir -p src/lib/tokens
python get_notion_token.py
```

## Bezpečnost

- **Tokeny jsou citlivé!** Nikdy je necommituj do gitu
- `.gitignore` obsahuje `src/lib/tokens/`
- Používej silný API_KEY pro upload endpoint
