from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, validator


class BuildRequest(BaseModel):
    chunk_size: Optional[int] = Field(default=None, ge=100, le=2000)
    chunk_overlap: Optional[int] = Field(default=None, ge=0, le=500)
    strategy: Optional[str] = Field(default=None, description="Chunking strategy override")
    vector_store_type: Optional[str] = Field(default=None, description="Override vector store adapter")


class BuildResponse(BaseModel):
    job_id: str
    documents_indexed: int
    chunks_created: int
    vector_store: str
    status: str = "completed"


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    retrieval_strategy: Optional[str] = Field(default=None)
    chain_type: Optional[str] = Field(default="standard")
    top_k: Optional[int] = Field(default=None, ge=1, le=10)

    @validator("question")
    def question_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value


class RetrievedChunk(BaseModel):
    content: str
    score: float = 0.0
    metadata: dict = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    strategy: str
    chain_type: str
    chunks: List[RetrievedChunk] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    vector_store_ready: bool
    documents_indexed: int
    pending_jobs: int = 0


class JobResponse(BaseModel):
    job_id: str
    job_type: str
    status: str
    message: str
    created_at: float
    updated_at: float
    metadata: dict = Field(default_factory=dict)
