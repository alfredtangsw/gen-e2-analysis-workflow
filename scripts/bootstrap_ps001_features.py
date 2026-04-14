"""PS-001 Phase 3b: Feature Engineering — compute baseline metrics and ratios."""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
from loguru import logger
import nbformat

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
INTERIM = WS / "problem-statements/ps-001-healthcare-system-baseline/data/3_interim"
PROCESSED = WS / "problem-statements/ps-001-healthcare-system-baseline/data/4_processed"
RESULTS = WS / "problem-statements/ps-001-healthcare-system-baseline/results/tables"
NB_DIR = WS / "problem-statements/ps-001-healthcare-system-baseline/notebooks"
LOGS = WS / "problem-statements/ps-001-healthcare-system-baseline/logs/etl"
HANDOFF_DIR = WS / "docs/agent-handoffs/feature-engineering/ps-001-healthcare-system-baseline"
for d in [PROCESSED, RESULTS, NB_DIR, LOGS, HANDOFF_DIR]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"features_{TS}.log"), level="DEBUG")
logger.info("PS-001 Feature Engineering started")


# ── Load cleaned data ─────────────────────────────────────────────────────────
def load(pattern: str) -> pl.DataFrame:
    matches = list(INTERIM.glob(f"*{pattern}*"))
    if not matches:
        logger.warning(f"No parquet for pattern: {pattern}")
        return pl.DataFrame()
    df = pl.read_parquet(str(matches[0]))
    logger.info(f"Loaded {matches[0].name}: {df.shape}")
    return df

nurses      = load("nurses-and-midwives")
doctors     = load("doctors")
allied      = load("allied-health")
dentists    = load("dentists")
pharmacists = load("pharmacists")
beds        = load("beds-in-inpatient")
population  = load("singapore-population")
admissions  = load("workforce_hospital-admission")


def year_col(df: pl.DataFrame) -> str:
    return next((c for c in df.columns if "year" in c.lower()), df.columns[0])

def value_col(df: pl.DataFrame) -> str:
    yc = year_col(df)
    return next((c for c in df.columns if c != yc and
                 df[c].dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64,
                                  pl.Float32, pl.Float64)), df.columns[-1])


# ── Feature 1: Workforce aggregate per year ───────────────────────────────────
logger.info("=== Feature 1: Workforce aggregate ===")
wf_frames = []
for name, df in [("nurses", nurses), ("doctors", doctors),
                 ("allied_health", allied), ("dentists", dentists),
                 ("pharmacists", pharmacists)]:
    if len(df) == 0: continue
    yc = year_col(df); vc = value_col(df)
    agg = (df.group_by(yc)
             .agg(pl.col(vc).sum().alias("headcount"))
             .sort(yc)
             .with_columns(pl.lit(name).alias("profession")))
    wf_frames.append(agg)

if wf_frames:
    wf_long = pl.concat(wf_frames, how="diagonal")
    # Add YoY growth rate per profession
    wf_long = wf_long.sort(["profession", year_col(nurses)]).with_columns(
        pl.col("headcount").shift(1).over("profession").alias("headcount_prev_year")
    ).with_columns(
        ((pl.col("headcount") - pl.col("headcount_prev_year")) /
         pl.col("headcount_prev_year") * 100).alias("yoy_growth_pct")
    )
    logger.info(f"Workforce long: {wf_long.shape}")
    print(wf_long.tail(10))

    out1 = PROCESSED / "workforce_headcount_long.parquet"
    wf_long.write_parquet(str(out1), compression="snappy")
    logger.info(f"Written: {out1}")
else:
    wf_long = pl.DataFrame()
    out1 = None


# ── Feature 2: Population total per year ─────────────────────────────────────
logger.info("=== Feature 2: Population aggregation ===")
if len(population) > 0:
    pop_yc = year_col(population)
    pop_vc = value_col(population)
    pop_agg = (population.group_by(pop_yc)
               .agg(pl.col(pop_vc).sum().alias("total_population"))
               .sort(pop_yc))
    logger.info(f"Population aggregated: {pop_agg.shape}")
    print(pop_agg.tail(10))
    out2 = PROCESSED / "population_annual.parquet"
    pop_agg.write_parquet(str(out2), compression="snappy")
    logger.info(f"Written: {out2}")
