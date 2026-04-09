# TODO — Singapore Healthcare Analysis (gen-e2)

> **Platform**: HEALIX / Databricks | **Python**: 3.11 | **Package manager**: uv
> **Owner**: Alfred | **Status key**: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Environment & Infrastructure

- [x] Install `uv` package manager
- [x] Create Python 3.11 virtual environment (`.venv`)
- [x] Create `requirements.txt` with all core dependencies
- [x] Create `.env.example` with credential templates
- [x] Create hybrid project folder structure (`shared/` + `problem-statements/`)
- [x] Create `shared/config/base.yml` and `shared/config/databricks.yml`
- [ ] Add KAGGLE_USERNAME / KAGGLE_KEY to local `.env` file (Alfred)
- [ ] Validate Kaggle credentials via `test_kaggle_credentials()` helper
- [ ] Configure Databricks connection for HEALIX deployment (when needed)

---

## Data Acquisition

- [ ] Identify Singapore healthcare datasets on Kaggle (disease, workforce, capacity)
- [ ] Run `kaggle_extractor.py` to download datasets into `shared/data/1_raw/`
- [ ] Verify raw files are immutable (read-only file permissions)
- [ ] Log extraction results (file sizes, row counts, timestamps) to `logs/etl/`
- [ ] Identify supplementary external reference data (SingStat demographics, WHO benchmarks)
- [ ] Download external reference data to `shared/data/2_external/`

---

## Data Validation & Quality

- [ ] Write data quality checks for each raw dataset using `shared/src/data_processing/validation.py`
- [ ] Generate quality reports to `logs/etl/` for all raw datasets
- [ ] Document known limitations and anomalies in `docs/data-dictionary/`
- [ ] Create schema contracts in `shared/data/schemas/`
- [ ] Write unit tests for validation functions in `shared/tests/unit/`

---

## ps-001 — Healthcare Workforce Sustainability

- [ ] Extract workforce dataset from Kaggle / MOH data
- [ ] Clean and standardise workforce data (null handling, dtype casting)
- [ ] Perform EDA: headcount trends, speciality mix, region distribution
- [ ] Engineer forecast features (lag, rolling mean, population ratios)
- [ ] Build demand forecasting models (ARIMA / Prophet / XGBoost)
- [ ] Evaluate models (MAPE, RMSE) and select best performer
- [ ] Generate results tables to `problem-statements/ps-001-healthcare-workforce/results/tables/`
- [ ] Build interactive HTML dashboard to `problem-statements/ps-001-healthcare-workforce/reports/dashboards/`
- [ ] Write integration tests to `problem-statements/ps-001-healthcare-workforce/tests/integration/`
- [ ] Review notebook outputs end-to-end before marking complete

---

## ps-002 — Disease Burden Temporal Trends

- [ ] Extract disease surveillance dataset from Kaggle / MOH data
- [ ] Clean and standardise disease data (disease names → Categorical, date parsing)
- [ ] Perform EDA: top diseases by burden, temporal trends, seasonal patterns
- [ ] Engineer temporal features (year-over-year change, rolling burden index)
- [ ] Build disease prevalence forecasting models
- [ ] Evaluate models and quantify uncertainty (confidence intervals)
- [ ] Generate results tables to `problem-statements/ps-002-disease-burden/results/tables/`
- [ ] Build interactive HTML dashboard to `problem-statements/ps-002-disease-burden/reports/dashboards/`
- [ ] Write integration tests to `problem-statements/ps-002-disease-burden/tests/integration/`
- [ ] Review notebook outputs end-to-end before marking complete

---

## ps-003 — Healthcare Capacity Optimisation

- [ ] Extract healthcare capacity dataset (beds, facilities, utilisation)
- [ ] Clean and standardise capacity data
- [ ] Perform EDA: capacity utilisation rates, regional gaps, trends
- [ ] Cross-join workforce and disease burden outputs for demand-supply gap analysis
- [ ] Build capacity optimisation model
- [ ] Generate actionable recommendations for resource reallocation
- [ ] Generate results tables to `problem-statements/ps-003-healthcare-capacity/results/tables/`
- [ ] Build interactive HTML dashboard to `problem-statements/ps-003-healthcare-capacity/reports/dashboards/`
- [ ] Write integration tests to `problem-statements/ps-003-healthcare-capacity/tests/integration/`
- [ ] Review notebook outputs end-to-end before marking complete

---

## Shared Library (`shared/src/`)

- [ ] Implement `shared/src/analysis/trend_detection.py` (Mann-Kendall, seasonal decomposition)
- [ ] Implement `shared/src/models/evaluation.py` (MAPE, RMSE, cross-validation helpers)
- [ ] Implement `shared/src/visualization/chart_generators.py` (Plotly wrappers)
- [ ] Implement `shared/src/orchestration/pipeline.py` (phase runner)
- [ ] Write unit tests for all shared modules (target: ≥ 80% coverage)
- [ ] Run `pytest --cov=shared/src shared/tests/` and review coverage report

---

## Code Quality & Review

- [ ] Configure `ruff` linter (create `ruff.toml` or `pyproject.toml` section)
- [ ] Run `ruff check .` before each PR and fix all warnings
- [ ] Run `code-reviewer` agent on each problem statement's notebooks and scripts
- [ ] Run `code-simplifier` agent to reduce complexity before final submission
- [ ] Confirm no hardcoded credentials or secrets in committed code (audit with `git grep`)

---

## Documentation & Reporting

- [ ] Review and update `docs/data-dictionary/disease_data.md` after data acquisition
- [ ] Review and update `docs/data-dictionary/workforce-forecast-features.md`
- [ ] Review `docs/data-dictionary/external_reference.md` with actual external files
- [ ] Create `docs/data-dictionary/capacity_data.md` for ps-003
- [ ] Update `docs/index.md` Phase 1-3 checklist as tasks are completed
- [ ] Produce executive summary PDF for each problem statement after dashboard build

---

## DevOps & Security

- [ ] Verify `.gitignore` excludes `.env`, `.venv/`, `__pycache__/`, `*.pkl`, `shared/data/1_raw/`
- [ ] Ensure `shared/data/1_raw/` files have read-only permissions after download
- [ ] Add pre-commit hook: `ruff check` + `pytest shared/tests/unit/` before every commit
- [ ] Document Databricks job setup in `shared/config/databricks.yml` when deploying to HEALIX
- [ ] Rotate Kaggle API key if it is ever accidentally committed
