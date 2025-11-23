from __future__ import annotations

import json
import sys
from pathlib import Path

import requests
import streamlit as st
import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components import api_client
from frontend.components.layout import render_page_header

CONFIG_PATH = Path("configs/config.yaml")
EXAMPLE_PATH = Path("configs/config.example.yaml")
REPORT_PATH = Path("evaluation/reports/latest.json")


def _load_config() -> tuple[dict, Path]:
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data, path


def _persist_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def render():
    render_page_header(
        "System Settings",
        "Configure API access, models, retrieval strategies, and vector stores while monitoring evaluation and health status.",
        highlight="⚙️",
    )

    config_data, config_path = _load_config()
    st.info(f"Active configuration file: {config_path}")

    st.subheader("API basics")
    api_base = st.text_input("API base URL", value=st.session_state.get("api_base", "http://localhost:8000"))
    if st.button("Save API base URL"):
        st.session_state["api_base"] = api_base
        api_client.set_api_base(api_base)
        st.success("API base URL saved.")

    st.subheader("Models & embeddings")
    with st.form("model-form"):
        model_cfg = config_data.get("model", {})
        llm_model = st.text_input("LLM model", value=model_cfg.get("llm", "gpt-4o"))
        embedding_model = st.text_input("Embedding model", value=model_cfg.get("embedding", "bge-large"))
        temperature = st.slider("Temperature", 0.0, 1.0, float(model_cfg.get("temperature", 0.15)), 0.05)
        azure_endpoint = st.text_input("Azure Endpoint", value=model_cfg.get("azure_endpoint", ""))
        azure_api_version = st.text_input("Azure API Version", value=model_cfg.get("azure_api_version", "2024-02-15-preview"))
        azure_chat = st.text_input("Azure Chat Deployment", value=model_cfg.get("azure_chat_deployment", ""))
        azure_embed = st.text_input(
            "Azure Embedding Deployment",
            value=model_cfg.get("azure_embedding_deployment", ""),
        )
        submitted = st.form_submit_button("Save model configuration")
        if submitted:
            config_data.setdefault("model", {})
            config_data["model"].update(
                {
                    "llm": llm_model,
                    "embedding": embedding_model,
                    "temperature": temperature,
                    "azure_endpoint": azure_endpoint or None,
                    "azure_api_version": azure_api_version or None,
                    "azure_chat_deployment": azure_chat or None,
                    "azure_embedding_deployment": azure_embed or None,
                }
            )
            _persist_config(config_data)
            st.success("Model configuration updated.")

    st.subheader("Retrieval & reranker")
    strategies = ["vector", "bm25", "hybrid", "router"]
    retrieval_cfg = config_data.get("retrieval", {})
    default_strategy = retrieval_cfg.get("strategy", "hybrid")
    if default_strategy not in strategies:
        default_strategy = "hybrid"
    with st.form("retrieval-form"):
        strategy = st.selectbox("Default retrieval strategy", strategies, index=strategies.index(default_strategy))
        reranker_model = st.text_input("Reranker model (optional)", value=retrieval_cfg.get("reranker", ""))
        reranker_top_k = st.slider("Reranker Top K", 1, 10, int(retrieval_cfg.get("reranker_top_k", 4)))
        router_enabled = st.toggle("Enable Router RAG", value=retrieval_cfg.get("router_enabled", True))
        submitted = st.form_submit_button("Save retrieval configuration")
        if submitted:
            config_data.setdefault("retrieval", {})
            config_data["retrieval"].update(
                {
                    "strategy": strategy,
                    "reranker": reranker_model or None,
                    "reranker_top_k": reranker_top_k,
                    "router_enabled": router_enabled,
                }
            )
            _persist_config(config_data)
            st.success("Retrieval configuration updated.")

    st.subheader("Vector store")
    stores = ["chroma", "faiss", "qdrant"]
    store_cfg = config_data.get("vector_store", {})
    default_store = store_cfg.get("type", "chroma")
    if default_store not in stores:
        default_store = "chroma"
    with st.form("vector-form"):
        store_type = st.selectbox("Type", stores, index=stores.index(default_store))
        persist_path = st.text_input("Persist path", value=store_cfg.get("persist_path", "./data/vectorstores/default"))
        collection_name = st.text_input("Collection name", value=store_cfg.get("collection_name", "langchain_rag"))
        host = st.text_input("Host (Qdrant)", value=store_cfg.get("host", ""))
        port = st.number_input("Port (Qdrant)", value=store_cfg.get("port", 6333), step=1)
        submitted = st.form_submit_button("Save vector store configuration")
        if submitted:
            config_data.setdefault("vector_store", {})
            config_data["vector_store"].update(
                {
                    "type": store_type,
                    "persist_path": persist_path,
                    "collection_name": collection_name,
                    "host": host or None,
                    "port": int(port) if port else None,
                }
            )
            _persist_config(config_data)
            st.success("Vector store configuration updated.")

    st.subheader("Environment variable hints (Azure)")
    st.code(
        "\n".join(
            [
                "AZURE_OPENAI_API_KEY=...",
                "AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com",
                "AZURE_OPENAI_API_VERSION=2024-02-15-preview",
                "AZURE_OPENAI_CHAT_DEPLOYMENT=gpt4o-chat",
                "AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-large",
            ]
        ),
        language="bash",
    )

    st.subheader("Configuration preview")
    st.code(yaml.safe_dump(config_data, sort_keys=False, allow_unicode=True), language="yaml")

    st.subheader("Evaluation results (ragas)")
    if REPORT_PATH.exists():
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        metrics = report.get("results", report)
        if isinstance(metrics, dict):
            cols = st.columns(len(metrics))
            for col, (metric, value) in zip(cols, metrics.items()):
                display = f"{value:.3f}" if isinstance(value, (int, float)) else value
                col.metric(metric, display)
        st.code(json.dumps(report, indent=2, ensure_ascii=False), language="json")
    else:
        st.info("Run `python scripts/evaluate.py` to generate an evaluation report.")

    st.subheader("Debug tools")
    if st.button("Run health check"):
        try:
            response = requests.get(f"{api_base}/health", timeout=15)
            st.json(response.json())
        except requests.RequestException as exc:
            st.error(f"Health check failed: {exc}")

    st.subheader("Logging tips")
    st.markdown(
        "- Backend logs: check the `uvicorn` console output\n"
        "- Streamlit logs: view terminal output or `.streamlit/logs`"
    )

if __name__ == "__main__":
    render()
