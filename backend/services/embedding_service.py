from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from langchain.schema.embeddings import Embeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, SentenceTransformerEmbeddings
from langchain_openai import AzureOpenAIEmbeddings

from backend.config.settings import get_settings
from backend.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


BGE_MODEL_ALIASES = {
    "bge-large": "BAAI/bge-large-en",
    "bge-m3": "BAAI/bge-m3",
    "bge-small": "BAAI/bge-small-en",
}


SUPPORTED_EMBEDDINGS = {
    "openai": "openai",
    "text-embedding-3-large": "openai",
    "text-embedding-3-small": "openai",
    "bge-large": "bge",
    "bge-m3": "bge",
    "sentence-transformers": "sentence",
}


def _resolve_embedding_backend(name: str) -> Literal["openai", "bge", "sentence"]:
    lowered = name.lower()
    for key, backend in SUPPORTED_EMBEDDINGS.items():
        if key in lowered:
            return backend  # type: ignore[return-value]
    return "sentence"


@lru_cache(maxsize=1)
def get_embedding_model() -> Embeddings:
    model_name = settings.model.embedding
    backend = _resolve_embedding_backend(model_name)
    logger.info("Loading embedding model %s via %s backend", model_name, backend)
    if backend == "openai":
        endpoint = settings.model.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = settings.model.azure_api_version or os.getenv("AZURE_OPENAI_API_VERSION")
        deployment = (
            settings.model.azure_embedding_deployment
            or os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
            or settings.model.azure_chat_deployment
            or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
        )
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        missing = [
            name
            for name, value in {
                "AZURE_OPENAI_ENDPOINT": endpoint,
                "AZURE_OPENAI_API_VERSION": api_version,
                "AZURE_OPENAI_EMBED_DEPLOYMENT": deployment,
                "AZURE_OPENAI_API_KEY": api_key,
            }.items()
            if not value
        ]
        if not missing:
            return AzureOpenAIEmbeddings(
                model=model_name,
                azure_endpoint=endpoint,
                api_version=api_version,
                azure_deployment=deployment,
                api_key=api_key,
            )
        logger.warning(
            "Azure OpenAI embedding configuration missing (%s); falling back to the local SentenceTransformer model all-MiniLM-L6-v2",
            ", ".join(missing),
        )
        return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    if backend == "bge":
        normalized_name = BGE_MODEL_ALIASES.get(model_name.lower(), model_name)
        encode_kwargs = {"normalize_embeddings": True}
        if "/" not in normalized_name:
            logger.warning(
                "BGE model %s does not appear to be a full Hugging Face repo id; defaulting to %s",
                model_name,
                normalized_name,
            )
        return HuggingFaceBgeEmbeddings(model_name=normalized_name, encode_kwargs=encode_kwargs)
    return SentenceTransformerEmbeddings(model_name=model_name)
