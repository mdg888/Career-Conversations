import uuid
from pathlib import Path
from typing import Optional

from backend.src.db.database import get_connection
from backend.src.models.document import (
    ALLOWED_EXTENSIONS, TEXT_TYPES, PDF_TYPES, DOCX_TYPES, IMAGE_TYPES, DocumentResponse
)
from backend.src.services.ocr_service import OCRService
from backend.src.services.vector_store import ChromaVectorStore


class DocumentService:

    def __init__(self, data_dir: Path, ocr: Optional[OCRService] = None):
        self._data_dir = data_dir
        self._ocr = ocr or OCRService()

    def _storage_dir(self, chatbot_id: str) -> Path:
        return self._data_dir / "users" / chatbot_id / "documents"

    def _chroma_dir(self, chatbot_id: str) -> Path:
        return self._data_dir / "users" / chatbot_id / "chroma"

    def _get_vector_store(self, chatbot_id: str) -> ChromaVectorStore:
        return ChromaVectorStore(
            collection_name=f"chatbot_{chatbot_id}",
            persist_dir=self._chroma_dir(chatbot_id),
        )

    def _extract_text(self, file_path: Path, file_type: str) -> str:
        if file_type in TEXT_TYPES:
            return file_path.read_text(encoding="utf-8", errors="replace")

        if file_type in PDF_TYPES:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )

        if file_type in DOCX_TYPES:
            from docx import Document
            doc = Document(str(file_path))
            return "\n".join(p.text for p in doc.paragraphs)

        if file_type in IMAGE_TYPES:
            return self._ocr.extract_text(file_path)

        return ""

    def ingest(self, chatbot_id: str, file_bytes: bytes, filename: str) -> DocumentResponse:
        ext = Path(filename).suffix.lstrip(".").lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type '{ext}' is not supported.")

        doc_id = str(uuid.uuid4())
        storage_dir = self._storage_dir(chatbot_id)
        storage_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{doc_id}_{filename}"
        file_path = storage_dir / safe_name
        file_path.write_bytes(file_bytes)

        with get_connection() as conn:
            conn.execute(
                """INSERT INTO documents (id, chatbot_id, filename, file_type, file_path, status)
                   VALUES (?, ?, ?, ?, ?, 'pending')""",
                (doc_id, chatbot_id, filename, ext, str(file_path))
            )

        try:
            text = self._extract_text(file_path, ext)
            if text.strip():
                self._embed_and_store(chatbot_id, doc_id, filename, text)

            with get_connection() as conn:
                conn.execute(
                    "UPDATE documents SET status = 'ready' WHERE id = ?", (doc_id,)
                )
        except Exception as e:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE documents SET status = 'failed', error = ? WHERE id = ?",
                    (str(e), doc_id)
                )

        return self.get_document(doc_id)

    def _embed_and_store(self, chatbot_id: str, doc_id: str, filename: str, text: str) -> None:
        from backend.src.services.embedding_service import EmbeddingService
        embedder = EmbeddingService()
        chunks = embedder.chunk(text)
        if not chunks:
            return

        store = self._get_vector_store(chatbot_id)
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
        store.add_documents(texts=chunks, metadatas=metadatas, ids=ids)

    def delete_document(self, doc_id: str) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT chatbot_id, file_path FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            if not row:
                return False
            chatbot_id = row["chatbot_id"]
            file_path = Path(row["file_path"])

        store = self._get_vector_store(chatbot_id)
        existing = store.count()
        if existing > 0:
            chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(1000)]
            try:
                store.delete_documents(chunk_ids)
            except Exception:
                pass

        if file_path.exists():
            file_path.unlink()

        with get_connection() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

        return True

    def get_document(self, doc_id: str) -> Optional[DocumentResponse]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
        if not row:
            return None
        return DocumentResponse(**dict(row))

    def list_documents(self, chatbot_id: str) -> list[DocumentResponse]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE chatbot_id = ? ORDER BY created_at DESC",
                (chatbot_id,)
            ).fetchall()
        return [DocumentResponse(**dict(r)) for r in rows]

    def rebuild_embeddings(self, doc_id: str) -> DocumentResponse:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
        if not row:
            raise ValueError(f"Document {doc_id} not found")

        doc = dict(row)
        chatbot_id = doc["chatbot_id"]
        file_path = Path(doc["file_path"])
        file_type = doc["file_type"]

        store = self._get_vector_store(chatbot_id)
        try:
            store.delete_documents([f"{doc_id}_chunk_{i}" for i in range(1000)])
        except Exception:
            pass

        try:
            text = self._extract_text(file_path, file_type)
            if text.strip():
                self._embed_and_store(chatbot_id, doc_id, doc["filename"], text)
            with get_connection() as conn:
                conn.execute(
                    "UPDATE documents SET status = 'ready', error = NULL WHERE id = ?", (doc_id,)
                )
        except Exception as e:
            with get_connection() as conn:
                conn.execute(
                    "UPDATE documents SET status = 'failed', error = ? WHERE id = ?",
                    (str(e), doc_id)
                )

        return self.get_document(doc_id)
