from __future__ import annotations

import argparse
from pathlib import Path
import shutil

SAMPLE_DIR = Path("samples")
UPLOAD_DIR = Path("data/uploads")


def main():
    parser = argparse.ArgumentParser(description="Copy sample docs into the upload directory")
    parser.add_argument("--source", default=str(SAMPLE_DIR), help="Directory with sample docs")
    parser.add_argument("--dest", default=str(UPLOAD_DIR), help="Destination upload dir")
    args = parser.parse_args()

    source = Path(args.source)
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)

    count = 0
    for file in source.glob("*"):
        if file.is_file():
            shutil.copy(file, dest / file.name)
            count += 1
    print(f"Copied {count} files into {dest}")


if __name__ == "__main__":
    main()
