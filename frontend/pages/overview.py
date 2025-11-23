from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components import api_client
from frontend.components.layout import render_page_header


def _navigate(target: str) -> None:
    st.session_state["nav_redirect"] = target
    st.rerun()


def _fetch_health() -> Dict[str, Any]:
    try:
        return api_client.health()
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Unable to reach backend: {exc}")
        return {
            "documents_indexed": 0,
            "vector_store_ready": False,
            "pending_jobs": 0,
            "model": "unknown",
            "uptime": "-",
        }


def _kpi_card(label: str, value: str | int, badge: str | None = None, accent: str = "#4b6bfb") -> None:
    st.markdown(
        f"""
        <div class='neo-card'>
            <div class='neo-card-label'>{label}</div>
            <div class='neo-card-value' style='color:{accent}'>{value}</div>
            {f"<span class='neo-chip'>{badge}</span>" if badge else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    render_page_header(
        "RAG Command Center",
        "Monitor the vector knowledge base, conversations, and evaluation results like a production-ready RAG pipeline.",
        highlight="🧠",
    )

    health = _fetch_health()

    col1, col2, col3, col4 = st.columns(4)
    _kpi_card("Indexed documents", health.get("documents_indexed", 0), "docs")
    _kpi_card("Vector store status", "ONLINE" if health.get("vector_store_ready") else "PENDING", accent="#00f5d4")
    _kpi_card("Queued jobs", health.get("pending_jobs", 0), accent="#ffd166")
    _kpi_card("Model", health.get("model", "gpt-4o"), accent="#f15bb5")

    st.markdown("---")

    st.subheader("Quick actions")
    quick_cols = st.columns(3)

    if quick_cols[0].button("⚙️ Build knowledge base", use_container_width=True):
        _navigate("build")
    if quick_cols[1].button("💬 Open Q&A", use_container_width=True):
        _navigate("chat")
    if quick_cols[2].button("📊 View evaluations", use_container_width=True):
        _navigate("evaluation")

    st.markdown("---")

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown("#### Architecture pulse")
        st.markdown(
            """
            <div class='neo-stack'>
                <div>
                    <h4>📡 Data ingestion</h4>
                    <p>Recursive / semantic / table chunking keeps long documents structured.</p>
                </div>
                <div>
                    <h4>🔎 Retrieval strategies</h4>
                    <p>Vector · BM25 · Hybrid · Router RAG automatically routes based on business intent.</p>
                </div>
                <div>
                    <h4>🧪 Evaluation loop</h4>
                    <p>ragas metrics and a nightly runner keep KPIs visible, tunable, and reproducible.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown("#### Build timeline")
        timeline = [
            ("Knowledge base initialized", "docs uploaded", "#4b6bfb"),
            ("RAG tuning", "router + reranker", "#00f5d4"),
            ("Evaluation loop", "ragas nightly", "#ffd166"),
        ]
        for title, desc, color in timeline:
            st.markdown(
                f"""
                <div class='neo-timeline'>
                    <span class='neo-dot' style='background:{color}'></span>
                    <div>
                        <strong>{title}</strong><br/>
                        <span>{desc}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.caption(f"Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    st.markdown("---")

    st.subheader("Suggested next steps")
    st.markdown(
        """
        - ✅ Upload your organization knowledge base and complete the first build
        - ✅ Configure the reranker and router in Settings
        - 🔄 Run `scripts/nightly_eval.py` to establish an evaluation baseline
        - 🔜 Add CI and monitoring to unlock production readiness
        """
    )

if __name__ == "__main__":
    render()
