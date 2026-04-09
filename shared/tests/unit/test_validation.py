"""
Unit tests for shared/src/data_processing/validation.py
"""
import polars as pl
import pytest

from shared.src.data_processing.validation import null_rate_report, validate_schema


def test_validate_schema_all_present():
    df = pl.DataFrame({"a": [1], "b": [2]})
    missing = validate_schema(df, ["a", "b"])
    assert missing == []


def test_validate_schema_missing_columns():
    df = pl.DataFrame({"a": [1]})
    missing = validate_schema(df, ["a", "b", "c"])
    assert set(missing) == {"b", "c"}


def test_null_rate_report_no_nulls():
    df = pl.DataFrame({"x": [1, 2, 3]})
    report = null_rate_report(df)
    assert report.filter(pl.col("column") == "x")["null_count"][0] == 0
    assert report.filter(pl.col("column") == "x")["null_rate"][0] == pytest.approx(0.0)


def test_null_rate_report_with_nulls():
    df = pl.DataFrame({"x": [1, None, None, 4]})
    report = null_rate_report(df)
    row = report.filter(pl.col("column") == "x")
    assert row["null_count"][0] == 2
    assert row["null_rate"][0] == pytest.approx(0.5)
