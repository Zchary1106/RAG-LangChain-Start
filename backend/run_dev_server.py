from __future__ import annotations

"""Developer-friendly entrypoint for running the FastAPI backend with scoped reloads."""

import argparse
from pathlib import Path

import uvicorn

from backend.config.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FastAPI backend with reload limited to backend/ directory")
    parser.add_argument("--host", default=None, help="Override API host (defaults to config.api.host)")
    parser.add_argument("--port", type=int, default=None, help="Override API port (defaults to config.api.port)")
    parser.add_argument("--no-reload", action="store_true", help="Disable reload even in dev mode")
    args = parser.parse_args()

    settings = get_settings()
    backend_dir = Path(__file__).resolve().parent

    uvicorn.run(
        "backend.api.main:app",
        host=args.host or settings.api.host,
        port=args.port or settings.api.port,
        reload=not args.no_reload,
        reload_dirs=[str(backend_dir)] if not args.no_reload else None,
        reload_includes=["*.py"],
        workers=1,
    )


if __name__ == "__main__":
    main()
