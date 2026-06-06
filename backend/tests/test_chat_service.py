import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from pydantic import BaseModel

from backend.src.services.chat_service import ChatService, Evaluation
from backend.src.services.config_service import ConfigService
from backend.src.models.chat import ChatRequest, Message
from backend.src.models.chatbot import ChatbotCreate


@pytest.fixture
def chatbot(tmp_db):
    return ConfigService().create_chatbot(ChatbotCreate(
        name="Test Bot",
        description="A helpful assistant.",
        tone="professional",
        greeting="Hello!",
        fallback_message="I don't know.",
    ))


@pytest.fixture
def service(tmp_path, tmp_db, chatbot):
    mock_openai = Mock()
    svc = ChatService(data_dir=tmp_path / "data", openai_client=mock_openai)
    return svc, mock_openai, chatbot.id


def _make_chat_response(content: str):
    resp = Mock()
    resp.choices = [Mock()]
    resp.choices[0].finish_reason = "stop"
    resp.choices[0].message.content = content
    return resp


def _make_eval_response(acceptable: bool, feedback: str):
    resp = Mock()
    resp.choices = [Mock()]
    resp.choices[0].message.parsed = Evaluation(
        is_acceptable=acceptable, feedback=feedback
    )
    return resp


def test_chat_basic(service):
    svc, mock_openai, chatbot_id = service
    mock_openai.chat.completions.create.return_value = _make_chat_response("I can help with that.")
    mock_openai.beta.chat.completions.parse.return_value = _make_eval_response(True, "Good")

    with patch.object(svc, "_retrieve_context", return_value=("Context text", ["doc.pdf"])):
        request = ChatRequest(message="Hello", history=[])
        result = svc.chat(chatbot_id, request)

    assert result.reply == "I can help with that."
    assert result.sources == ["doc.pdf"]
    assert result.session_id


def test_chat_with_history(service):
    svc, mock_openai, chatbot_id = service
    mock_openai.chat.completions.create.return_value = _make_chat_response("Sure!")
    mock_openai.beta.chat.completions.parse.return_value = _make_eval_response(True, "OK")

    with patch.object(svc, "_retrieve_context", return_value=("", [])):
        request = ChatRequest(
            message="Follow up",
            history=[Message(role="user", content="First"), Message(role="assistant", content="Hi")]
        )
        result = svc.chat(chatbot_id, request)

    call_args = mock_openai.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    roles = [m["role"] for m in messages]
    assert "user" in roles
    assert "assistant" in roles


def test_chat_triggers_rerun_on_rejection(service):
    svc, mock_openai, chatbot_id = service
    mock_openai.chat.completions.create.side_effect = [
        _make_chat_response("Bad response"),
        _make_chat_response("Improved response"),
    ]
    mock_openai.beta.chat.completions.parse.return_value = _make_eval_response(
        False, "Too casual"
    )

    with patch.object(svc, "_retrieve_context", return_value=("", [])):
        result = svc.chat(chatbot_id, ChatRequest(message="Hi", history=[]))

    assert result.reply == "Improved response"
    assert mock_openai.chat.completions.create.call_count == 2


def test_chat_with_tool_call(service):
    svc, mock_openai, chatbot_id = service

    tool_call = Mock()
    tool_call.id = "tc_1"
    tool_call.function.name = "record_contact"
    import json
    tool_call.function.arguments = json.dumps({"email": "a@b.com"})

    first_resp = Mock()
    first_resp.choices = [Mock()]
    first_resp.choices[0].finish_reason = "tool_calls"
    first_resp.choices[0].message.tool_calls = [tool_call]

    second_resp = _make_chat_response("Recorded your email!")

    mock_openai.chat.completions.create.side_effect = [first_resp, second_resp]
    mock_openai.beta.chat.completions.parse.return_value = _make_eval_response(True, "Good")

    with patch.object(svc, "_retrieve_context", return_value=("", [])):
        result = svc.chat(chatbot_id, ChatRequest(message="email: a@b.com", history=[]))

    assert result.reply == "Recorded your email!"


def test_chat_chatbot_not_found(service):
    svc, mock_openai, _ = service
    with pytest.raises(ValueError, match="not found"):
        svc.chat("nonexistent-id", ChatRequest(message="hello", history=[]))


def test_get_sessions_empty(service):
    svc, _, chatbot_id = service
    assert svc.get_sessions(chatbot_id) == []


def test_get_messages_after_chat(service):
    svc, mock_openai, chatbot_id = service
    mock_openai.chat.completions.create.return_value = _make_chat_response("Hi!")
    mock_openai.beta.chat.completions.parse.return_value = _make_eval_response(True, "OK")

    with patch.object(svc, "_retrieve_context", return_value=("", [])):
        result = svc.chat(chatbot_id, ChatRequest(message="Hello", history=[]))

    messages = svc.get_messages(result.session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
