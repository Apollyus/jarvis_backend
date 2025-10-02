from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import sys
from pathlib import Path

# Přidání src/lib do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from agent_core import get_agent_service, run_agent_query

app = FastAPI(title="MCP Agent API")

# CORS pro Next.js (běží defaultně na localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

# REST endpoint (jednodušší varianta)
@app.post("/api/chat")
async def chat(request: ChatMessage):
    result = await run_agent_query(request.message)
    return {"response": result, "session_id": request.session_id}

# WebSocket endpoint (pro streaming)
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
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

# Server-Sent Events varianta (alternativa k WebSocket)
@app.get("/api/chat/stream")
async def chat_stream(message: str):
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
    return {"message": "MCP Agent API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
