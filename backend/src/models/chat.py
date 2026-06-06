from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: list[Message] = []


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    sources: list[str] = []
