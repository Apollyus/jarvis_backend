"""
Modul pro autentizaci pomocí API klíče
Poskytuje jednoduchou, bezstavovou autentizaci API klíčem pro ochranu endpointů.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional, Dict
from pydantic import BaseModel
import os
import secrets
import hashlib
from dotenv import load_dotenv

# Načíst proměnné prostředí
load_dotenv()

# Konfigurace hlavičky API klíče
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Načíst platné API klíče z prostředí
VALID_API_KEYS = set()

# Načíst API klíč z proměnné prostředí
api_key = os.getenv("API_KEY")
if api_key:
    VALID_API_KEYS.add(api_key)

# Podpora více API klíčů (oddělených čárkami)
api_keys_str = os.getenv("API_KEYS")
if api_keys_str:
    for key in api_keys_str.split(","):
        key = key.strip()
        if key:
            VALID_API_KEYS.add(key)


# Uživatelské účty (login: heslo_hash)
# V produkci použijte databázi!
USERS: Dict[str, str] = {}

# Načíst uživatele z proměnných prostředí
# Formát: USERNAME=login PASSWORD=heslo
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
if username and password:
    # Hash hesla pomocí SHA-256
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    USERS[username] = password_hash


class LoginRequest(BaseModel):
    """Model požadavku pro přihlášení"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Model odpovědi po úspěšném přihlášení"""
    api_key: str
    message: str


async def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Závislostní funkce pro ověření API klíče z hlaviček požadavku.
    
    Args:
        api_key: API klíč z hlavičky X-API-Key
        
    Returns:
        str: Ověřený API klíč
        
    Raises:
        HTTPException: Pokud API klíč chybí nebo je neplatný
    """
    if not VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chyba konfigurace serveru: Žádné API klíče nejsou nakonfigurovány. Nastavte API_KEY nebo API_KEYS v proměnných prostředí."
        )
    
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chybí API klíč. Poskytněte hlavičku X-API-Key.",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Neplatný API klíč",
        )
    
    return api_key


def get_api_key_count() -> int:
    """Vrátí počet nakonfigurovaných API klíčů."""
    return len(VALID_API_KEYS)


def is_auth_configured() -> bool:
    """Zkontroluje, zda je autentizace správně nakonfigurována."""
    return len(VALID_API_KEYS) > 0


def verify_user_credentials(username: str, password: str) -> bool:
    """
    Ověří uživatelské přihlašovací údaje.
    
    Args:
        username: Uživatelské jméno
        password: Heslo v plain textu
        
    Returns:
        bool: True pokud jsou údaje správné, jinak False
    """
    if username not in USERS:
        return False
    
    # Hash zadaného hesla a porovnání s uloženým hashem
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return USERS[username] == password_hash


def generate_api_key() -> str:
    """
    Vygeneruje nový bezpečný API klíč.
    
    Returns:
        str: Nově vygenerovaný API klíč
    """
    return secrets.token_urlsafe(32)


def add_api_key(api_key: str) -> None:
    """
    Přidá nový API klíč do sady platných klíčů.
    
    Args:
        api_key: API klíč k přidání
    """
    VALID_API_KEYS.add(api_key)


def get_user_count() -> int:
    """Vrátí počet registrovaných uživatelů."""
    return len(USERS)