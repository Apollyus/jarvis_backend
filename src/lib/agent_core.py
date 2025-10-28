import asyncio
import logging
from langchain.schema import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
import dotenv
import os
import sys
from pathlib import Path
from typing import Dict, Any
from session_manager import get_session_manager

logger = logging.getLogger(__name__)

# Přidej src adresář do path (pro import notion_client)
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "notion-mcp"))
from notion_client import get_notion_access_token

dotenv.load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LINKUP_API_KEY = os.getenv("LINKUP_API_KEY")
N8N_API_URL = os.getenv("N8N_API_URL")
N8N_API_KEY = os.getenv("N8N_API_KEY")

if not OPENROUTER_API_KEY:
    logger.error("❌ OPENROUTER_API_KEY není nastaven v .env souboru")
    raise ValueError("OPENROUTER_API_KEY není nastaven v .env souboru")
if not LINKUP_API_KEY:
    logger.error("❌ LINKUP_API_KEY není nastaven v .env souboru")
    raise ValueError("LINKUP_API_KEY není nastaven v .env souboru")
if not N8N_API_URL:
    logger.error("❌ N8N_API_URL není nastaven v .env souboru")
    raise ValueError("N8N_API_URL není nastaven v .env souboru")
if not N8N_API_KEY:
    logger.error("❌ N8N_API_KEY není nastaven v .env souboru")
    raise ValueError("N8N_API_KEY není nastaven v .env souboru")

# Globální sessions pro ukládání historie konverzací (fallback když Redis není dostupný)
sessions: Dict[str, Dict[str, Any]] = {}

# Session manager (Redis)
session_manager = get_session_manager()

# Systémový prompt pro agenta
system_prompt = """
    Jsi inteligentní asistent s názvem JARVIS. Pomáháš uživateli s různými úkoly pomocí nástrojů, které máš k dispozici.
    Udržuj kontext konverzace a odpovídej co nejpřesněji. Používej suchý britský humor, když je to vhodné. S trochu sarkasmu.
    Pokud neznáš odpověď, přiznej to. Rozhodně si nevymýšlej.
    Vždy se snaž být co nejvíce užitečný a nápomocný.
    Nezapomeň, že můžeš volat nástroje, které máš k dispozici.

    Vždy se snaž spojovat si věci dohromady. Snaž se jednat samostatně a kreativně.
    Napřáklad při použití nástrojů si sám vytvoř plán, jak dosáhnout cíle uživatele, tzn. zjistit si potřebné id projektů pomocí dostupných nástrojů a poradit si s uživatelovo požadavkem.
    Na tomhle velice záleží a je to kritický bod fungování agenta.

    Uživatel ti píše pouze česky, nebo anglicky, takže odpovídej ve stejném jazyce, ve kterém ti píše.
    Může se stát, že uživatel přepne jentak jazyk v průběhu konverzace, takže buď na to připraven.

    Nevymýšlej si výsledky použití nástrojů. Ujisti se, že výsledek co reportuješ uživateli je přesně to, co nástroj vrátil.
    Je to vysoce kritické pro správné fungování agenta - tebe.

    Pokud uživatel požaduje něco co není v tvé kompetenci s tvými nástroji, zkus použít vyhledavání na internetu a zkus problém vyřešit.
    Máš k dispozici MCP na n8n, pokud nemáš nástroj na uživatelovo přání, vytvoř si ten nástroj na n8n. Pokud tak učiníš, popiš uživateli jak jsi to udělal a jak může nástroj používat v budoucnu.

    Dbej na to, aby tvé odpovědi byly stručné a výstižné. Nepiš zbytečně dlouhé odpovědi.

    Formátuj odpovědi pomocí markdownu. Mezi odstavci používej prázdné 2 řádky.
    
    KRITICKÉ PRAVIDLO PRO N8N NÁSTROJE:
    Když používáš n8n_update_full_workflow nebo n8n_create_workflow, NIKDY neposílej 'nodes' nebo 'connections' jako JSON string.
    Vždy je pošli jako přímý objekt/pole. Například:
    ❌ ŠPATNĚ: {"nodes": "[{\"id\": \"1\"...}]"} - tohle je string!
    ✅ SPRÁVNĚ: {"nodes": [{"id": "1"...}]} - tohle je pole objektů!
    Totéž platí pro connections, settings a všechny ostatní složité struktury.
    """

