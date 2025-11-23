from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List

from scripts.evaluate import DEFAULT_API, DEFAULT_HISTORY_DIR, run_evaluation

DEFAULT_OUTPUT_DIR = Path("evaluation/reports")


def _collect_datasets(inputs: List[str]) -> List[Path]:
    paths: List[Path] = []
    for item in inputs:
        path = Path(item)
        if path.is_file():
            paths.append(path)
        elif path.is_dir():
            paths.extend(sorted(path.glob("*.json")))
        else:
            for candidate in Path().glob(item):
                if candidate.is_file():
                    paths.append(candidate)
    return sorted(set(paths))


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch evaluator for scheduling/CI runs")
    parser.add_argument("--api", default=DEFAULT_API, help="FastAPI base URL")
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=[str(DEFAULT_OUTPUT_DIR.parent / "datasets" / "questions.json")],
        help="List of dataset files or glob patterns",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory to place latest reports")
    parser.add_argument("--history-dir", default=str(DEFAULT_HISTORY_DIR), help="Directory for timestamped reports")
    parser.add_argument("--tag", default=None, help="Optional run tag (will append dataset name)")
    parser.add_argument("--offline", action="store_true", help="Reuse answers stored in dataset instead of calling API")
    args = parser.parse_args()

    dataset_paths = _collect_datasets(args.datasets)
    if not dataset_paths:
        raise SystemExit("No datasets found for evaluation")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    history_dir = Path(args.history_dir) if args.history_dir else None

    for dataset_path in dataset_paths:
        dataset_tag = f"{args.tag}-{dataset_path.stem}" if args.tag else dataset_path.stem
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        output_path = output_dir / f"{dataset_path.stem}-latest.json"
        run_evaluation(
            api_base=args.api,
            dataset_path=dataset_path,
            output_path=output_path,
            history_dir=history_dir or output_dir / "history",
            tag=f"{dataset_tag}-{timestamp}",
            offline=args.offline,
        )

if __name__ == "__main__":
    main()
