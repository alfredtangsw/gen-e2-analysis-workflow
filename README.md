# gen-e2-analysis-workflow

End-to-end automated data analysis workflow for Singapore MOH healthcare data, driven by GitHub Copilot agents and structured prompts.

---

## Workflow Overview

```
Prompt 0 → Prompt 1 → Prompt 2 → Prompt 3 → executor.agent.md
  Setup     Problem    User        Impl.       Automated
  Project   Statements Stories     Plan        Execution
```

---

## Prerequisites

```bash
# Install uv (if not already installed)
pip install uv
```

---

## Step 1 — Attach Project Context

Before running any prompt, attach the following context documents in your GitHub Copilot Chat session so the agent has full project awareness:

| Document | Path | Purpose |
|---|---|---|
| Business Objectives | [docs/project-context/business-objectives.md](docs/project-context/business-objectives.md) | strategic goals, KPIs, and current analysis focus |
| Data Sources | [docs/project-context/data-sources.md](docs/project-context/data-sources.md) | dataset details, schema, and access methods |
| Tech Stack | [docs/project-context/tech-stack.md](docs/project-context/tech-stack.md) | Platform (Databricks/HEALIX), libraries (Polars, uv), and coding standards |

In Copilot Chat, use `#file:` references to include these:

```
#file:docs/project-context/business-objectives.md
#file:docs/project-context/data-sources.md
#file:docs/project-context/tech-stack.md
```

---

## Step 2 — Execute Prompts 0 → 3 (in order)

Run each prompt sequentially in GitHub Copilot Chat using `/` to invoke them. Each prompt builds on the outputs of the previous one.

### Prompt 0 — Project Initialization
**File**: [.github/prompts/0-start-gen-e2-data-analysis-project.prompt.md](.github/prompts/0-start-gen-e2-data-analysis-project.prompt.md)

Sets up the project folder structure, virtual environment, and base configuration. Answers questions about the target platform, data volume, and stakeholders.

```
/0-start-gen-e2-data-analysis-project
```

**Outputs**: Folder structure, `.env.example`, `requirements.txt`, `README.md` updates.

---

### Prompt 1 — Identify Problem Statements
**File**: [.github/prompts/1-identify-problem-statement.prompt.md](.github/prompts/1-identify-problem-statement.prompt.md)

Analyzes business context to surface and prioritize actionable analytics problem statements, constrained by actual data availability.

```
/1-identify-problem-statement
```

**Outputs**: `docs/objectives/problem_statements/ps-{num}-{name}.md` files.

---

### Prompt 2 — Generate User Stories
**File**: [.github/prompts/2-generate-user-stories-from-problem_statement.prompt.md](.github/prompts/2-generate-user-stories-from-problem_statement.prompt.md)

Decomposes every problem statement into sprint-ready user stories covering extraction, cleaning, EDA, feature engineering, modelling, and dashboards.

```
/2-generate-user-stories-from-problem_statement
```

**Outputs**: `docs/objectives/user_stories/problem-statement-{num}-{name}/` story files.

---

### Prompt 3 — Generate Implementation Plan
**File**: [.github/prompts/3-generate-data-analysis-implementation-plan.prompt.md](.github/prompts/3-generate-data-analysis-implementation-plan.prompt.md)

Creates a detailed, executable implementation plan for each user story. Evaluates model options (Hugging Face, statsmodels, scikit-learn) and appends the plan directly to the user story file.

```
/3-generate-data-analysis-implementation-plan
```

**Outputs**: Implementation plan sections appended to each user story file.

---

## Step 3 — Execute the Implementation (executor.agent.md)

**File**: [.github/agents/executor.agent.md](.github/agents/executor.agent.md)

The executor orchestrates the full pipeline by spawning specialized subagents for each phase. Run it in Copilot Chat, passing the problem statement number and name:

```
#executor.agent.md ps-001-healthcare-workforce-sustainability
```

### Execution Phases

| Phase | Agent(s) | Description |
|---|---|---|
| 1 | `data-extractor` | Download and extract raw data via Kaggle API |
| 2 | `data-cleaning` + `data-validation` | Clean datasets and validate schema/quality (parallel) |
| 3 | `exploratory-analysis` + `feature-engineer` | EDA, trend analysis, and feature construction (parallel) |
| 4 | `model-forecasting` | Train and evaluate forecasting models |
| 5 | `dashboard-visualization` | Build interactive HTML dashboard |
| 6 | `code-simplifier` → `code-reviewer` | Quality gate: simplify code, then execute all notebooks end-to-end |

