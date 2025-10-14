"""
Jednoduchý skript pro získání Notion OAuth Access Token

POUŽITÍ:
1. Spusť: python get_notion_token.py
2. Otevře se prohlížeč, schval přístup
3. Tokeny se uloží do src/lib/tokens/notion_tokens.json
4. Hotovo! Server bude automaticky obnovovat tokeny.

Stejný princip jako TickTick OAuth.
"""

import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import json
from pathlib import Path

# Notion OAuth konfigurace (public client)
CLIENT_ID = "YvWLaE2nKO861jM1"
REDIRECT_URI = "http://localhost:8080/callback"
AUTH_URL = "https://mcp.notion.com/authorize"
TOKEN_URL = "https://mcp.notion.com/token"

# Cesta k token souboru (stejné jako TickTick)
TOKEN_FILE = Path(__file__).parent / "src" / "lib" / "tokens" / "notion_tokens.json"

# Globální proměnná pro uložení kódu
auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        
        # Parsuj URL
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            
            # Odpověz do prohlížeče
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body>
                    <h1>Authorization successful!</h1>
                    <p>You can close this window and return to terminal.</p>
                    <script>window.close();</script>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Vypni logy

def get_access_token():
    """Získá access token pomocí OAuth flow"""
    
    print("=" * 60)
    print("Notion OAuth Access Token Getter")
    print("=" * 60)
    print()
    
    # 1. Vytvoř authorization URL
    auth_url = f"{AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
    
    print("Step 1: Opening browser for authorization...")
    print(f"URL: {auth_url}")
    print()
    
    # 2. Spusť lokální server
    server = HTTPServer(('localhost', 8080), CallbackHandler)
    
    # 3. Otevři prohlížeč
    webbrowser.open(auth_url)
    
    print("Step 2: Waiting for authorization...")
    print("(Approve access in your browser)")
    print()
    
    # 4. Čekej na callback (max 1 request)
    server.handle_request()
    
    if not auth_code:
        print("❌ Error: No authorization code received")
        return None
    
    print("✓ Authorization code received")
    print()
    
    # 5. Vyměň code za access token
    print("Step 3: Exchanging code for access token...")
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID
    }
    
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None
    
    token_data = response.json()
    
    print("✓ Access token received")
    print()
    
    # Ulož do JSON souboru
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)
    
    print("=" * 60)
    print(f"✓ Tokens saved to: {TOKEN_FILE}")
    print("=" * 60)
    print()
    print("ACCESS TOKEN:")
    print(token_data['access_token'])
    print()
    
    if 'refresh_token' in token_data:
        print("REFRESH TOKEN:")
        print(token_data['refresh_token'])
        print()
    
    if 'expires_in' in token_data:
        print(f"Expires in: {token_data['expires_in']} seconds (~1 hour)")
        print()
    
    print("=" * 60)
    print("Tokens saved successfully!")
    print("=" * 60)
    
    return token_data

def upload_to_vps(token_data):
    """Nahraje tokeny na VPS"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    VPS_URL = os.getenv("VPS_URL", "")
    API_KEY = os.getenv("API_KEY", "")
    
    print()
    print("=" * 60)
    print("Upload tokens to VPS?")
    print("=" * 60)
    choice = input("Upload to VPS? (y/N): ").strip().lower()
    
    if choice != 'y':
        print("Skipped. You can upload later with: python upload_notion_tokens.py")
        return
    
    print()
    print(f"Uploading to {VPS_URL}...")
    
    # Pošli data jako query parametry (ne JSON body)
    url = f"{VPS_URL}/api/notion/upload-tokens"
    headers = {
        "X-API-Key": API_KEY
    }
    params = {
        "access_token": token_data['access_token'],
        "refresh_token": token_data.get('refresh_token', '')
    }
    
    try:
        response = requests.post(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print()
        print("✅ SUCCESS!")
        print(f"   {result.get('detail')}")
        print()
        print("Notion MCP is now available on your VPS!")
        
    except requests.exceptions.RequestException as e:
        print()
        print(f"❌ Upload failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        print()
        print("You can try again later with: python upload_notion_tokens.py")

if __name__ == "__main__":
    try:
        tokens = get_access_token()
        if tokens:
            upload_to_vps(tokens)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