class AgentService:
    """Service pro správu MCP agenta a konverzací"""
    def __init__(self):
        self.llm = None
        self.client = None
        self._initialized = False

    async def initialize(self):
        """Inicializace LLM a MCP klienta"""
        if self._initialized:
            return
        self.llm = ChatOpenAI(
            model="anthropic/claude-haiku-4.5",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=OPENROUTER_API_KEY,
            temperature=0.2,
        )
        # Získat Notion access token
        notion_token = get_notion_access_token()
        
        logger.info("🚀 Začínám inicializaci MCP serverů...")
        logger.info(f"📍 N8N_API_URL: {N8N_API_URL}")
        logger.info(f"📍 N8N_API_KEY: {'*' * len(N8N_API_KEY) if N8N_API_KEY else 'None'}")
        
        # Zjisti, jestli jsou jednotlivé MCP servery povolené
        enable_whatsapp = os.getenv("ENABLE_WHATSAPP", "false").lower() == "true"
        enable_n8n = os.getenv("ENABLE_N8N", "true").lower() == "true"
        
        config = {
            "mcpServers": {
                "TickTick": {
                    "command": "python",
                    "args": ["src/ticktick-mcp/server.py", "run"]
                },
                "linkup": {
                    "command": "npx",
                    "args": ["-y", "linkup-mcp-server", "apiKey=" + LINKUP_API_KEY]
                },
                "fetch": {
                    "command": "npx",
                    "args": [
                        "mcp-fetch-server"
                    ], 
                    "env": {
                        "max_length": "50000"
                    }
                }
            }
        }
        
        # Přidat WhatsApp pouze pokud je povolen
        if enable_whatsapp:
            logger.info("✅ Přidávám WhatsApp MCP server")
            config["mcpServers"]["WhatsApp"] = {
                "command": "uv",
                "args": [
                    "--directory",
                    "/app/whatsapp-mcp/whatsapp-mcp-server",
                    "run",
                    "main.py"
                ]
            }
        else:
            logger.info("⏭️  WhatsApp MCP server je zakázán (ENABLE_WHATSAPP=false)")
        
        # Přidat N8N pouze pokud je povolen
        if enable_n8n:
            logger.info("✅ Přidávám N8N MCP server")
            config["mcpServers"]["n8n"] = {
                "command": "n8n-mcp",
                "args": [],
                "env": {
                    "MCP_MODE": "stdio",
                    "LOG_LEVEL": "error",
                    "DISABLE_CONSOLE_OUTPUT": "true",
                    "N8N_API_URL": f"{N8N_API_URL}",
                    "N8N_API_KEY": f"{N8N_API_KEY}"
                }
            }
        else:
            logger.info("⏭️  N8N MCP server je zakázán (ENABLE_N8N=false)")
        
        # Přidat Notion pouze pokud máme validní token
        # Používáme headers místo auth, abychom se vyhnuli automatickému OAuth flow
        if notion_token:
            config["mcpServers"]["Notion"] = {
                "url": "https://mcp.notion.com/mcp",
                "headers": {
                    "Authorization": f"Bearer {notion_token}"
                }
            }
        else:
            logger.warning("⚠️  Notion není nakonfigurován - chybí access token")
        
        logger.info(f"🔧 Inicializuji MCP klienta s těmito servery: {list(config['mcpServers'].keys())}")
        
        try:
            self.client = MCPClient.from_dict(config)
        except Exception as e:
            logger.error(f"❌ Chyba při vytváření MCP klienta: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        logger.info("✅ MCP klient úspěšně vytvořen")
        
        # Počkat na inicializaci sessions (dělá se asynchronně při prvním použití agenta)
        logger.info("⏳ Čekám na vytvoření MCP sessions...")
        await asyncio.sleep(1)
        
        # Zkusit získat informace o aktivních sessions a nástrojích
        try:
            active_sessions = self.client.get_all_active_sessions()
            logger.info(f"📡 Aktivní sessions: {list(active_sessions.keys())}")
            
            # Pro každou session vypsat dostupné nástroje
            for server_name, session in active_sessions.items():
                try:
                    if session.is_connected():
                        tools = await session.list_tools()
                        tool_names = [tool.name for tool in tools]
                        logger.info(f"🔧 Server '{server_name}': {len(tools)} nástrojů - {tool_names}")
                    else:
                        logger.warning(f"⚠️  Server '{server_name}': není připojen")
                except Exception as e:
                    logger.warning(f"⚠️  Server '{server_name}': chyba při získávání nástrojů - {e}")
        except Exception as e:
            logger.warning(f"⚠️  Nelze získat informace o sessions: {e}")
        
        self._initialized = True
    
    async def reinitialize_client(self):
        """Reinicializuje MCP klienta s novými tokeny"""
        self._initialized = False
        # Zavřít staré připojení pokud existuje
        if self.client:
            try:
                # Pokud má close metodu, zavolej ji
                if hasattr(self.client, 'close'):
                    await self.client.close()
            except Exception as e:
                logger.warning(f"Chyba při zavírání starého klienta: {e}")
        
        self.client = None
        await self.initialize()

    async def run_query(self, message: str, session_id: str = "default", retry_on_auth_error: bool = True) -> str:
        """
        Spustí dotaz s podporou session a historie konverzace
        Args:
            message: Uživatelská zpráva
            session_id: ID session pro udržování kontextu
            retry_on_auth_error: Pokud True, zkusí reinicializovat při auth chybě
        Returns:
            Odpověď agenta
        """
        await self.initialize()
        
        # Získat nebo vytvořit session
        # Nejdřív zkus Redis, pak fallback na memory
        session = session_manager.load_session(session_id)
        
        if session is None:
            # Zkus memory fallback
            if session_id in sessions:
                session = sessions[session_id]
                logger.info(f"📝 Načtena session z paměti: {session_id}")
            else:
                # Nová session
                session = {"history": []}
                logger.info(f"🆕 Vytvořena nová session: {session_id}")
        else:
            logger.info(f"💾 Načtena session z Redis: {session_id}")
        
        # Vytvořit nového agenta pro tento dotaz
        logger.info(f"🤖 Vytvářím MCPAgent pro session: {session_id}")
        agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=30,
            system_prompt=system_prompt,
            memory_enabled=True
        )
        
        # Logovat dostupné nástroje po vytvoření agenta
        # (nástroje se vytvoří až při inicializaci, která proběhne při run())
        logger.info(f"📋 Agent vytvořen pro session {session_id}")
        
        # Předat historii do agenta (bez aktuální zprávy)
        for msg in session["history"]:
            if msg["role"] == "user":
                agent.add_to_history(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                agent.add_to_history(AIMessage(content=msg["content"]))
        
        # Spustit agenta s aktuální zprávou - pokusit se obnovit při auth chybě
        try:
            result = await agent.run(message)
            
            # Po prvním běhu logovat dostupné nástroje
            if hasattr(agent, '_tools') and agent._tools:
                tool_names = [tool.name for tool in agent._tools]
                logger.info(f"🔧 Agent má k dispozici {len(tool_names)} nástrojů: {tool_names}")
                
                # Specificky zkontroluj n8n nástroje
                n8n_tools = [name for name in tool_names if 'n8n' in name.lower()]
                if n8n_tools:
                    logger.info(f"✅ N8N nástroje nalezeny: {n8n_tools}")
                else:
                    logger.warning(f"⚠️  Žádné N8N nástroje mezi dostupnými nástroji!")
            
        except Exception as e:
            error_msg = str(e).lower()
            # Pokud je to auth error (401, unauthorized, atd.), zkus reinicializovat
            if retry_on_auth_error and any(keyword in error_msg for keyword in ['401', 'unauthorized', 'auth', 'authentication']):
                logger.warning(f"⚠️  Detekována auth chyba, pokouším se reinicializovat s novými tokeny...")
                await self.reinitialize_client()
                # Zkus dotaz znovu (bez dalšího retry)
                return await self.run_query(message, session_id, retry_on_auth_error=False)
            else:
                # Jiná chyba nebo už jsme zkusili retry - vyhoď výjimku
                raise
        
        # Přidat uživatelskou zprávu do historie až po odpovědi
        session["history"].append({
            "role": "user",
            "content": message
        })
        # Přidat odpověď agenta do historie
        session["history"].append({
            "role": "assistant",
            "content": result
        })
        
        # Uložit do Redis (s fallbackem do memory)
        if not session_manager.save_session(session_id, session["history"]):
            # Redis není dostupný, ulož do memory
            sessions[session_id] = session
            logger.warning(f"⚠️  Session {session_id} uložena pouze do paměti (Redis nedostupný)")
        else:
            logger.info(f"💾 Session {session_id} uložena do Redis")
        
        return result

    def get_session_history(self, session_id: str = "default") -> list:
        """
        Získá historii konverzace pro danou session
        Args:
            session_id: ID session
        Returns:
            Seznam zpráv v historii
        """
        # Zkus Redis
        session = session_manager.load_session(session_id)
        if session:
            return session["history"]
        
        # Fallback na memory
        if session_id in sessions:
            return sessions[session_id]["history"]
        return []

    def clear_session(self, session_id: str = "default"):
        """
        Vymaže session a její historii
        Args:
            session_id: ID session k vymazání
        """
        # Smaž z Redis
        session_manager.delete_session(session_id)
        
        # Smaž z memory
        if session_id in sessions:
            del sessions[session_id]

# Singleton instance agenta
_agent_service_instance = None

def get_agent_service() -> AgentService:
    """
    Získá singleton instanci AgentService
    Returns:
        Instance AgentService
    """
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance

async def run_agent_query(message: str, session_id: str = "default") -> str:
    """
    Helper funkce pro rychlé spuštění dotazu
    Args:
        message: Uživatelská zpráva
        session_id: ID session
    Returns:
        Odpověď agenta
    """
    service = get_agent_service()
    return await service.run_query(message, session_id)

# Původní funkce pro zpětnou kompatibilitu
async def use_agent():
    """Původní demo funkce - zachováno pro zpětnou kompatibilitu"""
    result = await run_agent_query(
        "Vytvoř novou stránku v notionu s názvem 'Poznatky' a zapiš do ní text: Růže jsou rudé a fialky modré."
    )
    print("\n=== Výsledek ===")
    print(result)
