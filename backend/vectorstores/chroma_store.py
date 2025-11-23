from __future__ import annotations

from pathlib import Path
from typing import List

# Silence chroma telemetry + warnings before importing the vector store
import os

os.environ.setdefault("PERSIST_DIRECTORY", "")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMADB_DISABLE_TELEMETRY", "True")
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "False")
os.environ.setdefault("CHROMA_TELEMETRY", "False")
os.environ.setdefault("POSTHOG_DISABLE", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY_OPT_IN", "False")

from langchain.schema import Document
from langchain.schema.embeddings import Embeddings
from langchain_chroma import Chroma

def _disable_chroma_telemetry():  # pragma: no cover - best effort
    try:
        from chromadb.telemetry import posthog as core_posthog

        def _noop(*args, **kwargs):
            return None

        core_posthog.capture = _noop  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    try:
        from chromadb.telemetry.product import posthog as product_posthog

        def _noop_product(*args, **kwargs):
            return None

        product_posthog.capture = _noop_product  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass


_disable_chroma_telemetry()

from backend.vectorstores.base import VectorStoreAdapter


class ChromaVectorStore(VectorStoreAdapter):
    def __init__(self, persist_path: Path, embeddings: Embeddings) -> None:
        super().__init__(persist_path, embeddings)

    def build(self, documents: List[Document]):
        self.vector_store = Chroma.from_documents(
            documents,
            embedding=self.embeddings,
            persist_directory=str(self.persist_path),
        )
        persist_method = getattr(self.vector_store, "persist", None)
        if callable(persist_method):
            persist_method()
        else:
            client = getattr(self.vector_store, "_client", None)
            flush = getattr(client, "persist", None)
            if callable(flush):
                flush()
        return self.vector_store

    def load(self):
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_path),
        )
        return self.vector_store
