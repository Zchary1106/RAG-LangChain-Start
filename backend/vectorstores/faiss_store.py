from __future__ import annotations

from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain.schema.embeddings import Embeddings
from langchain_community.vectorstores import FAISS

from backend.vectorstores.base import VectorStoreAdapter


class FAISSVectorStore(VectorStoreAdapter):
    def __init__(self, persist_path: Path, embeddings: Embeddings) -> None:
        super().__init__(persist_path, embeddings)
        self.index_path = persist_path / "faiss.index"
        self.store_path = persist_path / "docs.pkl"

    def build(self, documents: List[Document]):
        store = FAISS.from_documents(documents, self.embeddings)
        store.save_local(str(self.persist_path))
        self.vector_store = store
        return store

    def load(self):
        self.vector_store = FAISS.load_local(
            str(self.persist_path),
            self.embeddings,
            allow_dangerous_deserialization=True,
        )
        return self.vector_store
