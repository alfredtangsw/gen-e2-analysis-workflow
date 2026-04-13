"""
Clean Phase — PS-002 Disease Burden Temporal Trends Analysis
Reads 5 raw CSVs, applies cleaning rules, writes parquets to data/4_processed/.
Also builds the mortality master (long-form, Total sex, 3 diseases).
"""
import polars as pl
from pathlib import Path
from datetime import date

BASE  = Path(__file__).resolve().parents[4]
RAW   = BASE / "shared/data/1_raw/mortality"
PS    = Path(__file__).resolve().parents[3]
PROC  = PS / "data/4_processed"
PROC.mkdir(parents=True, exist_ok=True)

STAMP = date.today().strftime("%Y%m%d")


def _validate_asmr(df: pl.DataFrame, col: str = "asmr_per_100k") -> pl.DataFrame:
    """Drop rows where ASMR is null or non-positive."""
    return df.filter(pl.col(col).is_not_null() & (pl.col(col) > 0))


def clean_cancer() -> pl.DataFrame:
    df = pl.read_csv(RAW / "age-standardised-mortality-rate-for-cancer.csv")
    df = (df
          .with_columns(pl.col("asmr_per_100k").round(2))
          .pipe(_validate_asmr)
          .sort(["year", "sex"]))
    df.write_parquet(PROC / "cancer_mortality_clean.parquet")
    return df


def clean_stroke() -> pl.DataFrame:
    df = pl.read_csv(RAW / "age-standardised-mortality-rate-for-stroke.csv")
    df = (df
          .with_columns(pl.col("asmr_per_100k").round(2))
          .pipe(_validate_asmr)
          .sort(["year", "sex"]))
    df.write_parquet(PROC / "stroke_mortality_clean.parquet")
    return df


def clean_ihd() -> pl.DataFrame:
    df = pl.read_csv(RAW / "age-standardised-mortality-rate-for-ischaemic-heart-disease.csv")
    df = (df
          .with_columns(pl.col("asmr_per_100k").round(2))
          .pipe(_validate_asmr)
          .sort(["year", "sex"]))
    df.write_parquet(PROC / "ihd_mortality_clean.parquet")
    return df


def clean_hospital_admissions() -> pl.DataFrame:
    df = pl.read_csv(RAW / "hospital-admission-rate-by-age-and-sex.csv")
    df = (df
          .drop_nulls(subset=["year", "age_group", "sex"])
          .filter(pl.col("admission_rate_per_100k") > 0)
          .with_columns(pl.col("admission_rate_per_100k").round(1))
          .sort(["year", "age_group", "sex"]))
    df.write_parquet(PROC / "hospital_admissions_clean.parquet")
    return df


def clean_vaccination() -> pl.DataFrame:
    df = pl.read_csv(RAW / "vaccination-and-immunisation-of-students-annual.csv")
    df = (df
          .drop_nulls(subset=["year", "programme"])
          .with_columns(pl.col("coverage_pct").clip(0.0, 100.0).round(1))
          .sort(["year", "programme"]))
    df.write_parquet(PROC / "vaccination_clean.parquet")
    return df


def build_master(cancer: pl.DataFrame, stroke: pl.DataFrame, ihd: pl.DataFrame) -> pl.DataFrame:
    """Combine three mortality datasets into a long-form master (Total sex only)."""
    master = pl.concat([
        cancer.filter(pl.col("sex") == "Total"),
        stroke.filter(pl.col("sex") == "Total"),
        ihd.filter(pl.col("sex") == "Total"),
    ]).sort(["disease", "year"])
    master.write_parquet(PROC / "mortality_master_clean.parquet")
    return master


def run() -> None:
    print("Cleaning datasets...")
    cancer = clean_cancer()
    stroke = clean_stroke()
    ihd    = clean_ihd()
    _      = clean_hospital_admissions()
    _      = clean_vaccination()
    master = build_master(cancer, stroke, ihd)
    print(f"  mortality_master_clean: {master.shape}")
    print(f"  Nulls in master: {master.null_count().sum_horizontal().sum()}")
    print(f"Clean phase complete → {PROC}")


if __name__ == "__main__":
    run()
