from __future__ import annotations

import os
import json
from typing import Any, Dict, Iterable, Iterator

import requests

API_BASE = os.getenv("RAG_API_BASE", "http://localhost:8000")


def set_api_base(url: str) -> None:
    global API_BASE  # noqa: PLW0603
    API_BASE = url.rstrip("/")


def _url(path: str) -> str:
    return f"{API_BASE}{path}"


def health() -> Dict[str, Any]:
    response = requests.get(_url("/health"), timeout=30)
    response.raise_for_status()
    return response.json()


def build_index(files: Iterable[bytes], filenames: Iterable[str], payload: Dict[str, Any]) -> Dict[str, Any]:
    form_files = [
        (
            "files",
            (name, data, "application/octet-stream"),
        )
        for name, data in zip(filenames, files)
    ]
    response = requests.post(_url("/build"), data=payload, files=form_files, timeout=120)
    response.raise_for_status()
    return response.json()


def query(question: str, strategy: str | None, chain_type: str, top_k: int | None = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"question": question, "chain_type": chain_type}
    if strategy:
        body["retrieval_strategy"] = strategy
    if top_k:
        body["top_k"] = top_k
    response = requests.post(_url("/query"), json=body, timeout=60)
    response.raise_for_status()
    return response.json()


def query_stream(question: str, strategy: str | None, chain_type: str, top_k: int | None = None) -> Iterator[Dict[str, Any]]:
    body: Dict[str, Any] = {"question": question, "chain_type": chain_type}
    if strategy:
        body["retrieval_strategy"] = strategy
    if top_k:
        body["top_k"] = top_k
    with requests.post(_url("/query/stream"), json=body, stream=True, timeout=None) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data:"):
                line = line[5:].strip()
            if line == "[DONE]":
                break
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            yield payload


def get_job(job_id: str) -> Dict[str, Any]:
    response = requests.get(_url(f"/jobs/{job_id}"), timeout=15)
    response.raise_for_status()
    return response.json()
