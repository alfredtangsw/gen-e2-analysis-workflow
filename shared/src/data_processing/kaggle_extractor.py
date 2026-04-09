"""
Kaggle data extractor.

Uses the Kaggle public API (credential-free for public datasets via HTTP,
or the official kaggle-python client for datasets that require authentication).

Credentials are read from environment variables:
  KAGGLE_USERNAME  — Kaggle account username
  KAGGLE_KEY       — Kaggle API key (from https://www.kaggle.com/settings/account)

Set these in your .env file (copied from .env.example).
"""
from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path
from time import sleep

import requests
from loguru import logger

# Default download root — override per-call or via env
_DEFAULT_RAW_DIR = Path(__file__).resolve().parents[3] / "shared" / "data" / "1_raw"
_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 5


def _get_kaggle_credentials() -> tuple[str, str]:
    """Read Kaggle credentials from environment variables."""
    username = os.environ.get("KAGGLE_USERNAME", "")
    key = os.environ.get("KAGGLE_KEY", "")
    if not username or not key:
        raise EnvironmentError(
            "KAGGLE_USERNAME and KAGGLE_KEY must be set in your .env file. "
            "See .env.example for instructions."
        )
    return username, key


def download_kaggle_dataset(
    dataset_slug: str,
    output_dir: str | Path | None = None,
    unzip: bool = True,
) -> Path:
    """Download a Kaggle dataset to output_dir.

    Parameters
    ----------
    dataset_slug:
        ``owner/dataset-name`` as shown in the Kaggle dataset URL.
    output_dir:
        Destination folder. Defaults to ``shared/data/1_raw/<dataset-name>/``.
    unzip:
        If True, extract the downloaded zip and remove the archive.

    Returns
    -------
    Path to the directory containing the downloaded files.
    """
    username, key = _get_kaggle_credentials()

    dataset_name = dataset_slug.split("/")[-1]
    dest = Path(output_dir) if output_dir else _DEFAULT_RAW_DIR / dataset_name
    dest.mkdir(parents=True, exist_ok=True)

    url = f"https://www.kaggle.com/api/v1/datasets/download/{dataset_slug}"
    logger.info(f"Downloading Kaggle dataset '{dataset_slug}' → {dest}")

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                auth=(username, key),
                stream=True,
                timeout=120,
            )
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            logger.warning(f"Attempt {attempt}/{_MAX_RETRIES} failed: {exc}")
            if attempt == _MAX_RETRIES:
                raise
            sleep(_RETRY_DELAY_SECONDS * attempt)

    zip_path = dest / f"{dataset_name}.zip"
    with zip_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    file_size_mb = zip_path.stat().st_size / (1024 ** 2)
    logger.info(f"Downloaded {file_size_mb:.1f} MB to {zip_path}")

    if unzip:
        logger.info(f"Extracting {zip_path}")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(dest)
        zip_path.unlink()
        logger.info(f"Extracted to {dest}")

    return dest


def test_kaggle_credentials() -> bool:
    """Validate Kaggle credentials by hitting the API's me endpoint."""
    try:
        username, key = _get_kaggle_credentials()
        response = requests.get(
            "https://www.kaggle.com/api/v1/competitions/list",
            auth=(username, key),
            timeout=15,
        )
        response.raise_for_status()
        logger.info("Kaggle credentials validated successfully.")
        return True
    except Exception as exc:
        logger.error(f"Kaggle credential validation failed: {exc}")
        return False
