"""PS-001 Phase 2: Clean and standardise raw workforce datasets."""

import json
from pathlib import Path

import polars as pl

BASE = Path(__file__).resolve().parents[5]
SHARED_RAW = BASE / "shared/data/1_raw/workforce"
PS_DIR = BASE / "problem-statements/ps-001-healthcare-workforce"
PROC_DIR = PS_DIR / "data/4_processed"
HANDOFF_DIR = BASE / "docs/agent-handoffs/data-cleaning/ps-001-healthcare-workforce"


def _make_dirs() -> None:
    for d in [PROC_DIR, HANDOFF_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def clean_doctors() -> pl.DataFrame:
    return (
        pl.read_csv(SHARED_RAW / "number-of-doctors.csv")
        .with_columns([
            pl.col("year").cast(pl.Int32),
            pl.col("sector").cast(pl.Categorical),
            pl.col("level").cast(pl.Categorical),
            pl.col("headcount").cast(pl.Int32),
        ])
        .filter(pl.col("year") <= 2019)
    )


def clean_nurses() -> pl.DataFrame:
    return (
        pl.read_csv(SHARED_RAW / "number-of-nurses-and-midwives.csv")
        .with_columns([
            pl.col("year").cast(pl.Int32),
            pl.col("sector").cast(pl.Categorical),
            pl.col("nurse_type").cast(pl.Categorical),
            pl.col("headcount").cast(pl.Int32),
        ])
        .filter(pl.col("year") <= 2019)
    )


def clean_pharmacists() -> pl.DataFrame:
    return (
        pl.read_csv(SHARED_RAW / "number-of-pharmacists.csv")
        .with_columns([
            pl.col("year").cast(pl.Int32),
            pl.col("sector").cast(pl.Categorical),
            pl.col("headcount").cast(pl.Int32),
        ])
        .filter(pl.col("year") <= 2019)
    )


def clean_dentists() -> pl.DataFrame:
    return (
        pl.read_csv(SHARED_RAW / "number-of-dentists.csv")
        .with_columns([
            pl.col("year").cast(pl.Int32),
            pl.col("sector").cast(pl.Categorical),
            pl.col("headcount").cast(pl.Int32),
        ])
        .filter(pl.col("year") <= 2019)
    )


def clean_allied_health() -> pl.DataFrame:
    return (
        pl.read_csv(SHARED_RAW / "number-of-allied-health-professionals.csv")
        .with_columns([
            pl.col("year").cast(pl.Int32),
            pl.col("profession").cast(pl.Categorical),
            pl.col("sector").cast(pl.Categorical),
            pl.col("headcount").cast(pl.Int32),
        ])
        .filter(pl.col("year") <= 2019)
    )


def clean_hospital_admissions() -> pl.DataFrame:
    return (
        pl.read_csv(SHARED_RAW / "hospital-admission-rate-by-age-and-sex.csv")
        .with_columns([
            pl.col("year").cast(pl.Int32),
            pl.col("age_group").cast(pl.Categorical),
            pl.col("sex").cast(pl.Categorical),
            pl.col("admission_rate_per_1000").cast(pl.Int32),
        ])
    )


def clean_facilities() -> pl.DataFrame:
    return (
        pl.read_csv(SHARED_RAW / "health-facilities-and-beds-in-inpatient-facilities.csv")
        .with_columns([
            pl.col("year").cast(pl.Int32),
            pl.col("facility_type").cast(pl.Categorical),
            pl.col("facility_count").cast(pl.Int32),
        ])
    )


def clean_population() -> pl.DataFrame:
    return (
        pl.read_csv(SHARED_RAW / "singapore-population-by-age.csv")
        .with_columns([
            pl.col("year").cast(pl.Int32),
            pl.col("age_group").cast(pl.Categorical),
            pl.col("population").cast(pl.Int32),
        ])
    )


def build_master(doctors: pl.DataFrame, nurses: pl.DataFrame, pharmacists: pl.DataFrame,
                 dentists: pl.DataFrame, allied: pl.DataFrame, pop_total: pl.DataFrame) -> pl.DataFrame:
    def _agg_total(df: pl.DataFrame, profession: str) -> pl.DataFrame:
        col = "profession" if "profession" in df.columns else None
        base = df.filter(pl.col("sector") == "total")
        if col:
            base = base.filter(pl.col("profession").is_not_null())
        return (
            base.group_by("year")
            .agg(pl.col("headcount").sum())
            .with_columns(pl.lit(profession).cast(pl.Categorical).alias("profession"))
        )

    master = pl.concat([
        _agg_total(doctors, "doctors"),
        _agg_total(nurses, "nurses"),
        _agg_total(pharmacists, "pharmacists"),
        _agg_total(dentists, "dentists"),
        _agg_total(allied, "allied_health"),
    ]).sort(["profession", "year"])

    master = master.join(pop_total, on="year", how="left")
    master = master.with_columns(
        (pl.col("headcount") / pl.col("total_population") * 10000).alias("density_per_10k_pop")
    )
    return master


def run() -> None:
    _make_dirs()

    doctors     = clean_doctors()
    nurses      = clean_nurses()
    pharmacists = clean_pharmacists()
    dentists    = clean_dentists()
    allied      = clean_allied_health()
    hosp_adm    = clean_hospital_admissions()
    facilities  = clean_facilities()
    population  = clean_population()

    pop_total = (
        population.group_by("year")
        .agg(pl.col("population").sum().alias("total_population"))
        .sort("year")
    )

    master = build_master(doctors, nurses, pharmacists, dentists, allied, pop_total)

    datasets = {
        "workforce_master_clean.parquet": master,
        "doctors_clean.parquet": doctors,
        "nurses_clean.parquet": nurses,
        "pharmacists_clean.parquet": pharmacists,
        "dentists_clean.parquet": dentists,
        "allied_health_clean.parquet": allied,
        "hospital_admissions_clean.parquet": hosp_adm,
        "facilities_clean.parquet": facilities,
        "population_clean.parquet": population,
        "population_totals_clean.parquet": pop_total,
    }

    for filename, df in datasets.items():
        df.write_parquet(PROC_DIR / filename)
        nulls = df.null_count().sum_horizontal().sum()
        print(f"  {filename}: {df.shape}, nulls={nulls}")

    handoff = {
        "agent": "data-cleaning",
        "problem_statement": "ps-001-healthcare-workforce-sustainability",
        "timestamp": "2026-04-09",
        "status": "completed",
        "cleaned_datasets": [{"file": k, "records": len(v)} for k, v in datasets.items()],
        "cleaning_actions": [
            "Cast all columns to Int32/Categorical",
            "Filtered to year <= 2019 (analysis period)",
            "Aggregated to master long-form dataset with density KPI",
            "Joined population for density_per_10k_pop",
        ],
        "next_agent": "exploratory-analysis",
        "files_created": [str(PROC_DIR / k) for k in datasets],
    }
    with open(HANDOFF_DIR / "cleaning_to_exploratory_20260409.json", "w") as f:
        json.dump(handoff, f, indent=2)

    print(f"Cleaning complete. {len(datasets)} parquets saved to {PROC_DIR}")


if __name__ == "__main__":
    run()
