"""
Notion OAuth client - stejný pattern jako TickTickClient
Automaticky obnovuje access token pomocí refresh tokenu.
"""

import json
import requests
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Správná cesta: src/lib/tokens/notion_tokens.json (ne src/notion-mcp/lib/tokens/)
TOKEN_PATH = Path(__file__).parent.parent / "lib" / "tokens" / "notion_tokens.json"

class NotionClient:
    """
    Klient pro Notion API s OAuth2 autentizací.
    Načte tokeny z JSON, automaticky obnovuje když expirují.
    """
    def __init__(self):
        self._load_tokens()
        # Notion MCP OAuth endpoint
        self.token_url = "https://mcp.notion.com/token"
        # Veřejný MCP client
        self.client_id = "YvWLaE2nKO861jM1"
        self.client_secret = None  # Public client nemá secret

    def _load_tokens(self):
        """Načti tokeny z JSON souboru"""
        if not TOKEN_PATH.exists():
            logger.warning(
                f"⚠️  Soubor s Notion tokeny neexistuje: {TOKEN_PATH}\n"
                f"   Notion MCP nebude dostupný. Pro aktivaci navštiv: /api/notion/auth"
            )
            self.access_token = None
            self.refresh_token = None
            return
        
        try:
            with open(TOKEN_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            
            if not self.access_token:
                logger.warning("⚠️  Chybí access_token v notion_tokens.json")
                return
            
            logger.info(f"✓ Notion tokeny načteny z {TOKEN_PATH}")
        except Exception as e:
            logger.error(f"Chyba při načítání Notion tokenů: {e}")
            self.access_token = None
            self.refresh_token = None

    def _refresh_access_token(self) -> bool:
        """
        Obnov access token pomocí refresh tokenu.
        Stejný princip jako TickTick.
        """
        if not self.refresh_token:
            logger.warning("Chybí refresh token, nelze obnovit.")
            return False
        
        logger.info("Obnovuji Notion access token...")
        
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        # Pokud máme client_secret, použijeme Basic Auth
        if self.client_secret:
            import base64
            basic_auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers["Authorization"] = f"Basic {basic_auth}"
        else:
            # Public client - client_id v body
            token_data["client_id"] = self.client_id
        
        try:
            response = requests.post(self.token_url, data=token_data, headers=headers)
            response.raise_for_status()
            
            tokens = response.json()
            self.access_token = tokens.get('access_token')
            
            # Pokud server vrátí nový refresh token, použij ho
            if 'refresh_token' in tokens:
                self.refresh_token = tokens.get('refresh_token')
            
            # Ulož nové tokeny zpět do JSON souboru
            with open(TOKEN_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "token_type": tokens.get("token_type", "bearer"),
                    "expires_in": tokens.get("expires_in", 3600),
                    "scope": tokens.get("scope", "")
                }, f, ensure_ascii=False, indent=2)
            
            logger.info("✓ Notion access token úspěšně obnoven")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Chyba při obnovení Notion tokenu: {e}")
            return False

    def get_access_token(self) -> str:
        """
        Vrátí validní access token.
        Při 401 chybě se pokusí token obnovit.
        """
        if not self.access_token:
            logger.warning("⚠️  Notion tokeny nejsou k dispozici. Navštiv /api/notion/auth pro autorizaci.")
            return ""
        return self.access_token

    def handle_401(self) -> bool:
        """
        Zavolej když dostaneš 401 chybu.
        Pokusí se obnovit token.
        """
        return self._refresh_access_token()


# Singleton pro jednoduchost
_client: Optional[NotionClient] = None

def get_notion_client() -> NotionClient:
    """Vrátí singleton instanci NotionClient"""
    global _client
    if _client is None:
        _client = NotionClient()
    return _client

def get_notion_access_token() -> str:
    """Helper funkce pro získání access tokenu"""
    return get_notion_client().get_access_token()
