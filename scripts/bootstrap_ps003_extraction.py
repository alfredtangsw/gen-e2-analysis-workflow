"""PS-003 Phase 1: Data Extraction — Load PS-001/PS-002 outputs + planning constants.

Inputs:
  PS-001: workforce_headcount_long.parquet, workforce_density_per_10k.parquet,
          beds_annual.parquet, population_annual.parquet, ps001_baseline_metrics.csv,
          ps001_cagr_by_profession.csv
  PS-002: ps002_forecasts_2021_2030.csv, ps002_model_metrics.csv
  Config: shared/config/base.yml → planning_constants
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
import yaml
from loguru import logger

WS = Path("/Users/alfredtang/Documents/Projects/gen-e2/gen-e2-analysis-workflow")
PS001 = WS / "problem-statements/ps-001-healthcare-system-baseline"
PS002 = WS / "problem-statements/ps-002-healthcare-demand-forecasting"
PS_DIR = WS / "problem-statements/ps-003-integrated-resource-planning"
RESULTS = PS_DIR / "results/tables"
LOGS = PS_DIR / "logs/etl"
NB_DIR = PS_DIR / "notebooks"
HANDOFF_DIR = WS / "docs/agent-handoffs/extraction/ps-003-integrated-resource-planning"
for d in [RESULTS, LOGS, NB_DIR, HANDOFF_DIR,
          PS_DIR / "data/3_interim", PS_DIR / "data/4_processed",
          PS_DIR / "reports/figures", PS_DIR / "reports/dashboards",
          PS_DIR / "results/metrics", PS_DIR / "results/exports"]:
    d.mkdir(parents=True, exist_ok=True)

TS = datetime.now().strftime("%Y%m%d_%H%M%S")
logger.remove()
logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
logger.add(str(LOGS / f"extraction_{TS}.log"), level="DEBUG")
logger.info("PS-003 data extraction started")

# ── Load planning constants from config ──────────────────────────────────────
CONFIG_PATH = WS / "shared/config/base.yml"
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)
planning = config["planning_constants"]
logger.info(f"Planning constants loaded: {list(planning.keys())}")

# ── Define inputs ────────────────────────────────────────────────────────────
INPUTS = [
    # (path, domain, description)
    (PS001 / "data/4_processed/workforce_headcount_long.parquet", "ps001", "Workforce headcount long (5 professions)"),
    (PS001 / "data/4_processed/workforce_density_per_10k.parquet", "ps001", "Workforce density per 10k"),
    (PS001 / "data/4_processed/beds_annual.parquet", "ps001", "Acute beds annual"),
    (PS001 / "data/4_processed/population_annual.parquet", "ps001", "Population annual"),
    (PS001 / "results/tables/ps001_baseline_metrics.csv", "ps001", "Baseline metrics"),
    (PS001 / "results/tables/ps001_cagr_by_profession.csv", "ps001", "CAGR by profession"),
    (PS001 / "results/tables/ps001_eda_summary.csv", "ps001", "EDA summary"),
    (PS002 / "results/tables/ps002_forecasts_2021_2030.csv", "ps002", "Demand forecasts 2021–2030"),
    (PS002 / "results/metrics/ps002_model_metrics.csv", "ps002", "Model metrics"),
]

def profile_input(path: Path, domain: str, desc: str) -> dict:
    try:
        if path.suffix == ".parquet":
            df = pl.read_parquet(str(path))
        else:
            df = pl.read_csv(str(path))
        yc = next((c for c in df.columns if c.lower() == "year"), None)
        yr_min = yr_max = None
        if yc:
            ys = df[yc].drop_nulls().cast(pl.Int64, strict=False).drop_nulls()
            if ys.len() > 0:
                yr_min, yr_max = int(ys.min()), int(ys.max())
        null_total = sum(df[c].null_count() for c in df.columns)
        logger.info(f"  ✅ {path.name}: {df.height} rows | {yr_min}–{yr_max} | nulls={null_total} | {desc}")
        return {"file": path.name, "domain": domain, "description": desc,
                "rows": df.height, "cols": df.width, "year_min": yr_min, "year_max": yr_max,
                "null_count": null_total, "load_status": "OK", "path": str(path)}
    except Exception as e:
        logger.error(f"  ❌ FAILED {path.name}: {e}")
        return {"file": path.name, "domain": domain, "description": desc,
                "rows": None, "cols": None, "year_min": None, "year_max": None,
                "null_count": None, "load_status": f"ERROR: {e}", "path": str(path)}

logger.info("Profiling inputs …")
profiles = [profile_input(p, d, desc) for p, d, desc in INPUTS]

# ── Reconciliation report ─────────────────────────────────────────────────────
recon_df = pl.DataFrame({k: [p[k] for p in profiles]
                          for k in ["file", "domain", "description", "rows", "year_min", "year_max", "null_count", "load_status"]})
RECON_PATH = LOGS / "ps003_input_reconciliation.csv"
recon_df.write_csv(str(RECON_PATH))
logger.info(f"Reconciliation report → {RECON_PATH}")

# ── Also write to results/tables for easy reference ──────────────────────────
RECON_RESULTS = RESULTS / "ps003_input_reconciliation.csv"
recon_df.write_csv(str(RECON_RESULTS))

failed = [p["file"] for p in profiles if p["load_status"] != "OK"]
gate = "FAILED" if failed else "PASSED"
logger.info(f"\nInputs loaded: {len(profiles)} | Failures: {failed} | Gate: {gate}")

# ── Planning constants summary ────────────────────────────────────────────────
constants_df = pl.DataFrame({
    "key": list(planning.keys()),
    "value": [str(v) for v in planning.values()],
})
CONST_PATH = RESULTS / "ps003_planning_constants.csv"
constants_df.write_csv(str(CONST_PATH))
logger.info(f"Planning constants → {CONST_PATH}")

# ── Notebook ──────────────────────────────────────────────────────────────────
import nbformat
NB_PATH = NB_DIR / "01_data_extraction.ipynb"
cells_src = [
    f"# PS-003 Integrated Resource Planning — Data Extraction\nimport polars as pl\nimport yaml\nfrom pathlib import Path\nWS = Path('{WS}')\nPS001 = WS / 'problem-statements/ps-001-healthcare-system-baseline'\nPS002 = WS / 'problem-statements/ps-002-healthcare-demand-forecasting'\nPS_DIR = WS / 'problem-statements/ps-003-integrated-resource-planning'\nprint('Paths set')",
    "# Load planning constants\nwith open(str(WS / 'shared/config/base.yml')) as f:\n    config = yaml.safe_load(f)\nplanning = config['planning_constants']\nprint('Planning constants:', planning)",
    "# Load PS-001 outputs\nwf = pl.read_parquet(str(PS001 / 'data/4_processed/workforce_headcount_long.parquet'))\nbeds = pl.read_parquet(str(PS001 / 'data/4_processed/beds_annual.parquet'))\npop = pl.read_parquet(str(PS001 / 'data/4_processed/population_annual.parquet'))\ncagr = pl.read_csv(str(PS001 / 'results/tables/ps001_cagr_by_profession.csv'))\nprint('WF:', wf.shape, '| Beds:', beds.shape, '| Pop:', pop.shape)\nprint(cagr)",
    "# Load PS-002 outputs\nforecasts = pl.read_csv(str(PS002 / 'results/tables/ps002_forecasts_2021_2030.csv'))\nprint('PS002 forecasts:', forecasts.shape)\nprint(forecasts.head(10))",
    "# Reconciliation report\nrecon = pl.read_csv(str(PS_DIR / 'results/tables/ps003_input_reconciliation.csv'))\nprint(recon)",
]
nb = nbformat.v4.new_notebook()
nb.cells = [nbformat.v4.new_code_cell(s) for s in cells_src]
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}}
nbformat.write(nb, str(NB_PATH))

# ── Handoff ───────────────────────────────────────────────────────────────────
TODAY = datetime.now(timezone.utc).strftime("%Y%m%d")
handoff = {
    "agent": "data-extractor",
    "problem_statement": "ps-003-integrated-resource-planning",
    "status": "success" if not failed else "failed",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "outputs": [
        {"path": str(RECON_PATH), "type": "csv", "description": "Input reconciliation report"},
        {"path": str(CONST_PATH), "type": "csv", "description": "Planning constants"},
        {"path": str(NB_PATH), "type": "notebook"},
    ],
    "inputs_loaded": len(profiles),
    "failed_inputs": failed,
    "planning_constants": planning,
    "ps001_processed_dir": str(PS001 / "data/4_processed"),
    "ps002_results_dir": str(PS002 / "results/tables"),
    "gate": gate,
    "next_agent": "data-validation",
}
HP = HANDOFF_DIR / f"extraction_to_validation_{TODAY}.json"
HP.write_text(json.dumps(handoff, indent=2))
logger.info(f"Handoff → {HP}")

print(f"\n{'='*60}")
print(f"  Inputs profiled : {len(profiles)}")
print(f"  Failures        : {failed or 'None'}")
print(f"  Gate            : {gate}")
print(f"{'='*60}")
