import json
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from backend.src.db.database import get_connection
from backend.src.models.chatbot import ChatbotCreate, ChatbotUpdate, ChatbotResponse


class ConfigService:

    def create_chatbot(self, data: ChatbotCreate) -> ChatbotResponse:
        chatbot_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO chatbots (id, name, description, tone, greeting, fallback_message, model, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chatbot_id, data.name, data.description, data.tone,
                 data.greeting, data.fallback_message, data.model, now, now)
            )
        return self.get_chatbot(chatbot_id)

    def get_chatbot(self, chatbot_id: str) -> Optional[ChatbotResponse]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM chatbots WHERE id = ?", (chatbot_id,)
            ).fetchone()
        if not row:
            return None
        return ChatbotResponse(**dict(row))

    def list_chatbots(self) -> list[ChatbotResponse]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chatbots ORDER BY created_at DESC"
            ).fetchall()
        return [ChatbotResponse(**dict(r)) for r in rows]

    def update_chatbot(self, chatbot_id: str, data: ChatbotUpdate) -> Optional[ChatbotResponse]:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        if not updates:
            return self.get_chatbot(chatbot_id)
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [chatbot_id]
        with get_connection() as conn:
            conn.execute(
                f"UPDATE chatbots SET {set_clause} WHERE id = ?", values
            )
        return self.get_chatbot(chatbot_id)

    def delete_chatbot(self, chatbot_id: str) -> bool:
        with get_connection() as conn:
            result = conn.execute(
                "DELETE FROM chatbots WHERE id = ? RETURNING id", (chatbot_id,)
            ).fetchone()
        return result is not None
