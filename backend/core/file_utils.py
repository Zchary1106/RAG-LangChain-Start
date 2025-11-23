from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from fastapi import UploadFile

from backend.config.settings import get_settings

settings = get_settings()


def ensure_directories() -> None:
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    tmp_dir = (settings.upload_path / "tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_store_path.mkdir(parents=True, exist_ok=True)


def save_upload(upload: UploadFile) -> Path:
    ensure_directories()
    destination = settings.upload_path / upload.filename
    with destination.open("wb") as out_file:
        shutil.copyfileobj(upload.file, out_file)
    return destination


def cleanup_files(paths: Iterable[Path]) -> None:
    for path in paths:
        if path.exists():
            path.unlink()
