import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel
from openai import OpenAI

from backend.src.core.tool_registry import make_tool_registry, TOOL_SCHEMAS
from backend.src.db.database import get_connection
from backend.src.models.chat import ChatRequest, ChatResponse, Message
from backend.src.services.config_service import ConfigService
from backend.src.services.vector_store import ChromaVectorStore

SYSTEM_PROMPT_TEMPLATE = """\
You are an AI assistant representing {name}.

{description}

Answer questions using only the knowledge base context provided below.
If the answer is not in the context, respond with: "{fallback_message}"

Do not hallucinate or invent information not in the context.
Maintain a {tone} tone throughout.

If the user expresses interest in connecting or getting in touch, ask for
their name and email and use the record_contact tool to save their details.
Include a brief summary of what they were interested in or asked about as the notes field.

If you cannot answer a question, use the record_unknown_question tool to log it.

## Knowledge Base Context:
{context}

With this context, assist the user while always representing {name}.
"""

EVALUATOR_TEMPLATE = """\
You are a quality evaluator for an AI chatbot representing {name}.

Evaluate whether the Agent's latest response is acceptable given:
- It should only use information from the provided knowledge base.
- It should maintain a {tone} tone.
- It should not hallucinate facts.
- If asked to get in touch, it should collect name and email.
- It should decline off-topic questions politely.

Knowledge base context used:
{context}
"""


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


class ChatService:

    def __init__(self, data_dir: Path, config_service: ConfigService | None = None, openai_client: OpenAI | None = None):
        self._data_dir = data_dir
        self._config_service = config_service or ConfigService()
        self._openai: OpenAI | None = openai_client

    def _get_openai(self) -> OpenAI:
        if self._openai is None:
            self._openai = OpenAI()
        return self._openai

    def _get_vector_store(self, chatbot_id: str) -> ChromaVectorStore:
        persist_dir = self._data_dir / "users" / chatbot_id / "chroma"
        return ChromaVectorStore(
            collection_name=f"chatbot_{chatbot_id}",
            persist_dir=persist_dir,
        )

    def _retrieve_context(self, chatbot_id: str, query: str, n: int = 5) -> tuple[str, list[str]]:
        store = self._get_vector_store(chatbot_id)
        results = store.query(query, n_results=n)
        if not results:
            return "", []
        context = "\n\n---\n\n".join(r.text for r in results)
        sources = list(dict.fromkeys(r.source for r in results))
        return context, sources

    def _handle_tool_calls(self, tool_calls, registry: dict) -> list[dict]:
        results = []
        for tc in tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            fn = registry.get(name)
            result = fn(**args) if fn else {}
            results.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tc.id,
            })
        return results

    def _evaluate(self, reply: str, message: str, history: list, config, context: str) -> Evaluation:
        evaluator_prompt = EVALUATOR_TEMPLATE.format(
            name=config.name,
            tone=config.tone,
            context=context or "(no context retrieved)",
        )
        messages = [
            {"role": "system", "content": evaluator_prompt},
            {"role": "user", "content": (
                f"Conversation so far:\n{history}\n\n"
                f"Latest user message:\n{message}\n\n"
                f"Agent's latest response:\n{reply}\n\n"
                "Is this response acceptable?"
            )},
        ]
        response = self._get_openai().beta.chat.completions.parse(
            model=config.model,
            messages=messages,
            response_format=Evaluation,
        )
        return response.choices[0].message.parsed

    def _rerun(self, reply: str, message: str, history: list, config, context: str, feedback: str) -> str:
        system = SYSTEM_PROMPT_TEMPLATE.format(
            name=config.name,
            description=config.description or "",
            fallback_message=config.fallback_message or "I don't have that information.",
            tone=config.tone,
            context=context or "(no context retrieved)",
        )
        system += (
            f"\n\n## Previous response was rejected by quality control\n"
            f"Your attempted answer: {reply}\n"
            f"Reason for rejection: {feedback}\n"
            "Please provide an improved response."
        )
        messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": message}]
        response = self._get_openai().chat.completions.create(model=config.model, messages=messages)
        return response.choices[0].message.content

    def chat(self, chatbot_id: str, request: ChatRequest) -> ChatResponse:
        config = self._config_service.get_chatbot(chatbot_id)
        if not config:
            raise ValueError(f"Chatbot {chatbot_id} not found")

        context, sources = self._retrieve_context(chatbot_id, request.message)

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            name=config.name,
            description=config.description or "",
            fallback_message=config.fallback_message or "I don't have that information.",
            tone=config.tone,
            context=context or "(No documents have been uploaded yet.)",
        )

        history = [{"role": m.role, "content": m.content} for m in request.history]
        messages = [{"role": "system", "content": system_prompt}] + history + [
            {"role": "user", "content": request.message}
        ]

        registry = make_tool_registry(chatbot_id)
        done = False
        while not done:
            response = self._get_openai().chat.completions.create(
                model=config.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
            )
            if response.choices[0].finish_reason == "tool_calls":
                msg_obj = response.choices[0].message
                results = self._handle_tool_calls(msg_obj.tool_calls, registry)
                messages.append(msg_obj)
                messages.extend(results)
            else:
                done = True

        reply = response.choices[0].message.content

        evaluation = self._evaluate(reply, request.message, history, config, context)
        if not evaluation.is_acceptable:
            reply = self._rerun(reply, request.message, history, config, context, evaluation.feedback)

        session_id = request.session_id or str(uuid.uuid4())
        self._persist_message(chatbot_id, session_id, "user", request.message)
        self._persist_message(chatbot_id, session_id, "assistant", reply, sources)

        return ChatResponse(reply=reply, session_id=session_id, sources=sources)

    def _persist_message(self, chatbot_id: str, session_id: str, role: str, content: str, sources: list[str] | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM chat_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO chat_sessions (id, chatbot_id, started_at) VALUES (?, ?, ?)",
                    (session_id, chatbot_id, now)
                )
            msg_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO chat_messages (id, session_id, role, content, sources, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (msg_id, session_id, role, content, json.dumps(sources or []), now)
            )

    def get_sessions(self, chatbot_id: str) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_sessions WHERE chatbot_id = ? ORDER BY started_at DESC",
                (chatbot_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_messages(self, session_id: str) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,)
            ).fetchall()
        result = []
        for r in rows:
            msg = dict(r)
            msg["sources"] = json.loads(msg.get("sources") or "[]")
            result.append(msg)
        return result
