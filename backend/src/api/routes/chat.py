from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from backend.src.models.chat import ChatRequest, ChatResponse
from backend.src.services.chat_service import ChatService
from backend.src.services.config_service import ConfigService
from backend.src.core.config import settings

router = APIRouter(prefix="/api/chatbots/{chatbot_id}", tags=["chat"])


def get_chat_service() -> ChatService:
    return ChatService(data_dir=settings.data_dir)


@router.post("/chat", response_model=ChatResponse)
def chat(chatbot_id: str, request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    try:
        return service.chat(chatbot_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions")
def get_sessions(chatbot_id: str, service: ChatService = Depends(get_chat_service)):
    return service.get_sessions(chatbot_id)


@router.get("/sessions/{session_id}/messages")
def get_messages(chatbot_id: str, session_id: str, service: ChatService = Depends(get_chat_service)):
    return service.get_messages(session_id)


@router.get("/contacts")
def get_contacts(chatbot_id: str):
    from backend.src.db.database import get_connection
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM contact_captures WHERE chatbot_id = ? ORDER BY captured_at DESC",
            (chatbot_id,)
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/unknown-questions")
def get_unknown_questions(chatbot_id: str):
    from backend.src.db.database import get_connection
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM unknown_questions WHERE chatbot_id = ? ORDER BY asked_at DESC",
            (chatbot_id,)
        ).fetchall()
    return [dict(r) for r in rows]
