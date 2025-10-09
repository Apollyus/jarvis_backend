from urllib.parse import urlencode
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
import time
import requests
from dotenv import load_dotenv
import sys
from pathlib import Path
import base64

# Přidání src/lib do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "lib"))

# Načtení TickTick OAuth konfigurace
load_dotenv()
TICKTICK_CLIENT_ID = os.getenv("TICKTICK_CLIENT_ID")
TICKTICK_CLIENT_SECRET = os.getenv("TICKTICK_CLIENT_SECRET")
TICKTICK_CALLBACK_URL = os.getenv("TICKTICK_CALLBACK_URL")
TICKTICK_TOKEN_PATH = str(Path(__file__).parent / "lib" / "tokens" / "ticktick_tokens.json")

from agent_core import get_agent_service, run_agent_query
from auth import (
    verify_api_key,
    is_auth_configured,
    LoginRequest,
    LoginResponse,
    verify_user_credentials,
    generate_api_key,
    add_api_key,
    get_user_count
)

app = FastAPI(title="MCP Agent API")

# CORS pro Next.js (běží defaultně na localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "https://agent.vojtechfal.cz", "https://ai.vojtechfal.cz"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

# TickTick OAuth 2.0 - zahájení autentizace
@app.get("/api/ticktick/auth")
async def ticktick_auth(state: str = "default"):
    """
    Přesměruje uživatele na TickTick OAuth 2.0 autorizační stránku
    """
    if not TICKTICK_CLIENT_ID or not TICKTICK_CALLBACK_URL:
        raise HTTPException(status_code=500, detail="TickTick OAuth není nakonfigurován")
    params = {
        "scope": "tasks:read tasks:write",
        "client_id": TICKTICK_CLIENT_ID,
        "state": state,
        "redirect_uri": TICKTICK_CALLBACK_URL,
        "response_type": "code"
    }
    oauth_url = f"https://ticktick.com/oauth/authorize?{urlencode(params)}"
    return {"auth_url": oauth_url}

# TickTick OAuth 2.0 - callback
@app.get("/api/ticktick/callback")
async def ticktick_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Chybí autorizační kód")
    token_url = "https://ticktick.com/oauth/token"
    scope = "tasks:read tasks:write"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "scope": scope,
        "redirect_uri": TICKTICK_CALLBACK_URL
    }
    # Basic Auth header
    basic_auth = base64.b64encode(f"{TICKTICK_CLIENT_ID}:{TICKTICK_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    resp = requests.post(token_url, data=data, headers=headers)
    if resp.status_code != 200:
        return {
            "detail": f"Chyba při získávání tokenu: {resp.text}",
            "status_code": resp.status_code,
            "response": resp.text
        }
    tokens = resp.json()
    tokens["obtained_at"] = int(time.time())
    Path(TICKTICK_TOKEN_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(TICKTICK_TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)
    return {"detail": "Tokeny úspěšně získány a uloženy.", "tokens": tokens}


# Endpoint pro přihlášení - VEŘEJNÝ
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Endpoint pro přihlášení uživatele.
    Ověří uživatelské jméno a heslo a vrátí API klíč.
    
    Args:
        request: LoginRequest s username a password
        
    Returns:
        LoginResponse s api_key a message
        
    Raises:
        HTTPException: 401 pokud jsou přihlašovací údaje neplatné
        HTTPException: 503 pokud nejsou nakonfigurováni žádní uživatelé
    """
    # Zkontrolovat, zda jsou nakonfigurováni uživatelé
    if get_user_count() == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nejsou nakonfigurováni žádní uživatelé. Nastavte USERNAME a PASSWORD v .env souboru."
        )
    
    # Ověřit přihlašovací údaje
    if not verify_user_credentials(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatné uživatelské jméno nebo heslo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vygenerovat nový API klíč
    new_api_key = generate_api_key()
    
    # Přidat klíč do sady platných klíčů
    add_api_key(new_api_key)
    
    return LoginResponse(
        api_key=new_api_key,
        message=f"Přihlášení úspěšné. Použijte tento API klíč v hlavičce X-API-Key pro přístup k chráněným endpointům."
    )


# REST endpoint (jednodušší varianta) - CHRÁNĚNÝ
@app.post("/api/chat")
async def chat(request: ChatMessage, api_key: str = Depends(verify_api_key)):
    result = await run_agent_query(request.message, request.session_id)
    return {"response": result, "session_id": request.session_id}

# WebSocket endpoint (pro streaming) - CHRÁNĚNÝ
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    # Ověřit API klíč z WebSocket připojení
    try:
        # Získat API klíč z parametrů dotazu nebo hlaviček
        api_key = websocket.query_params.get("api_key") or websocket.headers.get("x-api-key")
        
        if not is_auth_configured():
            await websocket.send_json({
                "type": "error",
                "message": "Chyba konfigurace serveru: Žádné API klíče nejsou nakonfigurovány"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        if not api_key:
            await websocket.send_json({
                "type": "error",
                "message": "Vyžadována autentizace: Chybí API klíč. Poskytněte přes 'api_key' parametr dotazu nebo 'X-API-Key' hlavičku"
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Ověřit API klíč
        await verify_api_key(api_key)
        
    except HTTPException as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Autentizace selhala: {e.detail}"
        })
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Chyba autentizace: {str(e)}"
        })
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    agent_service = get_agent_service()
    
    try:
        while True:
            # Přijmout zprávu od klienta
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            
            # Poslat potvrzení
            await websocket.send_json({
                "type": "status",
                "message": "Processing..."
            })
            
            # Spustit agenta
            try:
                result = await agent_service.run_query(user_message)
                
                # Poslat výsledek
                await websocket.send_json({
                    "type": "response",
                    "message": result,
                    "done": True
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

# Server-Sent Events varianta (alternativa k WebSocket) - PROTECTED
@app.get("/api/chat/stream")
async def chat_stream(message: str, api_key: str = Depends(verify_api_key)):
    from fastapi.responses import StreamingResponse
    
    async def event_generator():
        agent_service = get_agent_service()
        
        # Odeslat status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Processing...'})}\n\n"
        
        try:
            # Spustit agenta
            result = await agent_service.run_query(message)
            
            # Odeslat výsledek
            yield f"data: {json.dumps({'type': 'response', 'message': result, 'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/")
async def root():
    return {
        "message": "MCP Agent API běží",
        "version": "1.0.0",
        "authentication": "API klíč vyžadován pro chráněné endpointy"
    }

@app.get("/health")
async def health():
    auth_status = "nakonfigurováno" if is_auth_configured() else "není_nakonfigurováno"
    return {
        "status": "healthy",
        "authentication": auth_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
