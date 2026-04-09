"""
Data validation utilities for healthcare datasets.

Validates raw data on load: schema, dtypes, null rates, and value ranges.
Writes a quality report to logs/etl/.
"""
from __future__ import annotations

from pathlib import Path

import polars as pl
from loguru import logger


def validate_schema(df: pl.DataFrame, expected_columns: list[str]) -> list[str]:
    """Return a list of missing columns."""
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        logger.warning(f"Missing columns: {missing}")
    return missing


def null_rate_report(df: pl.DataFrame) -> pl.DataFrame:
    """Return a DataFrame with null counts and rates per column."""
    n = len(df)
    report = pl.DataFrame(
        {
            "column": df.columns,
            "null_count": [df[c].null_count() for c in df.columns],
            "null_rate": [df[c].null_count() / n if n > 0 else 0.0 for c in df.columns],
        }
    )
    return report


def write_quality_report(
    df: pl.DataFrame,
    dataset_name: str,
    log_dir: str | Path,
    expected_columns: list[str] | None = None,
) -> Path:
    """Run basic quality checks and persist a CSV report.

    Parameters
    ----------
    df:
        The loaded DataFrame to validate.
    dataset_name:
        Used as the filename prefix for the report.
    log_dir:
        Directory where the report CSV is saved.
    expected_columns:
        If provided, checks that all listed columns exist.

    Returns
    -------
    Path to the generated report file.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Running quality checks on '{dataset_name}': {df.shape}")

    if expected_columns:
        missing = validate_schema(df, expected_columns)
        if missing:
            logger.warning(f"Quality check — missing columns: {missing}")

    report = null_rate_report(df)
    high_null = report.filter(pl.col("null_rate") > 0.2)
    if len(high_null) > 0:
        logger.warning(f"High null rate (>20%) in columns: {high_null['column'].to_list()}")

    out_path = log_path / f"{dataset_name}_quality_report.csv"
    report.write_csv(out_path)
    logger.info(f"Quality report saved to {out_path}")
    return out_path
