from openai import OpenAI


class EmbeddingService:

    def __init__(self, model: str = "text-embedding-3-small"):
        self._client: OpenAI | None = None
        self._model = model

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI()
        return self._client

    def chunk(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        words = text.split()
        if not words:
            return []
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunks.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start += chunk_size - overlap
        return chunks

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._get_client().embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in response.data]
