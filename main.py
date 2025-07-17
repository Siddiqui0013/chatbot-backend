from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uuid
from chatbot import run_graph, get_initial_state, ChatState

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
type SessionStore = dict[str, ChatState]
sessions: SessionStore = {}

class ChatMessage(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_type: str
    is_complete: bool = False

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    try:
        if not chat_message.session_id:
            chat_message.session_id = str(uuid.uuid4())
        session_id = chat_message.session_id
        prev_state = sessions.get(session_id)
        result_state = run_graph(chat_message.message, session_id, prev_state)
        sessions[session_id] = result_state
        return ChatResponse(
            response=result_state["bot_response"],
            session_id=session_id,
            message_type=result_state["message_type"],
            is_complete=result_state["is_complete"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Hobby Discovery Chatbot API is running"}

@app.post("/api/reset-session")
async def reset_session(session_id: str):
    try:
        if session_id in sessions:
            del sessions[session_id]
        return {"message": "Session reset successfully", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        session = sessions[session_id]
        return {
            "session_id": session_id,
            "current_step": session.get("step"),
            "interests": session.get("interests", []),
            "dislikes": session.get("dislikes", []),
            "lifestyle_info": session.get("lifestyle", {}),
            "conversation_length": len(session.get("conversation_history", [])),
            "conversation_history": session.get("conversation_history", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)