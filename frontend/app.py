from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.theme import inject_theme  # noqa: E402
from frontend.pages import build, chat, evaluation, overview, settings  # noqa: E402

NAV_ITEMS = [
    {"key": "overview", "label": "Overview", "icon": "🏠", "section": "Overview", "render": overview.render, "description": "Metrics and action dashboard"},
    {"key": "build", "label": "Build Hub", "icon": "🧱", "section": "Build Hub", "render": build.render, "description": "Upload · Chunk · Index"},
    {"key": "chat", "label": "Retrieval Lab", "icon": "💬", "section": "Retrieval Lab", "render": chat.render, "description": "Conversational retrieval and debugging"},
    {"key": "evaluation", "label": "Evaluation Bench", "icon": "📊", "section": "Evaluation Bench", "render": evaluation.render, "description": "ragas metrics and trends"},
    {"key": "settings", "label": "System Settings", "icon": "⚙️", "section": "System Settings", "render": settings.render, "description": "Model and vector store configuration"},
]

NAV_SECTIONS = [
    {"title": "Overview", "caption": "Command center", "keys": ["overview"]},
    {"title": "Build Hub", "caption": "Upload · Chunk · Index", "keys": ["build"]},
    {"title": "Retrieval Lab", "caption": "QA experience and chunks", "keys": ["chat"]},
    {"title": "Evaluation Bench", "caption": "ragas metrics", "keys": ["evaluation"]},
    {"title": "System Settings", "caption": "Models / Storage / API", "keys": ["settings"]},
]

PAGE_MAP = {item["key"]: item for item in NAV_ITEMS}


def _default_route() -> str:
    return NAV_ITEMS[0]["key"]


def _render_sidebar(nav_route: str) -> None:
    current = PAGE_MAP.get(nav_route, NAV_ITEMS[0])
    st.sidebar.markdown(
        f"""
        <div class='rag-sidebar-title'>
            <div class='feature-label'>Current module</div>
            <div class='feature-name'>{current['label']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")
    for section in NAV_SECTIONS:
        st.sidebar.markdown(f"<div class='rag-sidebar-section'>{section['title']}</div>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<div class='rag-section-caption'>{section['caption']}</div>", unsafe_allow_html=True)
        for key in section["keys"]:
            item = PAGE_MAP[key]
            is_active = nav_route == key
            clicked = st.sidebar.button(
                f"{item['icon']} {item['label']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
                key=f"nav-btn-{key}",
                help=item.get("description"),
            )
            if clicked and not is_active:
                st.session_state["nav_route"] = key
                st.rerun()


st.set_page_config(page_title="LangChain RAG Starter", layout="wide", page_icon="🧠")
inject_theme()
if "nav_route" not in st.session_state:
    st.session_state["nav_route"] = _default_route()
if "nav_redirect" in st.session_state:
    target = st.session_state.pop("nav_redirect")
    if target in PAGE_MAP:
        st.session_state["nav_route"] = target

current_route = st.session_state["nav_route"]
if current_route not in PAGE_MAP:
    current_route = _default_route()
    st.session_state["nav_route"] = current_route

_render_sidebar(current_route)
PAGE_MAP[current_route]["render"]()
