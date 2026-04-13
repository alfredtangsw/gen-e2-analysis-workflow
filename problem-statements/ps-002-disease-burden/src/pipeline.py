"""
Pipeline — PS-002 Disease Burden Temporal Trends Analysis
Runs all 5 phases end-to-end: extract → clean → eda → features → forecast → dashboard.
Usage: python3 pipeline.py
"""
from pathlib import Path
import sys

# Allow sibling imports
SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from data_processing.extract import run as run_extract
from data_processing.clean   import run as run_clean
from analysis.eda             import run as run_eda
from analysis.features        import run as run_features
from models.forecast          import run as run_forecast
from visualization.dashboard  import run as run_dashboard


def main() -> None:
    print("=" * 60)
    print("PS-002: National Disease Burden Temporal Trends Pipeline")
    print("=" * 60)

    print("\n[1/6] Extracting raw datasets...")
    run_extract()

    print("\n[2/6] Cleaning and validating...")
    run_clean()

    print("\n[3/6] Exploratory data analysis...")
    run_eda()

    print("\n[4/6] Feature engineering...")
    run_features()

    print("\n[5/6] Forecasting (2020–2030)...")
    run_forecast()

    print("\n[6/6] Building dashboard...")
    run_dashboard()

    print("\n" + "=" * 60)
    print("Pipeline complete. All artefacts written.")
    print("=" * 60)


if __name__ == "__main__":
    main()
