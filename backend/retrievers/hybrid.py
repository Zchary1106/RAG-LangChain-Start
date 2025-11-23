from __future__ import annotations

from typing import List

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class HybridRetriever(BaseRetriever):
    vector_retriever: BaseRetriever
    keyword_retriever: BaseRetriever
    alpha: float = 0.6

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, vector_retriever: BaseRetriever, keyword_retriever: BaseRetriever, alpha: float = 0.6) -> None:
        super().__init__(vector_retriever=vector_retriever, keyword_retriever=keyword_retriever, alpha=alpha)

    def _get_relevant_documents(self, query: str) -> List[Document]:
        vector_docs = self.vector_retriever.get_relevant_documents(query)
        keyword_docs = self.keyword_retriever.get_relevant_documents(query)
        return self._merge(vector_docs, keyword_docs)

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        vector_docs = await self.vector_retriever.aget_relevant_documents(query)
        keyword_docs = await self.keyword_retriever.aget_relevant_documents(query)
        return self._merge(vector_docs, keyword_docs)

    def _merge(self, vector_docs: List[Document], keyword_docs: List[Document]) -> List[Document]:
        scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}
        for rank, doc in enumerate(vector_docs):
            key = doc.metadata.get("source", str(rank))
            scores[key] = scores.get(key, 0.0) + self.alpha * (1 / (rank + 1))
            doc_map[key] = doc
        for rank, doc in enumerate(keyword_docs):
            key = doc.metadata.get("source", f"kw-{rank}")
            scores[key] = scores.get(key, 0.0) + (1 - self.alpha) * (1 / (rank + 1))
            if key not in doc_map:
                doc_map[key] = doc
        ranked = sorted(doc_map.items(), key=lambda item: scores.get(item[0], 0), reverse=True)
        return [doc for _, doc in ranked]
