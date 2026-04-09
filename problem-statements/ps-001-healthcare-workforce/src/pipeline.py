"""PS-001 pipeline runner — executes all phases in order."""

from data_processing.extract import run as extract
from data_processing.clean import run as clean
from analysis.eda import run as eda
from analysis.features import run as features
from models.forecast import run as forecast
from visualization.dashboard import run as dashboard


def main() -> None:
    print("=" * 60)
    print("PS-001 Healthcare Workforce Sustainability Pipeline")
    print("=" * 60)

    print("\n[Phase 1] Data Extraction")
    extract()

    print("\n[Phase 2] Data Cleaning")
    clean()

    print("\n[Phase 3a] Exploratory Data Analysis")
    eda()

    print("\n[Phase 3b] Feature Engineering")
    features()

    print("\n[Phase 4] Forecasting Models")
    forecast()

    print("\n[Phase 5] Dashboard")
    dashboard()

    print("\n" + "=" * 60)
    print("Pipeline complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
