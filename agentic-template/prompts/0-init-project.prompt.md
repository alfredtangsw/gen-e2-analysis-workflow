---
description: Agentic Project Initialization
model: claude-sonnet-4.5
---

# Project Initialization

Ask the following questions before doing anything:

## Questions to Ask

1. **Project Objectives**
   - What specific decision or outcome will this project drive? What happens if we don't do it?
   - How will we measure success? What does "good enough" look like?

2. **Domain & Stakeholders**
   - What domain is this project in? (e.g., data analysis, content pipeline, software generation)
   - Who are the key stakeholders and what are their expectations?
   - What pain points or open questions have stakeholders raised?

3. **Technical Environment**
   - Target platform/runtime? (cloud, local, specific service)
   - Expected volume of inputs/outputs?
   - Any approved tools, libraries, APIs, or hard constraints?

4. **Pipeline Design**
   - How many distinct phases does the pipeline need?
   - Which phases are independent enough to run in parallel?
   - What does the final deliverable look like? (dashboard, report, API, code, model, etc.)

---

## Actions Based on Answers

### 1. Create Project Structure

```
.
├── .env.example                    # Credential/config template — never commit real values
├── .gitignore
├── README.md
├── requirements.txt                # Or package.json, go.mod, etc.
│
├── docs/
│   ├── project-context/            # Static context — attach to EVERY Copilot Chat session
│   │   ├── business-objectives.md  # Goals, stakeholders, KPIs, success criteria
│   │   ├── data-sources.md         # Available inputs, schemas, access methods
│   │   └── tech-stack.md           # Approved tools, platforms, constraints
│   │
│   ├── objectives/
│   │   ├── problem_statements/     # Output of Prompt 1: ps-{num}-{name}.md
│   │   └── user_stories/           # Output of Prompts 2+3: per-problem story files
│   │
│   └── agent-handoffs/             # Runtime communication between agents
│       └── {phase}/
│           └── {task-id}/
│               └── handoff_{timestamp}.json
│
├── shared/                         # Shared infrastructure (write once, use everywhere)
│   ├── src/                        # Reusable code modules
│   └── data/
│       └── 1_raw/                  # IMMUTABLE source data — never modify in place
│
└── {output-dir}/                   # Per-task self-contained output packages
    └── {task-id}/
        ├── src/
        ├── data/
        │   ├── interim/
        │   └── processed/
        ├── results/
        │   ├── tables/
        │   └── metrics/
        ├── reports/
        │   └── figures/
        ├── models/
        ├── config/
        ├── tests/
        └── logs/
```

### 2. Populate Context Documents

Create the three static context files. These are the agent's "world model" — read-only and attached to every session:

- `docs/project-context/business-objectives.md` — strategic goals, KPIs, stakeholders, success criteria
- `docs/project-context/data-sources.md` — available inputs, schemas, access methods, known limitations
- `docs/project-context/tech-stack.md` — approved platforms, languages, libraries, constraints

### 3. Setup Development Environment

- Create and activate a virtual environment appropriate for the tech stack
- Install base dependencies; lock versions
- Populate `.env.example` with all credential and config key names (placeholder values only)
- Verify credentials work before any downstream work depends on them
- Initialize Git repository with an initial commit

### 4. Create TODO.md

Break the project into small (2–4 hour) tasks organized by domain area:

```markdown
## {Domain Area}
- [ ] Task description (owner)
```

Cover: infrastructure, data pipeline, analysis/modeling, visualization, testing, DevOps, security, documentation review.

### 5. Configure Code Quality

Set up linting, formatting, and testing frameworks for the chosen tech stack. Document commands in README.md:

```bash
# Example for Python
ruff check .         # lint
ruff format .        # format
pytest tests/        # run tests
```

---

## Final Checks

- [ ] All three context documents exist and are populated
- [ ] Folder structure matches the hybrid layout above
- [ ] `.env.example` lists all required variables
- [ ] `.gitignore` excludes venv, secrets, large data files, build artifacts
- [ ] `requirements.txt` (or equivalent) is committed with pinned versions
- [ ] README.md explains project purpose, setup steps, and workflow
- [ ] Git repo initialized with initial commit
