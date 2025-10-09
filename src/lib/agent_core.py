import asyncio
from langchain.schema import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
import dotenv
import os
from typing import Dict, Any

dotenv.load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Globální sessions pro ukládání historie konverzací
sessions: Dict[str, Dict[str, Any]] = {}

# Systémový prompt pro agenta
system_prompt = """
    Jsi inteligentní asistent. Pomáháš uživateli s různými úkoly pomocí nástrojů, které máš k dispozici.
    Udržuj kontext konverzace a odpovídej co nejpřesněji. Používej suchý britský humor, když je to vhodné. S trochu sarkasmu.
    Pokud neznáš odpověď, přiznej to. Rozhodně si nevymýšlej.
    Vždy se snaž být co nejvíce užitečný a nápomocný.
    Nezapomeň, že můžeš volat nástroje, které máš k dispozici.
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
            model="google/gemini-2.5-flash-lite-preview-09-2025",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=OPENROUTER_API_KEY,
            temperature=0,
        )
        config = {
            "mcpServers": {
                "notionApi": {
                    "command": "npx",
                    "args": ["-y", "@notionhq/notion-mcp-server"],
                    "env": {
                        "NOTION_TOKEN": f"ntn_{os.getenv('NOTION_TOKEN_SECRET', '****')}"
                    }
                },
                "ticktick": {
                    "command": "python",
                    "args": ["src/ticktick-mcp/server.py", "run"]
                }
            }
        }
        self.client = MCPClient.from_dict(config)
        self._initialized = True

    async def run_query(self, message: str, session_id: str = "default") -> str:
        """
        Spustí dotaz s podporou session a historie konverzace
        Args:
            message: Uživatelská zpráva
            session_id: ID session pro udržování kontextu
        Returns:
            Odpověď agenta
        """
        await self.initialize()
        # Získat nebo vytvořit session
        if session_id not in sessions:
            sessions[session_id] = {
                "history": []
            }
        session = sessions[session_id]
        # Vytvořit nového agenta pro tento dotaz
        agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=30,
            system_prompt=system_prompt,
            memory_enabled=True
        )
        # Předat historii do agenta (bez aktuální zprávy)
        for msg in session["history"]:
            if msg["role"] == "user":
                agent.add_to_history(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                agent.add_to_history(AIMessage(content=msg["content"]))
        # Spustit agenta s aktuální zprávou
        result = await agent.run(message)
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
        return result

    def get_session_history(self, session_id: str = "default") -> list:
        """
        Získá historii konverzace pro danou session
        Args:
            session_id: ID session
        Returns:
            Seznam zpráv v historii
        """
        if session_id in sessions:
            return sessions[session_id]["history"]
        return []

    def clear_session(self, session_id: str = "default"):
        """
        Vymaže session a její historii
        Args:
            session_id: ID session k vymazání
        """
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
