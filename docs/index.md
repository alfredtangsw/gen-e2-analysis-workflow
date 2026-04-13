# Gen-E2 Documentation Hub

> **Complete documentation for Singapore Health Trends Analysis project**

Welcome to the Gen-E2 documentation. This page serves as the central navigation point for all project documentation, technical specifications, and development guidelines.

---

## 🚀 Quick Start

### New to the Project?
1. **[README](../README.md)** - Project overview and setup instructions
2. **[Business Objectives](project_context/business-objectives.md)** - Understand the "why"
3. **[Tech Stack](project_context/tech-stack.md)** - Technology platform and tools
4. **[TODO Task Tracker](../TODO.md)** - Current tasks and progress

### Starting a New Analysis?
1. Review existing **[Problem Statements](objectives/problem_statements/)**
2. Check **[Data Dictionary](data_dictionary/index.md)** for available datasets
3. Follow **[Data Analysis Best Practices](../.github/instructions/data-analysis-best-practices.instructions.md)**
4. Use hybrid structure: `problem-statements/ps-{num}-{name}/`

---

## 📚 Documentation Sections

### 1️⃣ Project Context & Goals

**Understanding the Business Need**

| Document | Description |
|----------|-------------|
| [Business Objectives](project_context/business-objectives.md) | MOH strategic goals and KPIs |
| [Data Sources](project_context/data-sources.md) | Available datasets and acquisition methods |
| [Tech Stack](project_context/tech-stack.md) | HEALIX/Databricks platform specifications |

**Stakeholder Requirements**
- **Policy Makers**: Evidence for health policy formulation
- **Government Officials**: Strategic planning and resource allocation
- **Team Heads**: Operational decisions and program prioritization

---

### 2️⃣ Problem Statements & Analysis

**Defined Problems We're Solving**

📁 **Location**: `docs/objectives/problem_statements/`

Current problem statements:

> These three problem statements form a sequential pipeline — each feeds the next. All analyses are constrained to the verified Kaggle Singapore Health Dataset (2006–2020) plus identified public external sources (SingStat, WHO GHO, MOM wages). See [PS README](objectives/problem_statements/README.md) for the full data feasibility assessment.

| # | Problem Statement | Priority | Status | Key Output |
|---|---|---|---|---|
| [PS-001](objectives/problem_statements/ps-001-healthcare-system-baseline.md) | Healthcare System Baseline — Workforce, Capacity & Utilisation | P0 | Initialized | Workforce baseline, facility baseline, admission rate baseline, system balance scorecard (staff-to-bed ratios vs WHO benchmarks) |
| [PS-002](objectives/problem_statements/ps-002-healthcare-demand-forecasting.md) | Healthcare Demand Forecasting — Disease Burden & Demographic Projections | P0 | Initialized | Cancer/stroke/IHD mortality forecasts (2020–2030); hospital admission volume projections by age group (2021–2035, 3 demographic scenarios) |
| [PS-003](objectives/problem_statements/ps-003-integrated-resource-planning.md) | Integrated Resource Planning & Budget Dashboard | P0 | Initialized | Workforce gap + annual hiring targets, bed gap + commissioning milestones, staff-facility alignment validation, workforce cost estimate, 6-tab HTML dashboard |

**Scope boundary**: The dataset supports workforce, beds, and admission-rate analysis at national aggregate, annual granularity. Occupancy rates, diagnosis-linked admissions, ICU/step-down splits, consumables, and expenditure by category are absent from the data and are excluded from all analyses.

**User Stories**

📁 **Location**: `docs/objectives/user_stories/`

Grouped by problem statement for traceability.

**How to Add New Problems**:
1. Create: `docs/objectives/problem_statements/ps-{num}-{slug}.md`
2. Follow template from [Data Analysis Best Practices](../.github/instructions/data-analysis-best-practices.instructions.md)
3. Update this index with link

---

### 3️⃣ Data Documentation

**Master Data Reference**

📁 **[Data Dictionary Index](data_dictionary/index.md)** - Complete data documentation hub

**Core Datasets**:
| Dataset | Description | Location |
|---------|-------------|----------|
| [Disease Data](data_dictionary/disease_data.md) | Disease surveillance & epidemiological data | `shared/data/1_raw/disease_surveillance/` |
| [Workforce Features](data_dictionary/workforce-forecast-features.md) | Healthcare workforce planning data | `shared/data/1_raw/workforce/` |
| [External Reference](data_dictionary/external_reference.md) | Demographics, benchmarks, reference data | `shared/data/2_external/` |

