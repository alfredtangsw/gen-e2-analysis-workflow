"""
EDA Phase — PS-002 Disease Burden Temporal Trends Analysis
Computes ASMR trend statistics, APC, gender gap, joinpoint detection,
and international benchmarking. Writes results to results/tables/.
"""
import polars as pl
import numpy as np
from pathlib import Path
from datetime import date

PS      = Path(__file__).resolve().parents[3]
PROC    = PS / "data/4_processed"
RESULTS = PS / "results/tables"
RESULTS.mkdir(parents=True, exist_ok=True)

STAMP = date.today().strftime("%Y%m%d")

# WHO global and OECD high-income 2019 benchmarks (per 100k)
BENCHMARKS = {
    "cancer":                   {"who": 175.0, "oecd": 144.0},
    "stroke":                   {"who": 85.0,  "oecd": 38.0},
    "ischaemic_heart_disease":  {"who": 120.0, "oecd": 88.0},
}


def compute_apc(years: list, rates: list) -> float:
    """Average Annual Percent Change via log-linear regression on full series."""
    x = np.array(years, dtype=float)
    y = np.log(np.array(rates, dtype=float))
    b = np.polyfit(x - x[0], y, 1)[0]
    return round(float(np.expm1(b)) * 100, 3)


def compute_cagr(start: float, end: float, n_years: int) -> float:
    return round((end / start) ** (1 / n_years) - 1, 4) * 100


def eda_summary(master: pl.DataFrame) -> pl.DataFrame:
    """Per-disease APC, CAGR, start/end ASMR, trend direction."""
    rows = []
    for d in master["disease"].unique().sort().to_list():
        sub = master.filter(pl.col("disease") == d).sort("year")
        years = sub["year"].to_list()
        rates = sub["asmr_per_100k"].to_list()
        asmr_1990 = rates[0]
        asmr_2019 = rates[-1]
        apc = compute_apc(years, rates)
        cagr = compute_cagr(asmr_1990, asmr_2019, len(rates) - 1)
        total_chg = round((asmr_2019 / asmr_1990 - 1) * 100, 2)
        rows.append({
            "disease": d,
            "asmr_1990": round(asmr_1990, 1),
            "asmr_2019": round(asmr_2019, 1),
            "apc_pct": apc,
            "cagr_pct": round(cagr, 3),
            "total_change_pct": total_chg,
            "trend_direction": "DECLINING" if apc < 0 else "INCREASING",
        })
    df = pl.DataFrame(rows)
    df.write_csv(RESULTS / "disease_burden_eda_summary.csv")
    return df


def gender_gap(cancer: pl.DataFrame, stroke: pl.DataFrame, ihd: pl.DataFrame) -> pl.DataFrame:
    """Male vs Female ASMR in 2019 with M:F ratio."""
    rows = []
    datasets = {"cancer": cancer, "stroke": stroke, "ischaemic_heart_disease": ihd}
    for d, df in datasets.items():
        sub = df.filter(pl.col("year") == 2019)
        male   = sub.filter(pl.col("sex") == "Male")["asmr_per_100k"][0]
        female = sub.filter(pl.col("sex") == "Female")["asmr_per_100k"][0]
        rows.append({
            "disease": d,
            "male_asmr_2019":   round(float(male), 1),
            "female_asmr_2019": round(float(female), 1),
            "mf_ratio":         round(float(male) / float(female), 2),
        })
    df = pl.DataFrame(rows)
    df.write_csv(RESULTS / "gender_gap_2019.csv")
    return df


def joinpoint_analysis(master: pl.DataFrame) -> pl.DataFrame:
    """Detect single inflection year per disease (year with largest APC discontinuity)."""
    rows = []
    for d in master["disease"].unique().sort().to_list():
        sub = master.filter(pl.col("disease") == d).sort("year")
        years = sub["year"].to_list()
        rates = sub["asmr_per_100k"].to_numpy()
        best_yr, best_diff = None, 0.0
        for i in range(3, len(rates) - 3):
            early_apc = compute_apc(years[:i+1], rates[:i+1].tolist())
            late_apc  = compute_apc(years[i:],   rates[i:].tolist())
            diff = abs(late_apc - early_apc)
            if diff > best_diff:
                best_diff = diff
                best_yr = years[i]
        rows.append({"disease": d, "inflection_year": best_yr,
                     "apc_discontinuity": round(best_diff, 3)})
    df = pl.DataFrame(rows)
    df.write_csv(RESULTS / "joinpoint_analysis.csv")
    return df


def international_benchmarking(master: pl.DataFrame) -> pl.DataFrame:
    """Compare 2019 Singapore ASMR vs WHO Global and OECD high-income."""
    rows = []
    for d in master["disease"].unique().sort().to_list():
        sg = float(master.filter((pl.col("disease") == d) & (pl.col("year") == 2019))["asmr_per_100k"][0])
        bm = BENCHMARKS.get(d, {})
        who  = bm.get("who", None)
        oecd = bm.get("oecd", None)
        rows.append({
            "disease": d,
            "singapore_2019": round(sg, 1),
            "who_global_2019": who,
            "oecd_high_income_2019": oecd,
            "vs_who_pct":  round((sg / who  - 1) * 100, 1) if who  else None,
            "vs_oecd_pct": round((sg / oecd - 1) * 100, 1) if oecd else None,
        })
    df = pl.DataFrame(rows)
    df.write_csv(RESULTS / "international_benchmarking.csv")
    return df


def run() -> None:
    master = pl.read_parquet(PROC / "mortality_master_clean.parquet")
    cancer = pl.read_parquet(PROC / "cancer_mortality_clean.parquet")
    stroke = pl.read_parquet(PROC / "stroke_mortality_clean.parquet")
    ihd    = pl.read_parquet(PROC / "ihd_mortality_clean.parquet")

    summary = eda_summary(master)
    print(f"  EDA summary: {summary.shape}")
    gender_gap(cancer, stroke, ihd)
    joinpoint_analysis(master)
    international_benchmarking(master)
    print(f"EDA phase complete → {RESULTS}")


if __name__ == "__main__":
    run()
