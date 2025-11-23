from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.layout import render_page_header

REPORT_DIR = Path("evaluation/reports")
DATASET_DIR = Path("evaluation/datasets")


def _list_json(directory: Path) -> List[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


def _load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_metrics(payload: Dict) -> Dict[str, float]:
    if isinstance(payload.get("metrics"), dict):
        return payload["metrics"]
    ragas_section = payload.get("ragas", {})
    if isinstance(ragas_section, dict):
        results = ragas_section.get("results") or ragas_section.get("scores") or {}
        if isinstance(results, dict):
            return results
    return {}


def _build_history(report_paths: List[Path]) -> pd.DataFrame:
    rows: List[Dict[str, str | float]] = []
    for path in report_paths:
        payload = _load_json(path)
        timestamp = payload.get("created_at") or path.stem
        metrics = _extract_metrics(payload)
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                rows.append({"timestamp": timestamp, "metric": name, "value": value, "source": path.name})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df.sort_values("timestamp", inplace=True)
    return df


def _render_latest_report(report_files: List[Path]) -> None:
    if not report_files:
        st.info("No evaluation reports yet. Run `python scripts/evaluate.py` and refresh this page.")
        return

    latest = report_files[-1]
    payload = _load_json(latest)
    metrics = _extract_metrics(payload)

    st.subheader(f"Latest evaluation · {latest.name}")
    if metrics:
        cols = st.columns(len(metrics))
        for col, (metric, value) in zip(cols, metrics.items()):
            display_value = f"{value:.3f}" if isinstance(value, (int, float)) else value
            col.metric(metric, display_value)
    else:
        st.warning("No metric fields found in the report. Check the generation script output.")

    with st.expander("View raw report JSON", expanded=False):
        st.json(payload)


def _render_history(report_files: List[Path]) -> None:
    df = _build_history(report_files)
    if df.empty:
        return

    st.subheader("Metric trends")
    pivot = df.pivot(index="timestamp", columns="metric", values="value")
    st.line_chart(pivot)

    csv_buffer = StringIO()
    pivot.to_csv(csv_buffer)
    st.download_button("Download metrics CSV", data=csv_buffer.getvalue(), file_name="ragas_metrics.csv")


def _render_datasets() -> None:
    st.subheader("Evaluation datasets")
    dataset_files = _list_json(DATASET_DIR)
    if not dataset_files:
        st.info("Add JSON files under `evaluation/datasets/` to preview them here.")
        return

    dataset_map = {path.name: path for path in dataset_files}
    selected_name = st.selectbox("Choose dataset", list(dataset_map.keys()))
    selected_path = dataset_map[selected_name]
    payload = _load_json(selected_path)

    st.caption(f"Samples: {len(payload)} · Path: {selected_path}")
    preview_rows = [
        {"question": item.get("question"), "ground_truth": item.get("ground_truth"), "has_answer": bool(item.get("answer"))}
        for item in payload
    ]
    st.dataframe(preview_rows, use_container_width=True)

    st.download_button(
        label="Download JSON",
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name=selected_path.name,
        mime="application/json",
    )


def _render_scripts() -> None:
    st.subheader("Evaluation scripts & automation")
    st.markdown("Use the commands below to generate datasets, trigger evaluations, or run in batches:")
    st.code("python scripts/generate_eval_dataset.py --source docs --output evaluation/datasets/generated.json", language="bash")
    st.code("python scripts/evaluate.py --dataset evaluation/datasets/questions.json", language="bash")
    st.code("python scripts/nightly_eval.py --datasets evaluation/datasets/*.json", language="bash")


def render() -> None:
    render_page_header(
        "Evaluation Bench",
        "Review ragas metrics, historical trends, and evaluation assets in one place.",
        highlight="📊",
    )

    report_files = _list_json(REPORT_DIR)
    _render_latest_report(report_files)
    _render_history(report_files)

    st.divider()
    _render_datasets()

    st.divider()
    _render_scripts()


if __name__ == "__main__":
    render()