**Data Standards**:
- Dates: `YYYY-MM-DD` format, `Date` type (Polars)
- Categories: `Categorical` type for disease names, regions
- Counts: `Int32` for case counts, headcounts
- Rates: `Float32` for percentages, per-capita metrics

---

### 4️⃣ Methodology & Techniques

**Analytical Frameworks**

📁 **Location**: `docs/methodology/`

- Statistical methods for health trend analysis
- Time series forecasting approaches
- Data validation and quality frameworks
- *To be expanded as methodologies are developed*

---

### 5️⃣ Development Guidelines

**Coding Standards & Best Practices**

| Guideline | Purpose |
|-----------|---------|
| [Python Best Practices](../.github/instructions/python-best-practices.instructions.md) | Python coding standards, type hints, docstrings |
| [Data Analysis Best Practices](../.github/instructions/data-analysis-best-practices.instructions.md) | Analysis lifecycle from problem definition to deployment |
| [Folder Structure Guide](../.github/instructions/data-analysis-folder-structure.instructions.md) | Project organization and file placement |

**Key Conventions**:
- **Package Manager**: Use `uv` (NOT pip/conda)
- **Data Processing**: Polars (primary), Pandas (fallback)
- **Logging**: `loguru` (NOT `print()`)
- **Testing**: Minimum 80% code coverage with `pytest`

---

### 6️⃣ Multi-Agent Orchestration System

**Specialized Agents for Complex Workflows**

📁 **Configuration**: `.agents/`

| Agent | Responsibility | Stage |
|-------|---------------|-------|
| **ExtractionAgent** | Data extraction and loading | 0-2 |
| **ProfilingAgent** | Data quality assessment | 3 |
| **CleaningAgent** | Data cleaning and preprocessing | 4 |
| **EDAAgent** | Exploratory data analysis | 5 |
| **ModelingAgent** | Statistical modeling and forecasting | 7 |
| **VisualizationAgent** | Publication-quality visualizations | 9 |
| **QualityAgent** | Code quality and testing | 8, 10 |
| **DocumentationAgent** | Technical documentation | 9 |

**Handoff Protocol**: Agents communicate via JSON handoff files in `shared/data/3_interim/agent_handoffs/`

**Configuration Files**:
- [Agent Configuration](../.agents/config.yml) - Pipeline orchestration settings
- [Agent Registry](../.agents/registry.yml) - Agent capabilities and skill mappings

---

## 🏗️ Project Structure Overview

```
gen-e2/
├── shared/                          ♻️ SHARED INFRASTRUCTURE
│   ├── src/                         # Reusable production code
│   │   ├── data_processing/         # ETL, extraction, cleaning
│   │   ├── analysis/                # Statistical algorithms
│   │   ├── models/                  # Modeling utilities
│   │   ├── visualization/           # Plotting functions
│   │   └── orchestration/           # Multi-agent pipeline
│   ├── data/                        # Single source of truth
│   │   ├── 1_raw/                   # Original data (READ-ONLY)
│   │   ├── 2_external/              # Reference data
│   │   ├── 3_interim/               # Processing checkpoints
│   │   └── 4_processed/             # Analysis-ready datasets
│   ├── sql/                         # Database queries
│   ├── tests/                       # Unit & integration tests
│   └── config/                      # Shared configuration
│
├── problem-statements/              📦 SELF-CONTAINED ANALYSES
│   └── ps-{num}-{name}/             # Complete analysis package
│       ├── notebooks/               # Exploratory analysis
│       ├── src/                     # Problem-specific code
│       ├── data/                    # Problem outputs
│       ├── results/                 # Analysis results
│       ├── reports/                 # Visualizations, dashboards
│       └── config/                  # Problem configuration
│
├── docs/                            📚 DOCUMENTATION
│   ├── index.md                     # This file
│   ├── objectives/                  # Problem statements
│   ├── data_dictionary/             # Data documentation
│   ├── methodology/                 # Analytical methods
│   └── project_context/             # Business context
│
├── .agents/                         🤖 MULTI-AGENT SYSTEM
│   ├── config.yml                   # Orchestration settings
│   ├── registry.yml                 # Agent capabilities
│   ├── templates/                   # Prompt templates
│   └── skills/                      # Domain knowledge
│
└── logs/                            📋 APPLICATION LOGS
    ├── etl/                         # Data processing logs
    ├── errors/                      # Error logs
    └── audit/                       # Audit trails
```

