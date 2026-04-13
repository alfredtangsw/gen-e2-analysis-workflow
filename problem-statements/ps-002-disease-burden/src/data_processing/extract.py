"""
Extract Phase — PS-002 Disease Burden Temporal Trends Analysis
Generates 5 synthetic raw datasets seeded from Singapore MOH epidemiological benchmarks.
Outputs written to shared/data/1_raw/mortality/.
"""
import numpy as np
import polars as pl
from pathlib import Path

np.random.seed(42)

BASE  = Path(__file__).resolve().parents[4]
RAW   = BASE / "shared/data/1_raw/mortality"
RAW.mkdir(parents=True, exist_ok=True)

YEARS = list(range(1990, 2020))       # 30-year window
SEX   = ["Male", "Female", "Total"]
N     = len(YEARS)
rng   = np.random.default_rng(42)


def _trend(start: float, end: float, noise: float = 0.02) -> np.ndarray:
    """Generate a smooth declining series from start to end with small noise."""
    t = np.linspace(0, 1, N)
    base = start * (end / start) ** t
    return base * (1 + rng.normal(0, noise, N))


def extract_cancer_mortality() -> pl.DataFrame:
    """Cancer ASMR 1990-2019 by sex (per 100,000). Male higher, declining slower."""
    rows = []
    for sex, s, e in [("Male", 280, 165), ("Female", 155, 135), ("Total", 215, 149)]:
        rates = _trend(s, e, noise=0.018)
        for i, y in enumerate(YEARS):
            rows.append({"year": y, "sex": sex, "disease": "cancer",
                         "asmr_per_100k": round(float(rates[i]), 2)})
    return pl.DataFrame(rows)


def extract_stroke_mortality() -> pl.DataFrame:
    """Stroke ASMR 1990-2019 by sex. Dramatic 73% overall decline."""
    rows = []
    for sex, s, e in [("Male", 145, 40), ("Female", 115, 30), ("Total", 130, 35)]:
        rates = _trend(s, e, noise=0.022)
        for i, y in enumerate(YEARS):
            rows.append({"year": y, "sex": sex, "disease": "stroke",
                         "asmr_per_100k": round(float(rates[i]), 2)})
    return pl.DataFrame(rows)


def extract_ihd_mortality() -> pl.DataFrame:
    """IHD ASMR 1990-2019 by sex. Inflection post-2000 (statins). ~75% decline."""
    rows = []
    # IHD has a steeper decline post-2000; reflect via piecewise
    for sex, s_early, mid, e in [("Male", 350, 200, 90),
                                   ("Female", 290, 160, 70),
                                   ("Total", 320, 180, 80)]:
        early = _trend(s_early, mid, noise=0.025)[:11]   # 1990-2000 (11 pts)
        late  = _trend(mid, e,   noise=0.020)[1:]         # 2001-2019 (19 pts)
        rates = np.concatenate([early, late])
        for i, y in enumerate(YEARS):
            rows.append({"year": y, "sex": sex, "disease": "ischaemic_heart_disease",
                         "asmr_per_100k": round(float(rates[i]), 2)})
    return pl.DataFrame(rows)


def extract_hospital_admissions() -> pl.DataFrame:
    """Hospital admission rates by age group and sex (per 100,000), 1990-2019."""
    age_groups = ["0-4", "5-14", "15-24", "25-34", "35-44",
                  "45-54", "55-64", "65-74", "75-84", "85+"]
    base_rates = [2800, 800, 650, 1200, 1800, 3500, 5500, 8200, 12000, 17000]
    rows = []
    for ag, base in zip(age_groups, base_rates):
        for sex in ["Male", "Female"]:
            sex_mult = 1.08 if sex == "Male" else 0.94
            rates = _trend(base * sex_mult, base * sex_mult * 0.85, noise=0.03)
            for i, y in enumerate(YEARS):
                rows.append({"year": y, "age_group": ag, "sex": sex,
                             "admission_rate_per_100k": round(float(rates[i]), 1)})
    return pl.DataFrame(rows)


def extract_vaccination() -> pl.DataFrame:
    """Vaccination coverage by programme, 1990-2019."""
    programmes = ["BCG", "Hepatitis B", "Diphtheria", "Tetanus",
                  "Pertussis", "Polio", "MMR", "Varicella"]
    base_cov = [97.5, 92.0, 96.0, 95.5, 95.0, 97.0, 91.0, 0.0]
    intro_yr = [1990, 1990, 1990, 1990, 1990, 1990, 1990, 2000]
    rows = []
    for prog, cov, intro in zip(programmes, base_cov, intro_yr):
        for y in YEARS:
            if y < intro:
                rate = 0.0
            elif y == intro and cov == 0.0:
                rate = 45.0
            else:
                delta = min(cov, cov + rng.normal(0, 0.8))
                t_since = y - intro
                rate = min(99.9, delta + t_since * 0.15 + rng.normal(0, 0.5))
                rate = max(0.0, rate)
            rows.append({"year": y, "programme": prog,
                         "coverage_pct": round(float(rate), 1)})
    return pl.DataFrame(rows)


def run() -> None:
    """Extract all 5 raw disease burden datasets."""
    datasets = {
        "age-standardised-mortality-rate-for-cancer": extract_cancer_mortality(),
        "age-standardised-mortality-rate-for-stroke": extract_stroke_mortality(),
        "age-standardised-mortality-rate-for-ischaemic-heart-disease": extract_ihd_mortality(),
        "hospital-admission-rate-by-age-and-sex": extract_hospital_admissions(),
        "vaccination-and-immunisation-of-students-annual": extract_vaccination(),
    }
    for name, df in datasets.items():
        path = RAW / f"{name}.csv"
        df.write_csv(path)
        print(f"  Wrote {path.name}: {df.shape}")
    print(f"Extraction complete → {RAW}")


if __name__ == "__main__":
    run()
