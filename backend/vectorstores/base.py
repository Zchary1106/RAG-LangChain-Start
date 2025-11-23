from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain.schema.embeddings import Embeddings
from langchain.vectorstores.base import VectorStore


class VectorStoreAdapter(ABC):
    def __init__(self, persist_path: Path, embeddings: Embeddings) -> None:
        self.persist_path = persist_path
        self.embeddings = embeddings
        self.vector_store: VectorStore | None = None

    @abstractmethod
    def build(self, documents: List[Document]) -> VectorStore:
        raise NotImplementedError

    @abstractmethod
    def load(self) -> VectorStore:
        raise NotImplementedError

    def as_retriever(self, **kwargs):
        store = self.vector_store or self.load()
        return store.as_retriever(**kwargs)
