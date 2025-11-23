from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List

import docx2txt
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from markdown import markdown
from pdfminer.high_level import extract_text as pdf_extract_text

from backend.config.settings import ChunkingConfig, get_settings
from backend.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}


class DocumentProcessor:
    def __init__(self, chunking_override: ChunkingConfig | None = None) -> None:
        self.chunking_cfg = chunking_override or settings.chunking

    def load_documents(self, file_paths: Iterable[Path]) -> List[Document]:
        documents: List[Document] = []
        for path in file_paths:
            ext = path.suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                logger.warning("Skipping unsupported file: %s", path)
                continue
            text = self._read_file(path)
            metadata = {"source": str(path)}
            documents.append(Document(page_content=text, metadata=metadata))
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunk_type = self.chunking_cfg.type
        if chunk_type == "semantic":
            chunks = self._semantic_chunk(documents)
        elif chunk_type == "table":
            chunks = self._table_aware_chunk(documents)
        else:
            chunks = self._recursive_chunk(documents)
        logger.info("Chunked %s documents into %s chunks", len(documents), len(chunks))
        return chunks

    def _recursive_chunk(self, documents: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunking_cfg.size,
            chunk_overlap=self.chunking_cfg.overlap,
            separators=["\n\n", "\n", "。", "，", " "],
        )
        return splitter.split_documents(documents)

    def _semantic_chunk(self, documents: List[Document]) -> List[Document]:
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ]
        )
        semantic_chunks: List[Document] = []
        for doc in documents:
            if doc.metadata.get("source", "").lower().endswith(".md"):
                splits = header_splitter.split_text(doc.page_content)
                for split in splits:
                    meta = {**doc.metadata, **split.metadata}
                    semantic_chunks.append(Document(page_content=split.page_content, metadata=meta))
            else:
                semantic_chunks.extend(self._recursive_chunk([doc]))
        return semantic_chunks

    def _table_aware_chunk(self, documents: List[Document]) -> List[Document]:
        table_pattern = re.compile(r"((?:^\|.*\|\s*$\n){2,})", re.MULTILINE)
        chunked: List[Document] = []
        for doc in documents:
            text = doc.page_content
            tables = table_pattern.findall(text)
            remaining = table_pattern.sub("", text)
            for table in tables:
                chunked.append(Document(page_content=table.strip(), metadata={**doc.metadata, "table": True}))
            chunked.extend(self._recursive_chunk([Document(page_content=remaining, metadata=doc.metadata)]))
        return chunked

    def _read_file(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext == ".pdf":
            return pdf_extract_text(str(path))
        if ext == ".docx":
            return docx2txt.process(str(path)) or ""
        text = path.read_text(encoding="utf-8", errors="ignore")
        if ext == ".md":
            # Convert Markdown to HTML, then strip tags naively
            html = markdown(text)
            return self._strip_html_tags(html)
        return text

    @staticmethod
    def _strip_html_tags(html: str) -> str:
        in_tag = False
        buffer: list[str] = []
        for char in html:
            if char == "<":
                in_tag = True
                continue
            if char == ">":
                in_tag = False
                continue
            if not in_tag:
                buffer.append(char)
        return "".join(buffer)
