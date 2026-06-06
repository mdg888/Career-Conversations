import pytest
from backend.src.services.vector_store import ChromaVectorStore


@pytest.fixture
def store(tmp_path):
    return ChromaVectorStore(
        collection_name="test_collection",
        persist_dir=tmp_path / "chroma",
    )


def test_add_and_query(store):
    store.add_documents(
        texts=["Python is a programming language", "FastAPI is a web framework"],
        metadatas=[{"source": "doc1.txt"}, {"source": "doc2.txt"}],
        ids=["chunk_0", "chunk_1"],
    )
    results = store.query("Python programming", n_results=1)
    assert len(results) == 1
    assert "Python" in results[0].text
    assert results[0].source == "doc1.txt"


def test_query_empty_store(store):
    results = store.query("anything")
    assert results == []


def test_count(store):
    assert store.count() == 0
    store.add_documents(
        texts=["hello"],
        metadatas=[{"source": "f.txt"}],
        ids=["id1"],
    )
    assert store.count() == 1


def test_delete_documents(store):
    store.add_documents(
        texts=["to delete", "to keep"],
        metadatas=[{"source": "a"}, {"source": "b"}],
        ids=["del_id", "keep_id"],
    )
    store.delete_documents(["del_id"])
    assert store.count() == 1


def test_reset(store):
    store.add_documents(
        texts=["data"],
        metadatas=[{"source": "x"}],
        ids=["id1"],
    )
    store.reset()
    assert store.count() == 0


def test_add_empty(store):
    store.add_documents([], [], [])
    assert store.count() == 0


def test_query_returns_scores(store):
    store.add_documents(
        texts=["machine learning algorithms"],
        metadatas=[{"source": "ml.txt"}],
        ids=["ml_0"],
    )
    results = store.query("machine learning", n_results=1)
    assert 0.0 <= results[0].score <= 1.0
