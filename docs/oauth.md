# OAuth integrace

## TickTick OAuth 2.0

### Co bylo implementováno

- Přidány dva nové endpointy do `src/api.py`:
    - `/api/ticktick/auth` – zahájí OAuth 2.0 autentizaci, vrací URL pro přesměrování na TickTick.
    - `/api/ticktick/callback` – zpracuje callback z TickTick, získá access/refresh tokeny a uloží je.
- Konfigurace (client_id, client_secret, callback_url) se načítá z `.env` souboru.
- Tokeny se ukládají do souboru `src/lib/ticktick_tokens.json`.
- Pro načítání proměnných z `.env` je použita knihovna `python-dotenv`.
- Pro komunikaci s TickTick API je použita knihovna `requests`.

### Proč takto

- Oddělené endpointy umožňují jasný OAuth flow (zahájení + zpracování callbacku).
- Ukládání tokenů do JSON souboru je jednoduché pro testování a další rozšíření (např. do DB).
- Konfigurace v `.env` je bezpečná a snadno měnitelná bez úprav kódu.
- Knihovny `python-dotenv` a `requests` jsou standardní pro práci s konfigurací a HTTP požadavky.

### Jak použít

1. Nastavte hodnoty v `.env`:
    - `CLIENT_ID`, `CLIENT_SECRET`, `CALLBACK_URL`
2. Otevřete `/api/ticktick/auth` – získáte URL pro přihlášení přes TickTick.
3. Po přihlášení TickTick přesměruje na `/api/ticktick/callback` – zde se získají a uloží tokeny.
4. Tokeny najdete v `src/lib/ticktick_tokens.json`.

---

Další OAuth integrace lze přidávat obdobně do tohoto souboru.
