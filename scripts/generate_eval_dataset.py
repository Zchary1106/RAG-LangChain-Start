from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a technical writer who crafts evaluation datasets for RAG systems."),
        (
            "human",
            """
            Read the knowledge snippet below and create {count} question-answer pairs.
            ---
            {context}
            ---
            Guidelines:
            1. Mix factual questions with reasoning questions.
            2. Answers must be grounded in the snippet—never invent facts.
            3. Return a JSON array where each item looks like {{"question": "", "answer": ""}}.
            """,
        ),
    ]
)


def _build_azure_llm(deployment_override: str | None) -> AzureChatOpenAI:
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment = deployment_override or os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
    missing = [
        name
        for name, value in {
            "AZURE_OPENAI_API_KEY": api_key,
            "AZURE_OPENAI_ENDPOINT": endpoint,
            "AZURE_OPENAI_API_VERSION": api_version,
            "AZURE_OPENAI_CHAT_DEPLOYMENT": deployment,
        }.items()
        if not value
    ]
    if missing:
        raise SystemExit(f"Missing Azure OpenAI configuration: {', '.join(missing)}")
    return AzureChatOpenAI(
        temperature=0.2,
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
        azure_deployment=deployment,
    )


def _gather_text(sources: Iterable[str]) -> List[str]:
    texts: List[str] = []
    for item in sources:
        path = Path(item)
        if path.is_file():
            texts.append(path.read_text(encoding="utf-8"))
        elif path.is_dir():
            for child in sorted(path.rglob("*.md")):
                texts.append(child.read_text(encoding="utf-8"))
            for child in sorted(path.rglob("*.txt")):
                texts.append(child.read_text(encoding="utf-8"))
        else:
            for candidate in Path().glob(item):
                if candidate.is_file():
                    texts.append(candidate.read_text(encoding="utf-8"))
    return texts


def _chunk(text: str, size: int, overlap: int) -> Iterable[str]:
    step = max(1, size - overlap)
    start = 0
    while start < len(text):
        end = start + size
        yield text[start:end]
        start += step


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic evaluation dataset via LLM")
    parser.add_argument("--source", nargs="+", default=["docs"], help="Files or folders to sample content from")
    parser.add_argument("--output", default="evaluation/datasets/generated.json", help="Where to store the dataset")
    parser.add_argument("--deployment", default=None, help="Azure OpenAI chat deployment name (default: env AZURE_OPENAI_CHAT_DEPLOYMENT)")
    parser.add_argument("--chunk-size", type=int, default=1200, help="Characters per prompt")
    parser.add_argument("--overlap", type=int, default=200, help="Overlap between chunks")
    parser.add_argument("--questions-per-chunk", type=int, default=2, help="Number of Q/A pairs per chunk")
    parser.add_argument("--max-samples", type=int, default=20, help="Maximum number of records to output")
    args = parser.parse_args()

    texts = _gather_text(args.source)
    if not texts:
        raise SystemExit("No source documents found for dataset generation")

    if args.chunk_size <= 0:
        raise SystemExit("--chunk-size must be a positive integer")
    if args.overlap < 0:
        raise SystemExit("--overlap must be >= 0")

    llm = _build_azure_llm(args.deployment)
    dataset: List[dict] = []

    for text in texts:
        for chunk in _chunk(text, args.chunk_size, args.overlap):
            if len(dataset) >= args.max_samples:
                break
            response = llm.invoke(TEMPLATE.format_messages(context=chunk, count=args.questions_per_chunk))
            qa_pairs = json.loads(response.content)
            for pair in qa_pairs:
                dataset.append(
                    {
                        "question": pair["question"],
                        "ground_truth": pair["answer"],
                        "answer": pair["answer"],
                        "contexts": [chunk.strip()],
                    }
                )
        if len(dataset) >= args.max_samples:
            break

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {len(dataset)} samples → {output_path}")


if __name__ == "__main__":
    main()
