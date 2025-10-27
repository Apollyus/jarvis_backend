"""
Session Manager pro JARVIS
Ukládá konverzace do Redis s automatickým TTL a cleanup
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis

logger = logging.getLogger(__name__)

class SessionManager:
    """Správa sessions v Redis"""
    
    def __init__(self, redis_url: Optional[str] = None, ttl_days: int = 7):
        """
        Inicializace SessionManageru
        
        Args:
            redis_url: URL pro připojení k Redis (default: localhost)
            ttl_days: Kolik dní má session přežít bez aktivity (default: 7)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.ttl_seconds = ttl_days * 24 * 60 * 60  # Převod na sekundy
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
        
    def connect(self):
        """Připojení k Redis"""
        if self._connected:
            return
            
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,  # Automaticky dekóduj do stringu
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test připojení
            self.redis_client.ping()
            self._connected = True
            logger.info(f"✅ Připojeno k Redis: {self.redis_url}")
        except redis.ConnectionError as e:
            logger.error(f"❌ Nepodařilo se připojit k Redis: {e}")
            logger.warning("⚠️  Sessions budou pouze v paměti (zmizí po restartu)")
            self.redis_client = None
            self._connected = False
        except Exception as e:
            logger.error(f"❌ Chyba při připojování k Redis: {e}")
            self.redis_client = None
            self._connected = False
    
    def _get_key(self, session_id: str) -> str:
        """Vytvoří Redis klíč pro session"""
        return f"jarvis:session:{session_id}"
    
    def save_session(self, session_id: str, history: List[Dict[str, str]]) -> bool:
        """
        Uloží session do Redis
        
        Args:
            session_id: ID session
            history: Historie zpráv
            
        Returns:
            True pokud se podařilo uložit, False jinak
        """
        if not self._connected or not self.redis_client:
            return False
            
        try:
            key = self._get_key(session_id)
            data = {
                "history": history,
                "updated_at": datetime.now().isoformat(),
                "session_id": session_id
            }
            
            # Uložit jako JSON s TTL
            self.redis_client.setex(
                key,
                self.ttl_seconds,
                json.dumps(data, ensure_ascii=False)
            )
            return True
        except Exception as e:
            logger.error(f"❌ Chyba při ukládání session {session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Načte session z Redis
        
        Args:
            session_id: ID session
            
        Returns:
            Dictionary s "history" nebo None pokud neexistuje
        """
        if not self._connected or not self.redis_client:
            return None
            
        try:
            key = self._get_key(session_id)
            data = self.redis_client.get(key)
            
            if data is None:
                return None
                
            session_data = json.loads(data)
            
            # Prodloužit TTL (session je aktivní)
            self.redis_client.expire(key, self.ttl_seconds)
            
            return {"history": session_data.get("history", [])}
        except Exception as e:
            logger.error(f"❌ Chyba při načítání session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Smaže session z Redis
        
        Args:
            session_id: ID session
            
        Returns:
            True pokud se podařilo smazat
        """
        if not self._connected or not self.redis_client:
            return False
            
        try:
            key = self._get_key(session_id)
            self.redis_client.delete(key)
            logger.info(f"🗑️  Session {session_id} smazána")
            return True
        except Exception as e:
            logger.error(f"❌ Chyba při mazání session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """
        Vrátí seznam všech aktivních session IDs
        
        Returns:
            Seznam session IDs
        """
        if not self._connected or not self.redis_client:
            return []
            
        try:
            pattern = self._get_key("*")
            keys = self.redis_client.keys(pattern)
            # Extrahovat session_id z klíčů
            session_ids = [key.replace("jarvis:session:", "") for key in keys]
            return session_ids
        except Exception as e:
            logger.error(f"❌ Chyba při listování sessions: {e}")
            return []
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Získá informace o session (bez celé historie)
        
        Returns:
            Dictionary s metadata nebo None
        """
        if not self._connected or not self.redis_client:
            return None
            
        try:
            key = self._get_key(session_id)
            data = self.redis_client.get(key)
            
            if data is None:
                return None
                
            session_data = json.loads(data)
            ttl = self.redis_client.ttl(key)
            
            return {
                "session_id": session_id,
                "message_count": len(session_data.get("history", [])),
                "updated_at": session_data.get("updated_at"),
                "expires_in_seconds": ttl if ttl > 0 else None
            }
        except Exception as e:
            logger.error(f"❌ Chyba při získávání info o session {session_id}: {e}")
            return None
    
    def cleanup_expired(self) -> int:
        """
        Vymaže expirované sessions (Redis to dělá automaticky, toto je pro manuální cleanup)
        
        Returns:
            Počet smazaných sessions
        """
        # Redis má automatický TTL, takže tento cleanup není nutný
        # Ponecháno pro kompatibilitu
        logger.info("ℹ️  Redis automaticky maže expirované sessions (TTL)")
        return 0

# Singleton instance
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Získá singleton instanci SessionManageru"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
        _session_manager.connect()
    return _session_manager
