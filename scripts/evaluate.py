from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pandas as pd
import requests
from ragas import evaluate
from ragas.metrics import answer_relevancy, context_precision, faithfulness

DEFAULT_API = "http://localhost:8000"
DEFAULT_DATASET = Path("evaluation/datasets/questions.json")
DEFAULT_OUTPUT = Path("evaluation/reports/latest.json")
DEFAULT_HISTORY_DIR = Path("evaluation/reports/history")
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


def call_query(api_base: str, question: str) -> Dict[str, Any]:
    response = requests.post(
        f"{api_base}/query",
        json={"question": question},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _summarize_scores(scores: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    if not scores:
        return {}
    summary: Dict[str, float] = {}
    for metric in scores[0].keys():
        values = [row.get(metric) for row in scores if isinstance(row.get(metric), (int, float))]
        if not values:
            continue
        series = pd.Series(values, dtype="float64")
        summary[metric] = round(float(series.mean()), 4)
    return summary


def _prepare_contexts(result_chunks: Iterable[Dict[str, Any]]) -> List[str]:
    contexts: List[str] = []
    for chunk in result_chunks:
        text = chunk.get("content") or chunk.get("text")
        if text:
            contexts.append(text)
    return contexts


def run_evaluation(
    api_base: str,
    dataset_path: Path,
    output_path: Path,
    *,
    history_dir: Path | None = DEFAULT_HISTORY_DIR,
    tag: str | None = None,
    offline: bool = False,
) -> Dict[str, Any]:
    dataset = load_dataset(dataset_path)
    rows = []
    for item in dataset:
        question = item["question"]
        ground_truth = item.get("ground_truth", "")
        preset_contexts = item.get("contexts", [])
        answer: str
        contexts: List[str]
        if offline and item.get("answer"):
            answer = item["answer"]
            contexts = preset_contexts
        else:
            result = call_query(api_base, question)
            answer = result.get("answer", "")
            contexts = _prepare_contexts(result.get("chunks", [])) or preset_contexts

        rows.append(
            {
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
            }
        )

    df = pd.DataFrame(rows)
    evaluation_result = evaluate(
        df,
        metrics=[faithfulness, answer_relevancy, context_precision],
    )

    now = datetime.utcnow()
    summary = _summarize_scores(evaluation_result.scores)
    ragas_blob = evaluation_result.to_json(indent=2, ensure_ascii=False)
    ragas_payload = json.loads(ragas_blob) if isinstance(ragas_blob, str) else ragas_blob

    payload = {
        "dataset": dataset_path.name,
        "dataset_path": str(dataset_path),
        "size": len(df),
        "created_at": now.isoformat() + "Z",
        "api_base": api_base,
        "tag": tag,
        "metrics": summary,
        "records": rows,
        "ragas": ragas_payload,
    }

    _ensure_dir(output_path)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    csv_path = output_path.with_suffix(".csv")
    evaluation_result.to_pandas().to_csv(csv_path, index=False, encoding="utf-8")

    if history_dir:
        history_dir.mkdir(parents=True, exist_ok=True)
        history_file = history_dir / f"{now.strftime(TIMESTAMP_FORMAT)}-{dataset_path.stem}.json"
        history_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    print(f"Evaluation completed for {dataset_path.name}. Metrics: {summary}")
    return payload


def main():
    parser = argparse.ArgumentParser(description="Run ragas evaluation against the RAG backend")
    parser.add_argument("--api", default=DEFAULT_API, help="FastAPI base URL")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="JSON dataset with question/ground_truth")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Where to store evaluation results")
    parser.add_argument("--history-dir", default=str(DEFAULT_HISTORY_DIR), help="Optional history directory")
    parser.add_argument("--tag", default=None, help="Custom label for this run")
    parser.add_argument("--offline", action="store_true", help="Skip API calls and reuse answers stored in the dataset")
    args = parser.parse_args()

    run_evaluation(
        api_base=args.api,
        dataset_path=Path(args.dataset),
        output_path=Path(args.output),
        history_dir=Path(args.history_dir) if args.history_dir else None,
        tag=args.tag,
        offline=args.offline,
    )


if __name__ == "__main__":
    main()
