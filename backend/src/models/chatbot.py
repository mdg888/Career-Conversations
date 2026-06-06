from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatbotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    tone: str = "professional"
    greeting: Optional[str] = None
    fallback_message: Optional[str] = "I don't have information about that."
    model: str = "gpt-4o-mini"


class ChatbotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    tone: Optional[str] = None
    greeting: Optional[str] = None
    fallback_message: Optional[str] = None
    model: Optional[str] = None


class ChatbotResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    tone: str
    greeting: Optional[str]
    fallback_message: Optional[str]
    model: str
    created_at: str
    updated_at: str
