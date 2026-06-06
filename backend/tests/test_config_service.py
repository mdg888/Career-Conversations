import pytest
from backend.src.services.config_service import ConfigService
from backend.src.models.chatbot import ChatbotCreate, ChatbotUpdate


@pytest.fixture
def service(tmp_db):
    return ConfigService()


def test_create_chatbot(service):
    data = ChatbotCreate(
        name="Test Bot",
        description="A test chatbot",
        tone="friendly",
        greeting="Hello!",
        fallback_message="I don't know.",
    )
    bot = service.create_chatbot(data)
    assert bot.id
    assert bot.name == "Test Bot"
    assert bot.tone == "friendly"


def test_get_chatbot(service):
    bot = service.create_chatbot(ChatbotCreate(name="Bot A"))
    fetched = service.get_chatbot(bot.id)
    assert fetched.id == bot.id
    assert fetched.name == "Bot A"


def test_get_chatbot_not_found(service):
    result = service.get_chatbot("nonexistent-id")
    assert result is None


def test_list_chatbots(service):
    service.create_chatbot(ChatbotCreate(name="Bot 1"))
    service.create_chatbot(ChatbotCreate(name="Bot 2"))
    bots = service.list_chatbots()
    assert len(bots) == 2


def test_update_chatbot(service):
    bot = service.create_chatbot(ChatbotCreate(name="Original"))
    updated = service.update_chatbot(bot.id, ChatbotUpdate(name="Updated"))
    assert updated.name == "Updated"


def test_update_chatbot_partial(service):
    bot = service.create_chatbot(ChatbotCreate(name="Bot", tone="professional"))
    updated = service.update_chatbot(bot.id, ChatbotUpdate(tone="casual"))
    assert updated.name == "Bot"
    assert updated.tone == "casual"


def test_delete_chatbot(service):
    bot = service.create_chatbot(ChatbotCreate(name="To Delete"))
    assert service.delete_chatbot(bot.id) is True
    assert service.get_chatbot(bot.id) is None


def test_delete_chatbot_not_found(service):
    assert service.delete_chatbot("fake-id") is False
