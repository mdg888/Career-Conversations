import json
import uuid
from datetime import datetime, timezone
from typing import Callable


def make_tool_registry(chatbot_id: str) -> dict[str, Callable]:
    """Return tool functions bound to a specific chatbot."""

    def record_contact(email: str, name: str = "Not provided", notes: str = "") -> dict:
        from backend.src.db.database import get_connection
        capture_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO contact_captures (id, chatbot_id, email, name, notes, captured_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (capture_id, chatbot_id, email, name, notes, now)
            )
        return {"status": "success", "capture_id": capture_id}

    def record_unknown_question(question: str) -> dict:
        from backend.src.db.database import get_connection
        q_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO unknown_questions (id, chatbot_id, question, asked_at)
                   VALUES (?, ?, ?, ?)""",
                (q_id, chatbot_id, question, now)
            )
        return {"status": "success"}

    return {
        "record_contact": record_contact,
        "record_unknown_question": record_unknown_question,
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "record_contact",
            "description": "Record that a user wants to get in touch and has provided their email address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "User email address"},
                    "name": {"type": "string", "description": "User's name if provided"},
                    "notes": {"type": "string", "description": "Any additional context from the conversation"},
                },
                "required": ["email"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "Record a question that could not be answered from the knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The unanswered question"},
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
    },
]
