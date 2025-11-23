from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.documents import Document

from backend.config.settings import ChunkingConfig, get_settings
from backend.core.file_utils import cleanup_files, save_upload
from backend.core.logger import get_logger
from backend.models.schemas import (
    BuildRequest,
    BuildResponse,
    HealthResponse,
    JobResponse,
    QueryRequest,
    QueryResponse,
    RetrievedChunk,
)
from backend.services.document_processor import DocumentProcessor
from backend.services.job_manager import job_manager
from backend.services.rag_service import RAGService
from backend.services.vector_store_service import VectorStoreService

logger = get_logger(__name__)
settings = get_settings()
app = FastAPI(title="LangChain RAG Starter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_service = VectorStoreService(settings)
rag_service = RAGService(vector_service, settings)


def _format_chunks(docs: List[Document]):
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(doc.metadata.get("score", 0.0)),
        }
        for doc in docs
    ]


def get_processor(req: BuildRequest) -> DocumentProcessor:
    chunk_cfg = ChunkingConfig(
        type=req.strategy or settings.chunking.type,
        size=req.chunk_size or settings.chunking.size,
        overlap=req.chunk_overlap or settings.chunking.overlap,
    )
    return DocumentProcessor(chunk_cfg)


@app.post("/build", response_model=BuildResponse)
async def build_knowledge_base(
    chunk_size: int | None = Form(default=None),
    chunk_overlap: int | None = Form(default=None),
    strategy: str | None = Form(default=None),
    vector_store_type: str | None = Form(default=None),
    files: List[UploadFile] = File(...),
):
    build_request = BuildRequest(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=strategy,
        vector_store_type=vector_store_type,
    )
    if not files:
        raise HTTPException(status_code=400, detail="At least one document is required")
    job = job_manager.create_job("build", metadata={"files": [file.filename for file in files]})
    saved_paths: List[Path] = []
    try:
        for file in files:
            saved_paths.append(save_upload(file))
        processor = get_processor(build_request)
        docs = processor.load_documents(saved_paths)
        if not docs:
            raise HTTPException(status_code=400, detail="No supported documents uploaded")
        job_manager.update_job(job.job_id, "running", message="Chunking documents")
        if build_request.vector_store_type:
            vector_service.switch_store(build_request.vector_store_type)
        chunks = processor.chunk_documents(docs)
        job_manager.update_job(job.job_id, "running", message="Building vector store", metadata={"chunks": len(chunks)})
        vector_service.build_store(chunks)
        job_manager.update_job(
            job.job_id,
            "completed",
            message="Build completed",
            metadata={
                "documents": len(docs),
                "vector_store": settings.vector_store.type,
            },
        )
        return BuildResponse(
            job_id=job.job_id,
            documents_indexed=len(docs),
            chunks_created=len(chunks),
            vector_store=settings.vector_store.type,
            status="completed",
        )
    except Exception as exc:  # noqa: BLE001
        job_manager.update_job(job.job_id, "failed", message=str(exc))
        raise
    finally:
        cleanup_files(saved_paths)


@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    if not vector_service.has_index():
        raise HTTPException(status_code=400, detail="Vector store is empty. Build an index first.")
    answer, docs, used_strategy, used_chain = rag_service.generate_answer(
        question=request.question,
        retrieval_strategy=request.retrieval_strategy,
        chain_type=request.chain_type or "standard",
        top_k=request.top_k,
    )
    chunks = [
        RetrievedChunk(
            content=doc.page_content,
            metadata=doc.metadata,
            score=doc.metadata.get("score", 0.0),
        )
        for doc in docs
    ]
    return QueryResponse(
        answer=answer,
        strategy=used_strategy,
        chain_type=used_chain,
        chunks=chunks,
    )


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/query/stream")
async def stream_query(request: QueryRequest):
    if not vector_service.has_index():
        raise HTTPException(status_code=400, detail="Vector store is empty. Build an index first.")

    handler, task, strategy, used_chain, should_stream = rag_service.stream_answer(
        question=request.question,
        retrieval_strategy=request.retrieval_strategy,
        chain_type=request.chain_type or "standard",
        top_k=request.top_k,
    )

    async def event_generator():
        try:
            if should_stream:
                async for token in handler.aiter():
                    yield _sse({"type": "token", "content": token})
            result = await task
            docs: List[Document] = result.get("source_documents", [])
            payload = {
                "type": "result",
                "answer": result.get("result", ""),
                "strategy": strategy,
                "chain_type": used_chain,
                "chunks": _format_chunks(docs),
            }
            yield _sse(payload)
            yield "data: [DONE]\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Streaming query failed")
            yield _sse({"type": "error", "message": str(exc)})
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if should_stream:
                handler.done()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    ready = vector_service.has_index()
    doc_count = len(vector_service.documents)
    status = "ok" if ready else "bootstrap"
    pending = job_manager.pending_jobs()
    return HealthResponse(status=status, vector_store_ready=ready, documents_indexed=doc_count, pending_jobs=pending)


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    record = job_manager.get_job(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        job_id=record.job_id,
        job_type=record.job_type,
        status=record.status,
        message=record.message,
        created_at=record.created_at,
        updated_at=record.updated_at,
        metadata=record.metadata,
    )
