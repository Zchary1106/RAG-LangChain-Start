from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Literal, Optional

from dotenv import load_dotenv
import yaml
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
DEFAULT_CONFIG_PATH = ROOT_DIR / "configs" / "config.yaml"
EXAMPLE_CONFIG_PATH = ROOT_DIR / "configs" / "config.example.yaml"


class ModelConfig(BaseModel):
    llm: str = Field(default="gpt-4o")
    embedding: str = Field(default="bge-large")
    temperature: float = Field(default=0.1)
    azure_endpoint: Optional[str] = None
    azure_api_version: Optional[str] = None
    azure_chat_deployment: Optional[str] = None
    azure_embedding_deployment: Optional[str] = None


class ChunkingConfig(BaseModel):
    type: Literal["recursive", "semantic", "table"] = "recursive"
    size: int = 500
    overlap: int = 100


class VectorStoreConfig(BaseModel):
    type: Literal["chroma", "faiss", "qdrant"] = "chroma"
    persist_path: str = "./data/vectorstores/default"
    collection_name: str = "langchain_rag"
    host: Optional[str] = None
    port: Optional[int] = None
    api_key: Optional[str] = None


class RetrievalConfig(BaseModel):
    strategy: Literal["vector", "bm25", "hybrid", "router"] = "vector"
    top_k: int = 4
    reranker: Optional[str] = None
    reranker_top_k: int = 4
    router_enabled: bool = True


class RouterRule(BaseModel):
    name: str
    keywords: List[str] = Field(default_factory=list)
    strategy: Literal["vector", "bm25", "hybrid"] = "vector"
    chain: Literal["standard", "map_reduce", "compression"] = "standard"


class PathConfig(BaseModel):
    upload_dir: str = "./data/uploads"
    tmp_dir: str = "./data/tmp"


class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class StreamlitConfig(BaseModel):
    port: int = 8501
    api_base: str = "http://localhost:8000"


class EvaluationConfig(BaseModel):
    dataset_path: str = "./evaluation/datasets/questions.json"
    output_dir: str = "./evaluation/reports"


class Settings(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    streamlit: StreamlitConfig = Field(default_factory=StreamlitConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    router_rules: List[RouterRule] = Field(
        default_factory=lambda: [
            RouterRule(name="code", keywords=["code", "function", "api", "error"], strategy="bm25", chain="map_reduce"),
            RouterRule(name="business", keywords=["business", "marketing", "product", "sales"], strategy="hybrid", chain="standard"),
        ]
    )

    @property
    def upload_path(self) -> Path:
        return (ROOT_DIR / self.paths.upload_dir).resolve()

    @property
    def vector_store_path(self) -> Path:
        return (ROOT_DIR / self.vector_store.persist_path).resolve()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_settings(config_path: Optional[Path] = None) -> Settings:
    path = config_path or Path(os.getenv("RAG_CONFIG_PATH", DEFAULT_CONFIG_PATH))
    example_data = _load_yaml(EXAMPLE_CONFIG_PATH)
    primary_data = _load_yaml(path)
    data = _merge_dicts(example_data, primary_data)
    return Settings(**data)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()


__all__: List[str] = [
    "Settings",
    "ModelConfig",
    "ChunkingConfig",
    "VectorStoreConfig",
    "RetrievalConfig",
    "PathConfig",
    "APIConfig",
    "StreamlitConfig",
    "EvaluationConfig",
    "RouterRule",
    "get_settings",
]
