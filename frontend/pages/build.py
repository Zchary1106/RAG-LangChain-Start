from __future__ import annotations

from datetime import datetime
import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components import api_client
from frontend.components.layout import render_page_header


VECTOR_STORE_OPTIONS = [
    {"label": "Chroma (Local)", "value": "chroma"},
    {"label": "FAISS (In-memory)", "value": "faiss"},
    {"label": "Qdrant (Service)", "value": "qdrant"},
]


def _append_log(stage: str, message: str) -> None:
    logs = st.session_state.setdefault("build_logs", [])
    logs.append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "stage": stage,
        "message": message,
    })


def render():
    render_page_header(
        "Build Hub",
        "Upload documents, choose a vector store, and track progress in real time.",
        highlight="🧱",
    )
    st.markdown(
        """
        <div class='rag-flow-grid'>
            <div class='rag-flow-step'>
                <span>UPLOAD</span>
                <strong>1 · Ingest documents</strong>
                <p>Supports PDF / DOCX / Markdown / TXT and auto-detects metadata.</p>
            </div>
            <div class='rag-flow-step'>
                <span>CHUNK</span>
                <strong>2 · Smart chunking</strong>
                <p>Recursive / Semantic / Table strategies cover most scenarios.</p>
            </div>
            <div class='rag-flow-step'>
                <span>INDEX</span>
                <strong>3 · Vector indexing</strong>
                <p>Switch between Chroma / FAISS / Qdrant and review recent jobs.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "health" not in st.session_state:
        st.session_state["health"] = api_client.health()
    if "last_job" not in st.session_state:
        st.session_state["last_job"] = None
    st.session_state.setdefault("build_logs", [])

    with st.expander("Current service status", expanded=True):
        cols = st.columns(3)
        health_state = st.session_state.get("health")
        cols[0].metric("Indexed documents", health_state.get("documents_indexed", 0))
        cols[1].metric("Vector store ready", "✅" if health_state.get("vector_store_ready") else "⌛")
        cols[2].metric("Queued jobs", health_state.get("pending_jobs", 0))
        if st.button("Refresh health status", key="refresh-health"):
            st.session_state["health"] = api_client.health()
            health_state = st.session_state["health"]
        st.json(health_state)

    with st.form("build-form"):
        uploaded_files = st.file_uploader(
            "Upload PDF / Word / Markdown / TXT",
            type=["pdf", "docx", "md", "txt"],
            accept_multiple_files=True,
        )
        if uploaded_files:
            st.dataframe(
                [{"Filename": f.name, "Size (KB)": round((f.size or 0) / 1024, 1)} for f in uploaded_files],
                use_container_width=True,
            )
        c1, c2, c3 = st.columns(3)
        chunk_size = c1.number_input("Chunk Size", min_value=100, max_value=2000, value=500, step=50)
        chunk_overlap = c2.number_input("Chunk Overlap", min_value=0, max_value=500, value=100, step=10)
        strategy = c3.selectbox("Chunk Strategy", ["recursive", "semantic", "table"], index=0)
        vector_store_label = st.selectbox(
            "Vector store target",
            [opt["label"] for opt in VECTOR_STORE_OPTIONS],
            index=0,
        )
        vector_store_value = next(opt["value"] for opt in VECTOR_STORE_OPTIONS if opt["label"] == vector_store_label)
        submit = st.form_submit_button("Start build", use_container_width=True)

    if submit:
        if not uploaded_files:
            st.warning("Please upload at least one file.")
        else:
            files_bytes = [file.getvalue() for file in uploaded_files]
            filenames = [file.name for file in uploaded_files]
            payload = {
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "strategy": strategy,
                "vector_store_type": vector_store_value,
            }
            progress_bar = st.progress(0)
            _append_log("upload", f"Received {len(files_bytes)} files")
            with st.status("Preparing upload", expanded=True) as status:
                status.update(label="Uploading and building...", state="running")
                try:
                    progress_bar.progress(25)
                    _append_log("chunk", "Starting document chunking")
                    response = api_client.build_index(files_bytes, filenames, payload)
                    progress_bar.progress(70)
                    job = api_client.get_job(response["job_id"])
                    st.session_state["last_job"] = job
                    st.session_state["health"] = api_client.health()
                    progress_bar.progress(100)
                    status.update(label="Build complete", state="complete")
                    st.success(f"Vector store {job['metadata'].get('vector_store', vector_store_value)} updated")
                    _append_log("vector", f"Build finished: {job['job_id']}")
                except Exception as exc:  # noqa: BLE001
                    status.update(label="Build failed", state="error")
                    st.error(f"Build failed: {exc}")
                    _append_log("error", str(exc))
                finally:
                    progress_bar.empty()

    last_job = st.session_state.get("last_job")
    if last_job:
        st.subheader("Most recent job")
        cols = st.columns(3)
        cols[0].metric("Job ID", last_job["job_id"])
        cols[1].metric("Status", last_job["status"])
        cols[2].metric("Documents", last_job.get("metadata", {}).get("documents", 0))
        if st.button("Refresh job status", key="refresh-job"):
            try:
                st.session_state["last_job"] = api_client.get_job(last_job["job_id"])
                last_job = st.session_state["last_job"]
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Unable to refresh job: {exc}")
        st.json(last_job)

    with st.expander("Build logs", expanded=False):
        logs = st.session_state.get("build_logs", [])
        if not logs:
            st.caption("No logs yet")
        else:
            for log in reversed(logs[-20:]):
                st.markdown(
                    f"<div class='rag-card'><span class='rag-chip'>{log['ts']}</span>"
                    f"<strong>{log['stage'].upper()}</strong> · {log['message']}</div>",
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    render()
