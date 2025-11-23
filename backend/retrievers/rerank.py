from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from backend.services.reranker_service import RerankerService


class RerankingRetriever(BaseRetriever):
    def __init__(self, base_retriever: BaseRetriever, reranker: RerankerService) -> None:
        super().__init__()
        self.base_retriever = base_retriever
        self.reranker = reranker

    def _get_relevant_documents(self, query: str) -> list[Document]:
        docs = self.base_retriever.get_relevant_documents(query)
        return self.reranker.rerank(query, docs)

    async def _aget_relevant_documents(self, query: str) -> list[Document]:
        docs = await self.base_retriever.aget_relevant_documents(query)
        return self.reranker.rerank(query, docs)
