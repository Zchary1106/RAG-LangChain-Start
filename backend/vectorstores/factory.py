from __future__ import annotations

from backend.config.settings import Settings
from backend.services.embedding_service import get_embedding_model
from backend.vectorstores.base import VectorStoreAdapter
from backend.vectorstores.chroma_store import ChromaVectorStore
from backend.vectorstores.faiss_store import FAISSVectorStore
from backend.vectorstores.qdrant_store import QdrantVectorStore


def create_vector_store(settings: Settings) -> VectorStoreAdapter:
    embeddings = get_embedding_model()
    persist_path = settings.vector_store_path
    persist_path.mkdir(parents=True, exist_ok=True)
    vstore_type = settings.vector_store.type
    if vstore_type == "faiss":
        return FAISSVectorStore(persist_path, embeddings)
    if vstore_type == "qdrant":
        cfg = settings.vector_store
        return QdrantVectorStore(
            persist_path,
            embeddings,
            host=cfg.host,
            port=cfg.port,
            api_key=cfg.api_key,
            collection_name=cfg.collection_name,
        )
    return ChromaVectorStore(persist_path, embeddings)
