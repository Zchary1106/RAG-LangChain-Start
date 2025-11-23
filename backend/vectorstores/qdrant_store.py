from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from langchain.schema import Document
from langchain.schema.embeddings import Embeddings

try:  # Optional dependency
    from langchain_community.vectorstores import Qdrant
    from qdrant_client import QdrantClient
except ModuleNotFoundError as exc:  # pragma: no cover - optional
    Qdrant = None  # type: ignore
    QdrantClient = None  # type: ignore
    _QDRANT_IMPORT_ERROR = exc
else:  # pragma: no cover - import succeeds
    _QDRANT_IMPORT_ERROR = None

from backend.vectorstores.base import VectorStoreAdapter


class QdrantVectorStore(VectorStoreAdapter):
    def __init__(
        self,
        persist_path: Path,
        embeddings: Embeddings,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        collection_name: str = "langchain_rag",
    ) -> None:
        super().__init__(persist_path, embeddings)
        if _QDRANT_IMPORT_ERROR is not None:
            raise RuntimeError(
                "Qdrant dependencies are not installed. Please `pip install qdrant-client langchain-community` "
                "or switch `vector_store.type` away from 'qdrant'."
            ) from _QDRANT_IMPORT_ERROR
        self.host = host or "http://localhost"
        self.port = port or 6333
        self.api_key = api_key
        self.collection_name = collection_name

    @property
    def _client(self) -> QdrantClient:
        return QdrantClient(url=f"{self.host}:{self.port}", api_key=self.api_key)

    def build(self, documents: List[Document]):
        self.vector_store = Qdrant.from_documents(
            documents=documents,
            embedding=self.embeddings,
            location=f"{self.host}:{self.port}",
            api_key=self.api_key,
            collection_name=self.collection_name,
        )
        return self.vector_store

    def load(self):
        self.vector_store = Qdrant(
            client=self._client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
        )
        return self.vector_store
