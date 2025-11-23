from __future__ import annotations

import os
from enum import Enum
from typing import Iterable, List, Optional

from langchain_core.documents import Document

try:  # Optional dependency for Cohere reranker
    import cohere
except ModuleNotFoundError:  # pragma: no cover - optional
    cohere = None  # type: ignore

try:  # Optional dependency for BGE reranker
    from FlagEmbedding import FlagReranker
except ModuleNotFoundError:  # pragma: no cover - optional
    FlagReranker = None  # type: ignore

try:  # Optional dependency for cross-encoder reranker
    from sentence_transformers import CrossEncoder
except ModuleNotFoundError:  # pragma: no cover - optional
    CrossEncoder = None  # type: ignore

from backend.config.settings import RetrievalConfig, get_settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


class RerankerType(str, Enum):
    COHERE = "cohere"
    BGE = "bge"
    CROSS_ENCODER = "cross_encoder"


class RerankerService:
    def __init__(self, config: RetrievalConfig | None = None) -> None:
        self.config = config or get_settings().retrieval
        self.model_name = (self.config.reranker or "").lower()
        self.reranker_type = self._detect_type(self.model_name)
        self._cohere_client: Optional[cohere.Client] = None  # type: ignore[attr-defined]
        self._bge_reranker: Optional[FlagReranker] = None  # type: ignore[name-defined]
        self._cross_encoder: Optional[CrossEncoder] = None  # type: ignore[name-defined]
        if self.reranker_type == RerankerType.COHERE:
            if not cohere:
                logger.warning("cohere package not installed; reranker will be disabled")
                self.reranker_type = None
            else:
                api_key = os.getenv("COHERE_API_KEY")
                if not api_key:
                    logger.warning("COHERE_API_KEY not set; reranker will be disabled")
                    self.reranker_type = None
                else:
                    self._cohere_client = cohere.Client(api_key)
        elif self.reranker_type == RerankerType.BGE:
            if not FlagReranker:
                logger.warning("FlagEmbedding not installed; BGE reranker will be disabled")
                self.reranker_type = None
            else:
                self._bge_reranker = FlagReranker(self.model_name or "BAAI/bge-reranker-large", use_fp16=True)
        elif self.reranker_type == RerankerType.CROSS_ENCODER:
            if not CrossEncoder:
                logger.warning("sentence-transformers not installed; CrossEncoder reranker will be disabled")
                self.reranker_type = None
            else:
                self._cross_encoder = CrossEncoder(self.model_name)

    @staticmethod
    def _detect_type(model_name: str | None) -> Optional[RerankerType]:
        if not model_name:
            return None
        if "cohere" in model_name:
            return RerankerType.COHERE
        if "bge" in model_name:
            return RerankerType.BGE
        return RerankerType.CROSS_ENCODER

    def enabled(self) -> bool:
        return self.reranker_type is not None

    def rerank(self, query: str, documents: Iterable[Document], top_k: int | None = None) -> List[Document]:
        docs = list(documents)
        if not self.enabled() or not docs:
            return docs
        limit = min(top_k or self.config.reranker_top_k, len(docs))
        if self.reranker_type == RerankerType.COHERE and self._cohere_client:
            return self._rerank_with_cohere(query, docs, limit)
        if self.reranker_type == RerankerType.BGE and self._bge_reranker:
            return self._rerank_with_bge(query, docs, limit)
        if self.reranker_type == RerankerType.CROSS_ENCODER and self._cross_encoder:
            return self._rerank_with_cross_encoder(query, docs, limit)
        return docs

    def _rerank_with_cohere(self, query: str, docs: List[Document], limit: int) -> List[Document]:
        payload = [{"text": doc.page_content} for doc in docs]
        response = self._cohere_client.rerank(
            query=query,
            documents=payload,
            top_n=limit,
            model=self.config.reranker,
        )
        ranked = sorted(response, key=lambda item: item.relevance_score, reverse=True)
        return [docs[item.index] for item in ranked]

    def _rerank_with_bge(self, query: str, docs: List[Document], limit: int) -> List[Document]:
        pairs = [[query, doc.page_content] for doc in docs]
        scores = self._bge_reranker.compute_score(pairs, batch_size=16)
        scored = list(zip(docs, scores))
        scored.sort(key=lambda item: item[1], reverse=True)
        return [doc for doc, _ in scored[:limit]]

    def _rerank_with_cross_encoder(self, query: str, docs: List[Document], limit: int) -> List[Document]:
        pairs = [(query, doc.page_content) for doc in docs]
        scores = self._cross_encoder.predict(pairs)
        scored = list(zip(docs, scores))
        scored.sort(key=lambda item: float(item[1]), reverse=True)
        return [doc for doc, _ in scored[:limit]]
