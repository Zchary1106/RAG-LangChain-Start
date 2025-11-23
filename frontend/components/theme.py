from __future__ import annotations

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
        :root {
            --rag-bg: #f5f7fb;
            --rag-bg-radial: radial-gradient(circle at 10% 10%, rgba(37, 99, 235, 0.12), transparent 40%),
                              radial-gradient(circle at 80% 0%, rgba(236, 72, 153, 0.15), transparent 38%),
                              #f5f7fb;
            --rag-surface: #ffffff;
            --rag-surface-alt: #fdf2ff;
            --rag-border: rgba(15, 23, 42, 0.08);
            --rag-primary: #2563eb;
            --rag-accent: #7c3aed;
            --rag-success: #15803d;
            --rag-warning: #b45309;
            --rag-danger: #dc2626;
            --rag-text: #0f172a;
            --rag-muted: #64748b;
        }
        body, .stApp {
            background: var(--rag-bg-radial);
            color: var(--rag-text);
            font-family: 'Space Grotesk', 'Segoe UI', system-ui;
        }
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(18px);
            border-right: 1px solid var(--rag-border);
            box-shadow: 8px 0 25px rgba(15, 23, 42, 0.08);
        }
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        [data-testid="stSidebar"] .rag-sidebar-title {
            padding: 1.2rem 1rem 0.6rem;
            border-bottom: 1px solid rgba(15, 23, 42, 0.08);
            margin-bottom: 0.6rem;
        }
        [data-testid="stSidebar"] .rag-sidebar-title .feature-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.32em;
            color: var(--rag-muted);
            margin-bottom: 0.2rem;
        }
        [data-testid="stSidebar"] .rag-sidebar-title .feature-name {
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--rag-text);
        }
        [data-testid="stSidebar"] .sidebar-content {
            padding-top: 1rem;
        }
        h1, h2, h3, h4, h5 {
            letter-spacing: 0.01em;
            color: var(--rag-text);
        }
        h1 span.gradient,
        h2 span.gradient {
            background: linear-gradient(120deg, var(--rag-primary), var(--rag-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .rag-card {
            border-radius: 16px;
            padding: 1.1rem 1.4rem;
            background: var(--rag-surface);
            border: 1px solid var(--rag-border);
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(6px);
        }
        .rag-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.15rem 0.8rem;
            border-radius: 999px;
            background: rgba(37, 99, 235, 0.08);
            color: var(--rag-primary);
            font-size: 0.75rem;
            margin-right: 6px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .rag-tag-warning {
            background: rgba(250, 204, 21, 0.18);
            color: var(--rag-warning);
        }
        .neo-hero {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 2.6rem;
            border-radius: 28px;
            background: linear-gradient(140deg, #eef2ff, #fdeffb);
            border: 1px solid rgba(59, 130, 246, 0.18);
            box-shadow: 0 25px 70px rgba(148, 163, 184, 0.35);
            margin-bottom: 1.8rem;
        }
        .neo-hero-radial {
            position: relative;
            width: 230px;
            height: 230px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(59,130,246,0.18), rgba(248,250,252,0.8));
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .neo-glow {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: rgba(236, 72, 153, 0.45);
            filter: blur(46px);
            animation: pulse-glow 6s ease-in-out infinite;
        }
        .neo-hero-icon {
            position: absolute;
            font-size: 2.8rem;
            color: rgba(15, 23, 42, 0.7);
            text-shadow: 0 0 25px rgba(37,99,235,0.35);
        }
        @keyframes pulse-glow {
            0% {transform: scale(0.85); opacity: 0.5;}
            50% {transform: scale(1.15); opacity: 1;}
            100% {transform: scale(0.85); opacity: 0.5;}
        }
        .neo-hero h1 {
            font-size: 2.7rem;
            margin-bottom: 0.5rem;
        }
        .neo-subtitle {
            max-width: 540px;
            color: var(--rag-muted);
        }
        .neo-kicker {
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.35em;
            color: var(--rag-accent);
        }
        .neo-card {
            padding: 1.3rem;
            border-radius: 20px;
            background: var(--rag-surface);
            border: 1px solid var(--rag-border);
            box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.05);
            margin-bottom: 1rem;
        }
        .neo-card-label {font-size: 0.78rem; color: var(--rag-muted); text-transform: uppercase; letter-spacing: 0.24em;}
        .neo-card-value {
            font-size: 2.1rem;
            font-weight: 600;
            margin-top: 0.35rem;
            background: linear-gradient(120deg, var(--rag-primary), var(--rag-accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .neo-chip {
            display: inline-block;
            padding: 0.25rem 0.8rem;
            border-radius: 999px;
            background: rgba(236, 72, 153, 0.12);
            color: var(--rag-accent);
            font-size: 0.72rem;
        }
        .neo-stack > div {
            padding: 1rem 1.2rem;
            border-left: 3px solid rgba(37,99,235,0.4);
            margin-bottom: 0.8rem;
            background: rgba(248,250,252,0.8);
            border-radius: 14px;
            color: var(--rag-text);
        }
        .neo-timeline {
            display: flex;
            gap: 0.8rem;
            align-items: center;
            padding: 0.6rem 0;
        }
        .neo-dot {
            width: 12px;
            height: 12px;
            border-radius: 12px;
            display: inline-block;
            box-shadow: 0 0 12px currentColor;
        }
        .metric small {
            color: var(--rag-muted);
        }
        .stMarkdown p {
            color: var(--rag-text);
        }
        .stTabs [data-baseweb="tab"] {
            color: var(--rag-muted);
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: var(--rag-primary);
        }
        .stDataFrame, .stCheckbox, .stTextInput>div>div>input, .stTextArea textarea, .stNumberInput input {
            color: var(--rag-text);
        }
        .stDataFrame {
            background: var(--rag-surface);
            border-radius: 16px;
            border: 1px solid var(--rag-border);
        }
        .stProgress .st-bo {
            background-color: rgba(15,23,42,0.1);
        }
        .stProgress .st-bq {
            background: linear-gradient(120deg, var(--rag-primary), var(--rag-accent));
        }
        .stMetric {
            background: var(--rag-surface);
            padding: 0.8rem 1rem;
            border-radius: 16px;
            border: 1px solid var(--rag-border);
            box-shadow: 0 10px 30px rgba(15,23,42,0.08);
        }
        [data-testid="stSidebar"] .rag-sidebar-section {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.28em;
            color: var(--rag-muted);
            margin-top: 1.2rem;
            margin-bottom: 0.3rem;
        }
        [data-testid="stSidebar"] .rag-section-caption {
            font-size: 0.8rem;
            color: var(--rag-muted);
            margin-bottom: 0.4rem;
        }
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
            border-radius: 14px;
            border: 1px solid var(--rag-border);
            background: rgba(241, 245, 249, 0.9);
            color: var(--rag-text);
            transition: all 0.2s ease;
        }
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {
            border-color: rgba(37,99,235,0.4);
            box-shadow: 0 0 20px rgba(59,130,246,0.25);
        }
        [data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
            border-radius: 14px;
            border: 1px solid transparent;
            background: linear-gradient(120deg, rgba(37,99,235,0.95), rgba(236,72,153,0.95));
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 20px 40px rgba(59,130,246,0.25);
        }
        .rag-health-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.6rem;
            margin-bottom: 0.6rem;
        }
        .rag-stat-pill {
            padding: 0.65rem 0.8rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid var(--rag-border);
            box-shadow: 0 10px 25px rgba(15,23,42,0.08);
        }
        .rag-stat-pill span {
            display: block;
            font-size: 0.7rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--rag-muted);
        }
        .rag-stat-pill strong {
            display: block;
            font-size: 1rem;
            margin-top: 0.2rem;
        }
        .rag-stat-pill.ok strong { color: var(--rag-success); }
        .rag-stat-pill.warn strong { color: var(--rag-warning); }
        .rag-stat-pill.neutral strong { color: var(--rag-text); }
        .rag-flow-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.8rem;
            margin-bottom: 1rem;
        }
        .rag-flow-step {
            padding: 1rem;
            border-radius: 16px;
            border: 1px dashed rgba(37,99,235,0.35);
            background: rgba(255,255,255,0.8);
        }
        .rag-flow-step strong {
            display: block;
            font-size: 0.85rem;
            color: var(--rag-text);
        }
        .rag-flow-step span {
            font-size: 0.8rem;
            color: var(--rag-muted);
        }
        .rag-flow-step p {
            font-size: 0.75rem;
            color: var(--rag-muted);
            margin: 0.35rem 0 0;
        }
        .reportview-container .main .block-container {
            padding-top: 1.3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
