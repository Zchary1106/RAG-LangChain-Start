from __future__ import annotations

import os
import asyncio
from typing import List, Tuple

from langchain.chains import RetrievalQA
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain_core.documents import Document
from langchain_community.llms import FakeListLLM
from langchain_openai import AzureChatOpenAI

from backend.config.settings import Settings, get_settings
from backend.core.logger import get_logger
from backend.retrievers.rerank import RerankingRetriever
from backend.services.prompts import COMBINE_PROMPT, MAP_PROMPT, STUFF_PROMPT
from backend.services.reranker_service import RerankerService
from backend.services.router_service import RouterService
from backend.services.vector_store_service import VectorStoreService

logger = get_logger(__name__)


class RAGService:
    def __init__(self, vector_service: VectorStoreService, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.vector_service = vector_service
        self.llm = self._init_llm()
        self.router_service = RouterService(self.settings)
        self.reranker_service = RerankerService(self.settings.retrieval)

    def generate_answer(
        self,
        question: str,
        retrieval_strategy: str | None = None,
        chain_type: str = "standard",
        top_k: int | None = None,
    ) -> Tuple[str, List[Document], str, str]:
        strategy, resolved_chain = self._pick_strategy_and_chain(question, retrieval_strategy, chain_type)
        retriever = self.vector_service.get_retriever(strategy=strategy, top_k=top_k)
        if self.reranker_service.enabled():
            retriever = RerankingRetriever(retriever, self.reranker_service)
        qa_chain = self._build_chain(resolved_chain, retriever)
        logger.info("Running RAG pipeline with %s strategy and %s chain", strategy, resolved_chain)
        result = qa_chain.invoke({"query": question})
        answer = result["result"]
        docs: List[Document] = result.get("source_documents", [])
        if not docs:
            logger.info("No source documents returned; falling back to direct LLM answer.")
            answer = self._direct_answer(question)
            return answer, [], "llm_fallback", "direct_llm"
        return answer, docs, strategy, resolved_chain

    def stream_answer(
        self,
        question: str,
        retrieval_strategy: str | None = None,
        chain_type: str = "standard",
        top_k: int | None = None,
    ) -> tuple[AsyncIteratorCallbackHandler, asyncio.Task, str, str, bool]:
        strategy, resolved_chain = self._pick_strategy_and_chain(question, retrieval_strategy, chain_type)
        retriever = self.vector_service.get_retriever(strategy=strategy, top_k=top_k)
        if self.reranker_service.enabled():
            retriever = RerankingRetriever(retriever, self.reranker_service)
        preview_docs = self._preview_documents(retriever, question)
        handler = AsyncIteratorCallbackHandler()
        streaming_llm = self._init_llm(streaming=True, callbacks=[handler])
        if not hasattr(streaming_llm, "ainvoke") and not hasattr(streaming_llm, "astream"):
            logger.info("Configured LLM lacks async streaming support; falling back to direct answer.")

            async def _direct_task():
                response = await self._invoke_llm_async(streaming_llm, question)
                content = getattr(response, "content", str(response))
                return {"result": content, "source_documents": []}

            task = asyncio.create_task(_direct_task())
            return handler, task, "llm_fallback", "direct_llm", False
        if not preview_docs:
            logger.info("No documents found for streaming run; streaming direct LLM answer instead.")

            async def _direct_task():
                response = await self._invoke_llm_async(streaming_llm, question)
                content = getattr(response, "content", str(response))
                return {"result": content, "source_documents": []}

            task = asyncio.create_task(_direct_task())
            return handler, task, "llm_fallback", "direct_llm", False
        qa_chain = self._build_chain(resolved_chain, retriever, llm=streaming_llm)
        logger.info("Streaming RAG pipeline with %s strategy and %s chain", strategy, resolved_chain)
        task = asyncio.create_task(qa_chain.ainvoke({"query": question}))
        return handler, task, strategy, resolved_chain, True

    def _preview_documents(self, retriever, question: str) -> List[Document]:
        try:
            if hasattr(retriever, "invoke"):
                docs = retriever.invoke(question)
            elif hasattr(retriever, "get_relevant_documents"):
                docs = retriever.get_relevant_documents(question)
            else:
                return []
            return docs or []
        except Exception as exc:  # noqa: BLE001
            logger.warning("Preview retrieval failed, falling back to direct LLM: %s", exc)
            return []

    async def _invoke_llm_async(self, llm, prompt: str):
        if hasattr(llm, "ainvoke"):
            return await llm.ainvoke(prompt)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: llm.invoke(prompt))

    def _build_chain(self, chain_type: str, retriever, llm=None):
        chain_type = chain_type.lower()
        lc_chain_type = "stuff"
        effective_retriever = retriever
        if chain_type == "map_reduce":
            lc_chain_type = "map_reduce"
        elif chain_type == "compression":
            compressor = LLMChainExtractor.from_llm(llm or self.llm)
            effective_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)
        elif chain_type == "router":
            # Router still leverages default chain, but retrieval strategy may have been altered already
            lc_chain_type = "stuff"
        chain_kwargs = self._prompt_kwargs(lc_chain_type)
        return RetrievalQA.from_chain_type(
            llm=llm or self.llm,
            chain_type=lc_chain_type,
            retriever=effective_retriever,
            chain_type_kwargs=chain_kwargs,
            return_source_documents=True,
        )

    def _prompt_kwargs(self, chain_type: str):
        if chain_type == "map_reduce":
            return {
                "question_prompt": MAP_PROMPT,
                "combine_prompt": COMBINE_PROMPT,
            }
        return {"prompt": STUFF_PROMPT}

    def _init_llm(self, *, streaming: bool = False, callbacks: List | None = None):
        llm = self._init_azure_llm(streaming=streaming, callbacks=callbacks)
        if llm:
            return llm
        logger.warning("Azure OpenAI credentials are missing; using FakeListLLM as a placeholder model.")
        help_text = "Set the AZURE_OPENAI_API_* variables (see .env.example) and restart the service."
        return FakeListLLM(responses=[help_text])

    def _direct_answer(self, question: str) -> str:
        response = self.llm.invoke(question)
        return getattr(response, "content", str(response))

    def _init_azure_llm(self, *, streaming: bool = False, callbacks: List | None = None):
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = self.settings.model.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = self.settings.model.azure_api_version or os.getenv("AZURE_OPENAI_API_VERSION")
        deployment = self.settings.model.azure_chat_deployment or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        if not all([api_key, endpoint, api_version, deployment]):
            missing = [
                name
                for name, value in {
                    "AZURE_OPENAI_API_KEY": api_key,
                    "AZURE_OPENAI_ENDPOINT": endpoint,
                    "AZURE_OPENAI_API_VERSION": api_version,
                    "AZURE_OPENAI_CHAT_DEPLOYMENT": deployment,
                }.items()
                if not value
            ]
            logger.warning("Azure OpenAI configuration is incomplete: %s", ", ".join(missing))
            return None
        return AzureChatOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=deployment,
            api_version=api_version,
            temperature=self.settings.model.temperature,
            api_key=api_key,
            streaming=streaming,
            callbacks=callbacks or [],
        )

    def _pick_strategy_and_chain(self, question: str, override: str | None, chain_type: str | None) -> tuple[str, str]:
        target_chain = (chain_type or "standard").lower()
        if self.router_service.should_route(chain_type, override):
            decision = self.router_service.route(question)
            return decision.strategy, decision.chain
        strategy = (override or "").lower()
        if strategy and strategy != "router":
            return strategy, target_chain
        lowered = question.lower()
        if any(keyword in lowered for keyword in ["code", "api", "function"]):
            return "bm25", target_chain
        if any(keyword in lowered for keyword in ["business", "marketing", "product"]):
            return "hybrid", target_chain
        return self.settings.retrieval.strategy, target_chain