Each phase writes a handoff JSON to `docs/agent-handoffs/{phase}/ps-{num}-{name}/` before the next phase begins.

### Verify Completion

After the executor finishes, check:

```bash
# Confirm handoff files exist for all phases
ls docs/agent-handoffs/*/ps-001-healthcare-workforce-sustainability/

# Confirm notebooks are non-empty
du -sh problem-statement/ps-001-healthcare-workforce-sustainability/notebooks/*.ipynb

# Confirm processed data exists
ls problem-statement/ps-001-healthcare-workforce-sustainability/data/4_processed/
```

---

## Local Environment Setup

```bash
# 1 — Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2 — Create and activate virtual environment
uv venv .venv --python 3.11
source .venv/bin/activate  # macOS / Linux

# 3 — Install dependencies
uv pip install -r requirements.txt

# 4 — Copy and fill in environment variables
cp .env.example .env
# Edit .env and set KAGGLE_USERNAME and KAGGLE_KEY
```

---

## Project Structure

```
.
├── .env.example               # Environment variable template (copy to .env)
├── requirements.txt           # Python dependencies
├── .github/
│   ├── prompts/               # Prompts 0-3 (run in order)
│   ├── agents/                # Specialist agents (executor + subagents)
│   ├── skills/                # Reusable skill instructions
│   └── copilot-instructions.md
├── docs/
│   ├── project-context/       # business-objectives, data-sources, tech-stack ← attach these
│   ├── objectives/
│   │   ├── problem_statements/  # ps-{num}-{name}.md
│   │   └── user_stories/        # Generated by Prompt 2
│   ├── agent-handoffs/          # Phase-to-phase communication JSONs
│   └── domain-knowledge/        # Healthcare metrics, forecasting guides
├── shared/                    # SHARED INFRASTRUCTURE (write once, use everywhere)
│   ├── src/                   # Reusable library code
│   │   ├── data_processing/   # ETL, cleaning, validation, Kaggle extractor
│   │   ├── analysis/          # Statistical algorithms, trend detection
│   │   ├── models/            # Forecasting utilities, evaluation metrics
│   │   ├── visualization/     # Chart generators
│   │   ├── orchestration/     # Multi-agent pipeline helpers
│   │   └── utils/             # Config loader, logger setup
│   ├── data/
│   │   ├── 1_raw/             # Original immutable source data (READ-ONLY)
│   │   └── 2_external/        # Reference data (demographics, benchmarks)
│   ├── sql/                   # SQL views, stored procedures, extraction queries
│   ├── config/
│   │   ├── base.yml           # Base project settings
│   │   └── databricks.yml     # HEALIX/Databricks platform settings
│   └── tests/                 # Unit tests for shared code
└── problem-statements/        # SELF-CONTAINED ANALYSES (one folder per problem)
    ├── ps-001-healthcare-workforce/
    ├── ps-002-disease-burden/
    └── ps-003-healthcare-capacity/
        ├── notebooks/         # Interactive exploration (Jupyter)
        ├── src/               # Problem-specific helpers (imports shared/)
        ├── data/3_interim/    # Intermediate outputs
        ├── data/4_processed/  # Final analysis-ready datasets
        ├── results/           # Tables, metrics, stakeholder exports
        ├── reports/           # Figures, dashboards, presentations
        ├── models/            # Trained model artefacts
        ├── config/config.yml  # Analysis parameters
        ├── scripts/           # End-to-end pipeline runner
        ├── tests/             # Integration tests
        └── logs/              # ETL and error logs
```

---

## Key References

- [docs/project-context/business-objectives.md](docs/project-context/business-objectives.md) — MOH strategic goals
- [docs/project-context/data-sources.md](docs/project-context/data-sources.md) — Dataset schema and access
- [docs/project-context/tech-stack.md](docs/project-context/tech-stack.md) — Platform and library standards
- [.github/copilot-instructions.md](.github/copilot-instructions.md) — Coding conventions (Polars, uv, loguru)
- [.github/agents/executor.agent.md](.github/agents/executor.agent.md) — Full pipeline executor
