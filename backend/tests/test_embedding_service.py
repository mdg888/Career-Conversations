import pytest
from unittest.mock import Mock, patch
from backend.src.services.embedding_service import EmbeddingService


@pytest.fixture
def service():
    return EmbeddingService()


def test_chunk_basic(service):
    text = "word " * 600
    chunks = service.chunk(text.strip(), chunk_size=500, overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        words = chunk.split()
        assert len(words) <= 500


def test_chunk_short_text(service):
    text = "hello world"
    chunks = service.chunk(text)
    assert chunks == ["hello world"]


def test_chunk_empty(service):
    assert service.chunk("") == []


def test_chunk_overlap(service):
    words = list(range(600))
    text = " ".join(str(w) for w in words)
    chunks = service.chunk(text, chunk_size=100, overlap=20)
    # Second chunk should start 80 words after first chunk starts
    first_chunk_words = chunks[0].split()
    second_chunk_words = chunks[1].split()
    # They should share the overlap words
    assert first_chunk_words[-20:] == second_chunk_words[:20]


def test_chunk_exact_size(service):
    text = " ".join(["word"] * 500)
    chunks = service.chunk(text, chunk_size=500, overlap=0)
    assert len(chunks) == 1


def test_embed_calls_openai(service):
    mock_client = Mock()
    mock_embedding = Mock()
    mock_embedding.embedding = [0.1, 0.2, 0.3]
    mock_client.embeddings.create.return_value = Mock(data=[mock_embedding])
    service._client = mock_client

    result = service.embed(["hello world"])

    assert result == [[0.1, 0.2, 0.3]]
    mock_client.embeddings.create.assert_called_once()


def test_embed_empty(service):
    result = service.embed([])
    assert result == []


def test_embed_multiple(service):
    mock_client = Mock()
    mock_client.embeddings.create.return_value = Mock(data=[
        Mock(embedding=[0.1]),
        Mock(embedding=[0.2]),
    ])
    service._client = mock_client

    result = service.embed(["text one", "text two"])
    assert len(result) == 2
    assert result[0] == [0.1]
    assert result[1] == [0.2]