**Key Principles**:
1. **Shared Code**: Write reusable functions in `shared/src/`, import in problem statements
2. **Data Isolation**: Raw data in `shared/data/1_raw/` (single source), processed in problem folders
3. **Self-Contained**: Each problem statement is a complete, shareable package

---

## 🎯 Project Phases & Roadmap

### Phase 0: Setup ✅ **COMPLETED**
- [x] Environment configuration (Python 3.9, uv package manager)
- [x] Virtual environment creation and activation
- [x] Dependencies installation (Polars, Databricks, testing frameworks)
- [x] Folder structure creation (hybrid shared + problem-statements)
- [x] Documentation setup (README, docs/index, data dictionary)
- [x] Configuration files (base.yml, databricks.yml, .env.example)

### Phase 1: Data Acquisition 🚧 **NEXT**
- [ ] Identify Singapore health datasets on Kaggle and other sources
- [ ] Create data extraction scripts in `shared/src/data_processing/extractors/`
- [ ] Download datasets using Kaggle connector (or alternative credential-free methods)
- [ ] Place raw data in `shared/data/1_raw/` with proper documentation
- [ ] Validate data integrity and completeness
- [ ] Update data dictionary with acquired datasets

### Phase 2: Data Profiling 📊
- [ ] Create data profiling scripts using Polars
- [ ] Assess data quality (completeness, accuracy, consistency, timeliness)
- [ ] Generate data quality reports in `logs/etl/data_quality/`
- [ ] Document known limitations and caveats in data dictionary
- [ ] Create data validation tests in `shared/tests/data/`
- [ ] Identify data quality issues requiring remediation

### Phase 3: Problem Discovery 🔍
- [ ] Conduct stakeholder workshops with policy makers and team heads
- [ ] Define concrete problem statements addressing health policy needs
- [ ] Create user stories grouped by problem in `docs/objectives/user_stories/`
- [ ] Prioritize analyses based on stakeholder impact and data availability
- [ ] Create problem statement folders: `problem-statements/ps-{num}-{name}/`
- [ ] Document expected outcomes and success criteria

### Phase 4: Exploratory Data Analysis 📈
- [ ] Create EDA notebooks in `problem-statements/ps-{num}/notebooks/1_exploratory/`
- [ ] Identify health trends, patterns, and anomalies
- [ ] Perform statistical analysis and hypothesis testing
- [ ] Generate summary statistics and initial visualizations
- [ ] Document findings and insights in notebooks
- [ ] Refactor reusable code to `shared/src/`

### Phase 5: Statistical Modeling 🔬
- [ ] Develop predictive models and forecasting algorithms
- [ ] Perform feature engineering in `notebooks/3_feature_engineering/`
- [ ] Train and validate models, save to `ps-{num}/models/`
- [ ] Evaluate model performance with appropriate metrics
- [ ] Document modeling methodology in `docs/methodology/`
- [ ] Create model evaluation reports

### Phase 6: Visualization & Reporting 📊
- [ ] Create publication-quality visualizations
- [ ] Build interactive dashboards using Plotly/Altair
- [ ] Generate reports for stakeholders in `ps-{num}/reports/`
- [ ] Create executive summaries highlighting key findings
- [ ] Develop presentations for policy makers
- [ ] Export analysis results to stakeholder-ready formats

### Phase 7: Deployment & Automation 🚀
- [ ] Deploy pipelines to HEALIX/Databricks platform
- [ ] Automate ETL workflows with scheduled jobs
- [ ] Set up monitoring and alerting for data quality
- [ ] Create CI/CD pipelines in `.github/workflows/`
- [ ] Document deployment procedures and runbooks
- [ ] Establish maintenance and update procedures

### Phase 8: Ongoing Maintenance 🔄
- [ ] Monitor data quality and pipeline health
- [ ] Update models and analyses as new data arrives
- [ ] Respond to stakeholder feedback and new requirements
- [ ] Maintain documentation and keep it current
- [ ] Conduct periodic reviews and retrospectives
- [ ] Archive completed problem statements

