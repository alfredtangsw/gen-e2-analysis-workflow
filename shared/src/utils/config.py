"""
Shared utilities: configuration loader and logger setup.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from loguru import logger

# Load .env once at import time
load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_project_root() -> Path:
    """Return the absolute project root path."""
    return _PROJECT_ROOT


def load_config(config_path: str | Path) -> dict:
    """Load a YAML configuration file, expanding environment variables."""
    path = Path(config_path)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    with path.open() as f:
        raw = f.read()
    # Expand $VAR and ${VAR} patterns
    expanded = os.path.expandvars(raw)
    return yaml.safe_load(expanded)


def setup_logger(log_dir: str | Path, level: str = "INFO") -> None:
    """Configure loguru to write to a rotating file in log_dir."""
    log_path = _PROJECT_ROOT / log_dir
    log_path.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path / "{time:YYYY-MM-DD}.log",
        level=level,
        rotation="00:00",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
    )
