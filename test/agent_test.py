import asyncio
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
import dotenv
import os

dotenv.load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

async def main():
    # 1. LLM přes OpenRouter - jednotný přístup k různým modelům. Používají OpenAI SDK, takže je to kompatibilní s LangChain
    llm = ChatOpenAI(
        model="google/gemini-2.5-flash-lite-preview-09-2025",
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=OPENROUTER_API_KEY,
        temperature=0,
    )

    # 2. Konfigurace MCP serverů (nástrojů), může jich být mnohem více
    # Používáme oficiální Notion MCP server přes mcp.notion.com
    config = {
        "mcpServers": {
            "Notion": {
            "url": "https://mcp.notion.com/mcp"
            }
        }
    }

    # 3. Inicializace MCP klienta přes knihovnu mcp_use
    client = MCPClient.from_dict(config)

    # Vytvoření MCP agenta s LLM a klientem
    # Tady je vlastně celý kouzelný kousek, který umožňuje LLM volat nástroje přes MCP
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # 4. Spuštění dotazu
    result = await agent.run("Vytvoř novou stránku v notionu s názvem 'Poznatky' a zapiš do ní text: Růže jsou rudé a fialky modré.")
    print("\n=== Výsledek ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