---

## 🔧 Key Resources

### Development
- **Virtual Environment**: `.venv/` (activated via `source .venv/bin/activate`)
- **Dependencies**: `requirements.txt` (install via `uv pip install -r requirements.txt`)
- **Configuration**: `.env` (copy from `.env.example`)
- **Tests**: Run with `pytest` (target: >80% coverage)

### Data Locations
- **Raw Data**: `shared/data/1_raw/` (immutable, never modify)
- **External Reference**: `shared/data/2_external/` (demographics, benchmarks)
- **Interim Data**: `shared/data/3_interim/` (intermediate processing)
- **Processed Data**: `shared/data/4_processed/` (analysis-ready)

### Code Organization
- **Shared Code**: `shared/src/` (reusable across all analyses)
- **Problem-Specific**: `problem-statement/ps-{num}-{slug}/` (self-contained)
- **Tests**: `shared/tests/` and `problem-statements/*/tests/`
- **Scripts**: `scripts/shared/` (automation and utilities)

## 📖 Documentation Types

### 📝 Problem Statements
Define what we're trying to solve:
- **What**: Clear problem definition
- **Why**: Business value and stakeholder needs  
- **Success**: Measurable criteria and KPIs

### 👥 User Stories
Capture stakeholder perspectives:
- **As a** [role]
- **I want** [capability]
- **So that** [benefit]

### 📊 Data Dictionary
Document all datasets:
- Field definitions and data types
- Value ranges and constraints
- Data quality notes
- Lineage and refresh frequency

### 🔬 Methodology  
Explain analytical approaches:
- Statistical methods used
- Assumptions and limitations
- Validation procedures
- References and citations

## 🤝 Contributing to Documentation

### Adding Documentation

1. **Problem Statement**: Create in `objectives/problem_statements/ps-{num}-{slug}.md`
2. **User Story**: Create in `objectives/user_stories/ps-{num}/`
3. **Data Dictionary**: Create in `data_dictionary/{dataset}.md` and update index
4. **Methodology**: Create in `methodology/{method}.md`

### Documentation Standards

- Use **Markdown** formatting
- Include **table of contents** for long documents
- Add **metadata** (author, date, version)
- Use **clear headings** and structure
- Include **examples** where helpful
- Link to **related documents**
- Keep **up to date** with code changes

## 🔍 Finding Information

### By Topic
- **Business context**: `project_context/` folder
- **Data details**: `data_dictionary/` folder
- **Analysis methods**: `methodology/` folder
- **Specific problems**: `objectives/problem_statements/`

### By Phase
- **Planning**: Problem statements and user stories
- **Development**: Tech stack and coding guidelines
- **Analysis**: Methodology and data dictionary
- **Deployment**: Business objectives and tech stack

### By Stakeholder
- **Policy Makers**: Business objectives, problem statements
- **Analysts**: Methodology, data dictionary, coding guidelines
- **Engineers**: Tech stack, folder structure, development guidelines
- **Leadership**: Business objectives, executive summaries in reports

## 📚 External References

### MOH Resources
- [MOH Website](https://www.moh.gov.sg/)
- [Healthcare Statistics](https://www.moh.gov.sg/resources-statistics)

### Technical Documentation
- [Polars Documentation](https://pola-rs.github.io/polars/)
- [Databricks Documentation](https://docs.databricks.com/)
- [Kaggle API Documentation](https://www.kaggle.com/docs/api)

### Best Practices
- [Python Best Practices](../.github/instructions/python-best-practices.instructions.md)
- [Data Analysis Lifecycle](../.github/instructions/data-analysis-best-practices.instructions.md)

## ✅ Next Steps

1. **Review project context** to understand business objectives
2. **Check TODO.md** for current priorities
3. **Read tech stack documentation** to understand tools
4. **Explore problem statements** to see defined analyses
5. **Review data dictionary** to understand available data

## 📞 Getting Help

- **Questions about data**: Check data dictionary or data-sources.md
- **Technical issues**: Review tech-stack.md and coding guidelines
- **Business context**: See business-objectives.md
- **Specific tasks**: Check TODO.md for status and assignments

---

**Last Updated**: March 11, 2026  
**Maintainer**: Gen-E2 Team  
**Version**: 1.0.0
