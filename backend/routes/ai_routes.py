# backend/routes/ai_routes.py
# Import your AI classes
import sys
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from utils.conversational_recommender import ConversationalRestaurantBot
from utils.restaurant_recommender import RestaurantRecommender

BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)



ai_router = APIRouter()

# Initialize recommender (singleton)
recommender = None
# Store chatbot sessions (in production, use Redis or similar)
chatbot_sessions = {}


def get_recommender():
    """Lazy initialization of RestaurantRecommender"""
    global recommender
    if recommender is not None:
        return recommender
    try:
        recommender = RestaurantRecommender()
        return recommender
    except Exception as e:
        print(f"Error initializing RestaurantRecommender: {e}")
        return None


# ============ REQUEST/RESPONSE MODELS ============


class RecommendationRequest(BaseModel):
    query: str


class RecommendationResponse(BaseModel):
    recommendation: str
    success: bool = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool = True


class ChatResetRequest(BaseModel):
    session_id: str


# ============ ENDPOINTS ============


@ai_router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    One-shot restaurant recommendation using AI

    Example request:
    {
        "query": "I want Italian food downtown with vegetarian options"
    }
    """
    try:
        rec = get_recommender()
        if rec is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI recommender is not configured. Check your GROQ_API_KEY or OPENAI_API_KEY.",
            )

        recommendation = rec.get_recommendations(request.query)
        return RecommendationResponse(recommendation=recommendation, success=True)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get recommendations: {str(e)}"
        )


@ai_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Conversational chatbot with memory

    Maintains conversation history per session.

    Example request:
    {
        "message": "I'm looking for dinner",
        "session_id": "optional-uuid-here"
    }

    The session_id is optional - if not provided, a new session will be created.
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())

        if session_id not in chatbot_sessions:
            try:
                chatbot_sessions[session_id] = ConversationalRestaurantBot()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to initialize chatbot: {str(e)}. Check your GROQ_API_KEY.",
                )

        bot = chatbot_sessions[session_id]
        response = bot.chat(request.message)

        return ChatResponse(response=response, session_id=session_id, success=True)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@ai_router.post("/chat/reset")
async def reset_chat(request: ChatResetRequest):
    """
    Reset a chat session's conversation history

    Example request:
    {
        "session_id": "your-session-uuid"
    }
    """
    try:
        session_id = request.session_id

        if session_id in chatbot_sessions:
            chatbot_sessions[session_id].reset()
            return {
                "success": True,
                "message": "Chat session reset successfully",
                "session_id": session_id,
            }

        raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error resetting chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset chat: {str(e)}")


@ai_router.delete("/chat/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session completely

    This removes the session from memory. The user will need to start a new session.
    """
    try:
        if session_id in chatbot_sessions:
            del chatbot_sessions[session_id]
            return {"success": True, "message": "Session deleted successfully"}

        raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete session: {str(e)}"
        )


@ai_router.get("/chat/sessions")
async def list_sessions():
    """
    List all active chat sessions (for debugging/admin)
    """
    return {
        "success": True,
        "active_sessions": list(chatbot_sessions.keys()),
        "count": len(chatbot_sessions),
    }