else:
    pop_agg = pl.DataFrame()
    out2 = None


# ── Feature 3: Workforce density per 10,000 population ───────────────────────
logger.info("=== Feature 3: Workforce density per 10k ===")
density_frames = []
if len(wf_long) > 0 and len(pop_agg) > 0:
    wf_yc = year_col(nurses)
    pop_yc2 = year_col(population)
    merged = wf_long.join(pop_agg, left_on=wf_yc, right_on=pop_yc2, how="left")
    merged = merged.with_columns(
        (pl.col("headcount") / pl.col("total_population") * 10000).alias("per_10k_population")
    )
    logger.info(f"Density computed: {merged.shape}")
    print(merged.filter(pl.col("profession") == "nurses").tail())
    out3 = PROCESSED / "workforce_density_per_10k.parquet"
    merged.write_parquet(str(out3), compression="snappy")
    logger.info(f"Written: {out3}")
else:
    merged = pl.DataFrame()
    out3 = None


# ── Feature 4: Beds aggregate + ratios ────────────────────────────────────────
logger.info("=== Feature 4: Bed metrics ===")
if len(beds) > 0:
    beds_yc = year_col(beds)
    beds_vc = value_col(beds)
    beds_agg = (beds.group_by(beds_yc)
                .agg(pl.col(beds_vc).sum().alias("total_beds"))
                .sort(beds_yc))
    if len(pop_agg) > 0:
        beds_merged = beds_agg.join(pop_agg, left_on=beds_yc, right_on=pop_yc2 if len(pop_agg) > 0 else beds_yc, how="left")
        beds_merged = beds_merged.with_columns(
            (pl.col("total_beds") / pl.col("total_population") * 10000).alias("beds_per_10k")
        )
    else:
        beds_merged = beds_agg

    out4 = PROCESSED / "beds_annual.parquet"
    beds_merged.write_parquet(str(out4), compression="snappy")
    logger.info(f"Written: {out4}")
    print(beds_merged.tail())
else:
    beds_merged = pl.DataFrame()
    out4 = None


# ── Feature 5: CAGR computation for baseline metrics ─────────────────────────
logger.info("=== Feature 5: CAGR per profession ===")
cagr_rows = []
if len(wf_long) > 0:
    yc = year_col(nurses)
    for profession in wf_long["profession"].unique().to_list():
        sub = wf_long.filter(pl.col("profession") == profession).sort(yc)
        years = sub[yc].to_list()
        vals  = sub["headcount"].to_list()
        if len(vals) < 2: continue
        for (y_s, v_s), (y_e, v_e), label in [
            ((years[0], vals[0]), (years[-1], vals[-1]), f"{years[0]}-{years[-1]}"),
        ]:
            if v_s and v_s > 0 and v_e and (y_e - y_s) > 0:
                c = (v_e / v_s) ** (1 / (y_e - y_s)) - 1
                cagr_rows.append({"profession": profession, "period": label,
                                   "start_year": y_s, "end_year": y_e,
                                   "start_value": v_s, "end_value": v_e,
                                   "cagr_pct": round(c * 100, 3)})
    cagr_df = pl.DataFrame(cagr_rows)
    out5 = RESULTS / "ps001_cagr_by_profession.csv"
    cagr_df.write_csv(str(out5))
    logger.info(f"CAGR table → {out5}")
    print(cagr_df)
else:
    out5 = None


# ── Write baseline metrics summary ────────────────────────────────────────────
logger.info("=== Writing Baseline Metrics Summary ===")
rows = []
if len(merged) > 0:
    yc = year_col(nurses)
    for yr in [2006, 2012, 2018]:
        for prof in merged["profession"].unique().to_list():
            sub = merged.filter((pl.col(yc) == yr) & (pl.col("profession") == prof))
            if len(sub) == 0: continue
            rows.append({
                "year": yr,
                "profession": prof,
                "headcount": float(sub["headcount"][0]),
                "per_10k": round(float(sub["per_10k_population"][0]), 2) if "per_10k_population" in sub.columns and sub["per_10k_population"][0] is not None else None,
                "yoy_growth_pct": round(float(sub["yoy_growth_pct"][0]), 2) if "yoy_growth_pct" in sub.columns and sub["yoy_growth_pct"][0] is not None else None,
            })

