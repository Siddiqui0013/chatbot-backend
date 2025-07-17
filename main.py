from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uuid
from chatbot import HobbyChatbot

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot = HobbyChatbot()

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
        
        result = await chatbot.process_message(
            message=chat_message.message,
            session_id=chat_message.session_id
        )
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            message_type=result["message_type"],
            is_complete=result["is_complete"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
    return {"status": "healthy", "message": "Hobby Discovery Chatbot API is running"}

@app.post("/api/reset-session")
async def reset_session(session_id: str):
    """Reset a conversation session"""
    try:
        if session_id in chatbot.sessions:
            del chatbot.sessions[session_id]
        return {"message": "Session reset successfully", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        if session_id not in chatbot.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = chatbot.sessions[session_id]
        return {
            "session_id": session_id,
            "current_step": session.get("current_step"),
            "interests": session.get("user_interests", []),
            "dislikes": session.get("user_dislikes", []),
            "lifestyle_info": session.get("lifestyle_info", {}),
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