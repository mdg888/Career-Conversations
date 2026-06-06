import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from backend.src.services.document_service import DocumentService
from backend.src.services.ocr_service import OCRService


@pytest.fixture
def service(tmp_path, tmp_db):
    return DocumentService(data_dir=tmp_path / "data")


@pytest.fixture
def chatbot_id(tmp_db):
    from backend.src.services.config_service import ConfigService
    from backend.src.models.chatbot import ChatbotCreate
    bot = ConfigService().create_chatbot(ChatbotCreate(name="Test Bot"))
    return bot.id


def _make_txt_bytes(text: str) -> bytes:
    return text.encode("utf-8")


@patch.object(DocumentService, "_embed_and_store")
def test_ingest_txt(mock_embed, service, chatbot_id):
    content = _make_txt_bytes("Hello, this is a test document.")
    doc = service.ingest(chatbot_id, content, "test.txt")

    assert doc.chatbot_id == chatbot_id
    assert doc.filename == "test.txt"
    assert doc.file_type == "txt"
    assert doc.status == "ready"
    mock_embed.assert_called_once()


@patch.object(DocumentService, "_embed_and_store")
def test_ingest_md(mock_embed, service, chatbot_id):
    content = _make_txt_bytes("# Heading\nSome markdown content.")
    doc = service.ingest(chatbot_id, content, "readme.md")
    assert doc.status == "ready"
    assert doc.file_type == "md"


def test_ingest_unsupported_type(service, chatbot_id):
    with pytest.raises(ValueError, match="not supported"):
        service.ingest(chatbot_id, b"content", "script.exe")


@patch.object(DocumentService, "_embed_and_store")
def test_list_documents(mock_embed, service, chatbot_id):
    service.ingest(chatbot_id, _make_txt_bytes("doc one"), "one.txt")
    service.ingest(chatbot_id, _make_txt_bytes("doc two"), "two.txt")
    docs = service.list_documents(chatbot_id)
    assert len(docs) == 2


@patch.object(DocumentService, "_embed_and_store")
def test_delete_document(mock_embed, service, chatbot_id):
    doc = service.ingest(chatbot_id, _make_txt_bytes("delete me"), "del.txt")
    result = service.delete_document(doc.id)
    assert result is True
    docs = service.list_documents(chatbot_id)
    assert len(docs) == 0


def test_delete_nonexistent_document(service):
    assert service.delete_document("fake-id") is False


@patch.object(DocumentService, "_embed_and_store")
def test_get_document(mock_embed, service, chatbot_id):
    doc = service.ingest(chatbot_id, _make_txt_bytes("content"), "file.txt")
    fetched = service.get_document(doc.id)
    assert fetched.id == doc.id


@patch.object(DocumentService, "_embed_and_store")
def test_ingest_stores_file_on_disk(mock_embed, service, chatbot_id):
    content = _make_txt_bytes("stored content")
    doc = service.ingest(chatbot_id, content, "stored.txt")
    # Verify the file was written to the expected storage directory
    storage_dir = service._storage_dir(chatbot_id)
    stored_files = list(storage_dir.glob(f"*_{doc.filename}"))
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == content


@patch.object(DocumentService, "_embed_and_store", side_effect=RuntimeError("embed failed"))
def test_ingest_marks_failed_on_embed_error(mock_embed, service, chatbot_id):
    content = _make_txt_bytes("some content")
    doc = service.ingest(chatbot_id, content, "fail.txt")
    assert doc.status == "failed"
    assert "embed failed" in doc.error
