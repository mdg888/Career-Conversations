from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import chromadb


@dataclass
class QueryResult:
    text: str
    source: str
    score: float


class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, texts: list[str], metadatas: list[dict], ids: list[str]) -> None: ...

    @abstractmethod
    def query(self, query_text: str, n_results: int = 5) -> list[QueryResult]: ...

    @abstractmethod
    def delete_documents(self, ids: list[str]) -> None: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def count(self) -> int: ...


class ChromaVectorStore(VectorStore):

    def __init__(self, collection_name: str, persist_dir: Path):
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, texts: list[str], metadatas: list[dict], ids: list[str]) -> None:
        if not texts:
            return
        self._collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def query(self, query_text: str, n_results: int = 5) -> list[QueryResult]:
        count = self._collection.count()
        if count == 0:
            return []
        actual_n = min(n_results, count)
        results = self._collection.query(
            query_texts=[query_text],
            n_results=actual_n,
            include=["documents", "metadatas", "distances"]
        )
        out = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            out.append(QueryResult(
                text=doc,
                source=meta.get("source", "Unknown"),
                score=1.0 - dist,
            ))
        return out

    def delete_documents(self, ids: list[str]) -> None:
        if ids:
            self._collection.delete(ids=ids)

    def reset(self) -> None:
        self._client.delete_collection(self._collection.name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection.name,
            metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return self._collection.count()