if rows:
    metrics_df = pl.DataFrame(rows)
    baseline_path = RESULTS / "ps001_baseline_metrics.csv"
    metrics_df.write_csv(str(baseline_path))
    logger.info(f"Baseline metrics → {baseline_path}")
    print(metrics_df)
else:
    baseline_path = None
    metrics_df = pl.DataFrame()


# ── Notebook ──────────────────────────────────────────────────────────────────
NB_PATH = NB_DIR / "05_feature_engineering.ipynb"
nb = nbformat.v4.new_notebook()
cells_src = [
    f"import polars as pl\nfrom pathlib import Path\nWS = Path('{WS}')\nPROCESSED = WS/'problem-statements/ps-001-healthcare-system-baseline/data/4_processed'\nRESULTS = WS/'problem-statements/ps-001-healthcare-system-baseline/results/tables'\nprint('Paths set')",
    "wf = pl.read_parquet(str(PROCESSED/'workforce_headcount_long.parquet'))\nprint('Workforce long shape:', wf.shape)\nprint(wf.head())",
    "print('YoY growth rates by profession:')\nprint(wf.filter(pl.col('profession')=='nurses').select(['year','headcount','yoy_growth_pct']).tail(10))",
    "density = pl.read_parquet(str(PROCESSED/'workforce_density_per_10k.parquet'))\nprint('Density (nurses):')\nprint(density.filter(pl.col('profession')=='nurses').select(['year','headcount','per_10k_population']).tail(10))",
    "cagr = pl.read_csv(str(RESULTS/'ps001_cagr_by_profession.csv'))\nprint('CAGR by profession:')\nprint(cagr)",
    "beds = pl.read_parquet(str(PROCESSED/'beds_annual.parquet'))\nprint('Beds annual:')\nprint(beds.tail(10))",
    "baseline = pl.read_csv(str(RESULTS/'ps001_baseline_metrics.csv'))\nprint('Baseline metrics:')\nprint(baseline)",
]
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}
nbformat.write(nb, str(NB_PATH))

# ── Handoff JSON ───────────────────────────────────────────────────────────────
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
outputs = [
    {"path": str(out1), "type": "parquet", "description": "Workforce headcount long (all professions)"},
    {"path": str(out2), "type": "parquet", "description": "Population annual aggregate"},
    {"path": str(out3), "type": "parquet", "description": "Workforce density per 10k population"},
    {"path": str(out4), "type": "parquet", "description": "Beds annual aggregate + per-10k"},
    {"path": str(out5), "type": "csv", "description": "CAGR by profession"},
    {"path": str(baseline_path) if baseline_path else "", "type": "csv", "description": "Baseline metrics 2006/2012/2018"},
    {"path": str(NB_PATH), "type": "notebook", "description": "Feature engineering notebook"},
]
outputs = [o for o in outputs if o["path"]]

handoff = {
    "agent": "feature-engineer",
    "problem_statement": "ps-001-healthcare-system-baseline",
    "status": "success",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "outputs": outputs,
    "features_created": [
        "headcount_per_profession_per_year",
        "yoy_growth_pct",
        "per_10k_population",
        "beds_per_10k",
        "cagr_by_profession",
    ],
    "key_datasets": {
        "workforce_headcount_long": str(out1),
        "workforce_density_per_10k": str(out3),
        "beds_annual": str(out4),
        "cagr_table": str(out5),
        "baseline_metrics": str(baseline_path) if baseline_path else None,
    },
    "notes": f"Features engineering complete. Processed parquets in {PROCESSED}.",
}
HANDOFF_PATH = HANDOFF_DIR / f"features_to_dashboard_{TODAY}.json"
HANDOFF_PATH.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff JSON → {HANDOFF_PATH}")

print(f"\n{'='*62}")
print(f"  Processed parquets : {PROCESSED}")
print(f"  CAGR CSV           : {out5}")
print(f"  Baseline Metrics   : {baseline_path}")
print(f"  Notebook           : {NB_PATH}")
print(f"  Handoff JSON       : {HANDOFF_PATH}")
print(f"{'='*62}")
