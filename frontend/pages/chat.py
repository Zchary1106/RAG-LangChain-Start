from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components import api_client
from frontend.components.layout import render_page_header


def render():
    render_page_header(
        "Retrieval Lab",
        "Instant Q&A with retrieved context analysis to validate retrieval strategies.",
        highlight="💬",
    )
    strategy = st.selectbox("Retrieval strategy", ["auto", "vector", "bm25", "hybrid", "router"], index=0)
    chain_type = st.selectbox("RAG chain type", ["standard", "compression", "map_reduce", "router"], index=0)
    col1, col2 = st.columns([1, 1])
    top_k = col1.slider("Top K", min_value=1, max_value=10, value=4)
    rerank_hint = col2.toggle("Show chunk metadata", value=True)
    streaming_enabled = st.toggle("Enable streaming answers", value=True)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    question = st.text_area("Ask your question", height=120, placeholder="For example: What is RAG?")
    if st.button("Ask", type="primary"):
        if not question.strip():
            st.warning("Please enter a question")
        else:
            resolved_strategy = None if strategy == "auto" else strategy
            status_placeholder = st.empty() if streaming_enabled else None
            answer_placeholder = st.empty() if streaming_enabled else None
            try:
                if streaming_enabled:
                    assert answer_placeholder is not None  # narrow type for mypy
                    status_placeholder.info("Streaming answer in progress…")
                    streamed_text = ""
                    final_payload = None
                    for event in api_client.query_stream(
                        question=question,
                        strategy=resolved_strategy,
                        chain_type=chain_type,
                        top_k=top_k,
                    ):
                        event_type = event.get("type")
                        if event_type == "token":
                            streamed_text += event.get("content", "")
                            answer_placeholder.markdown(streamed_text or "\u200b")
                        elif event_type == "result":
                            final_payload = event
                        elif event_type == "error":
                            raise RuntimeError(event.get("message", "Streaming error"))
                    if final_payload is None:
                        raise RuntimeError("Streaming API did not return a final result")
                    final_answer = final_payload.get("answer", streamed_text)
                    answer_placeholder.markdown(final_answer or "\u200b")
                    st.session_state["chat_history"].append(
                        {
                            "question": question,
                            "answer": final_answer,
                            "chunks": final_payload.get("chunks", []),
                            "strategy": final_payload.get("strategy", strategy),
                            "chain": final_payload.get("chain_type", chain_type),
                        }
                    )
                    status_placeholder.success("Generation complete")
                else:
                    with st.spinner("Fetching answer..."):
                        response = api_client.query(
                            question=question,
                            strategy=resolved_strategy,
                            chain_type=chain_type,
                            top_k=top_k,
                        )
                    st.session_state["chat_history"].append(
                        {
                            "question": question,
                            "answer": response["answer"],
                            "chunks": response.get("chunks", []),
                            "strategy": response.get("strategy", strategy),
                            "chain": response.get("chain_type", chain_type),
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                if status_placeholder is not None:
                    status_placeholder.error("Generation failed")
                st.error(f"Query failed: {exc}")

    history = st.session_state["chat_history"]
    if not history:
        st.info("Ask a question to see answers and retrieved context.")
        return

    tab_conv, tab_context = st.tabs(["Conversation", "Retrieved context"])

    with tab_conv:
        for turn in reversed(history):
            with st.chat_message("user"):
                st.write(turn["question"])
            with st.chat_message("assistant"):
                st.write(turn["answer"])
                st.caption(f"Strategy: {turn.get('strategy')} · Chain: {turn.get('chain')}")

    with tab_context:
        options = list(range(len(history)))
        selection = st.selectbox(
            "Select a turn to inspect",
            options=options,
            format_func=lambda idx: f"Q{idx + 1}: {history[idx]['question'][:30]}...",
        )
        selected_turn = history[selection]
        chunks = selected_turn.get("chunks", [])
        st.markdown(
            f"**Strategy**: {selected_turn.get('strategy')}  |  **Chain**: {selected_turn.get('chain')}  |  **Chunks**: {len(chunks)}"
        )
        if not chunks:
            st.caption("No retrieved chunks for this turn.")
        else:
            for idx, chunk in enumerate(chunks, start=1):
                score = chunk.get("score", 0.0)
                meta = chunk.get("metadata", {})
                st.markdown(
                    f"""
                    <div class='rag-card'>
                        <div>
                            <span class='rag-chip'>Chunk {idx}</span>
                            <span class='rag-chip'>score {score:.2f}</span>
                            <span class='rag-chip'>{meta.get('source', 'unknown')}</span>
                        </div>
                        <p>{chunk.get('content', '').strip()}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if rerank_hint and meta:
                    st.caption(meta)


if __name__ == "__main__":
    render()
