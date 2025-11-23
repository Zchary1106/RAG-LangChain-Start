from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document
from langchain.vectorstores.base import VectorStoreRetriever

from backend.config.settings import Settings, get_settings
from backend.core.logger import get_logger
from backend.retrievers.hybrid import HybridRetriever
from backend.vectorstores.base import VectorStoreAdapter
from backend.vectorstores.factory import create_vector_store

logger = get_logger(__name__)


def _to_base_retriever(retriever: VectorStoreRetriever):
    return retriever  # satisfies BaseRetriever protocol


class VectorStoreService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.adapter: VectorStoreAdapter = create_vector_store(self.settings)
        self.documents: List[Document] = []
        self._ensure_vector_store_loaded()

    def build_store(self, documents: List[Document]) -> VectorStoreAdapter:
        logger.info("Building vector store with %s documents", len(documents))
        self.documents = documents
        self.adapter.build(documents)
        return self.adapter

    def switch_store(self, store_type: str) -> None:
        store_type = store_type.lower()
        if store_type == self.settings.vector_store.type:
            return
        logger.info("Switching vector store adapter to %s", store_type)
        self.settings.vector_store.type = store_type  # type: ignore[assignment]
        self.adapter = create_vector_store(self.settings)
        self._ensure_vector_store_loaded()

    def get_retriever(self, strategy: str | None = None, top_k: int | None = None):
        strategy = (strategy or self.settings.retrieval.strategy).lower()
        top_k = top_k or self.settings.retrieval.top_k
        vector_retriever = _to_base_retriever(
            self.adapter.as_retriever(search_kwargs={"k": top_k})
        )
        
        def _fallback(reason: str):
            logger.warning("Retrieval strategy %s fallback to vector retriever: %s", strategy, reason)
            return vector_retriever

        def _build_keyword_retriever():
            if not self.documents:
                return None, "No source documents are available. Re-run the build workflow to enable BM25/Hybrid retrieval."
            try:
                retriever = BM25Retriever.from_documents(self.documents, k=top_k)
                return retriever, None
            except ImportError as exc:
                return None, f"Missing dependency rank_bm25: {exc}"
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to initialize BM25 retriever")
                return None, str(exc)
        if strategy == "vector":
            return vector_retriever
        if strategy == "bm25":
            keyword_retriever, reason = _build_keyword_retriever()
            if keyword_retriever is None:
                return _fallback(reason or "BM25 retriever unavailable")
            return keyword_retriever
        if strategy in {"hybrid", "router"}:
            keyword_retriever, reason = _build_keyword_retriever()
            if keyword_retriever is None:
                return _fallback(reason or "Hybrid keyword retriever unavailable")
            return HybridRetriever(vector_retriever, keyword_retriever)
        raise ValueError(f"Unsupported retrieval strategy: {strategy}")

    def has_index(self) -> bool:
        self._ensure_vector_store_loaded()
        return self.adapter.vector_store is not None

    def _ensure_vector_store_loaded(self) -> None:
        if self.adapter.vector_store is not None:
            return
        if not self._has_persisted_store():
            return
        try:
            self.adapter.load()
            logger.info("Loaded persisted vector store from %s", self.settings.vector_store_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load existing vector store: %s", exc)

    def _has_persisted_store(self) -> bool:
        path: Path = self.settings.vector_store_path
        if not path.exists():
            return False
        try:
            next(path.iterdir())
            return True
        except StopIteration:
            return False
        except FileNotFoundError:
            return False
