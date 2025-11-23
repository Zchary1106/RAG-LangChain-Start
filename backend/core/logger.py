from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Optional

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "logging.yaml"


def configure_logging(config_path: Optional[Path] = None) -> None:
    path = config_path or CONFIG_PATH
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
