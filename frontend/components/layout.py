from __future__ import annotations

import streamlit as st


def render_page_header(
    title: str,
    subtitle: str,
    *,
    kicker: str = "LangChain · FastAPI · Streamlit",
    highlight: str | None = None,
) -> None:
    """Render a shared neon hero banner used across all pages."""

    highlight_html = f"<div class='neo-hero-icon'>{highlight}</div>" if highlight else ""
    st.markdown(
        f"""
        <div class='neo-hero'>
            <div>
                <p class='neo-kicker'>{kicker}</p>
                <h1>{title}</h1>
                <p class='neo-subtitle'>{subtitle}</p>
            </div>
            <div class='neo-hero-radial'>
                <div class='neo-glow'></div>
                {highlight_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
