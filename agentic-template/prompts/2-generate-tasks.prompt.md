---
description: Generate User Stories (Tasks) from Problem Statements
model: claude-sonnet-4.5
---

# Generate User Stories from Problem Statements

## Role

You are a senior technical lead. Your job is to decompose every problem statement into sprint-ready user stories that an autonomous agent can execute — each story self-contained, testable, and unambiguous.

## Objective

Decompose **all** problem statements into sequenced user stories that:
1. Map to a concrete pipeline phase (extraction, cleaning, analysis, modeling, delivery)
2. Have clear, verifiable acceptance criteria
3. Specify exact inputs and expected outputs
4. Can be assigned to a single specialist agent

**Process every file in `docs/objectives/problem_statements/` — do not skip any.**

---

## Instructions

### Step 1: Read Context

1. Read all problem statement files in `docs/objectives/problem_statements/`
2. Read `docs/project-context/data-sources.md` and `docs/project-context/tech-stack.md`
3. Extract: objectives, required inputs, expected outputs, success criteria, constraints

### Step 2: Map Problems to Pipeline Phases

Every problem follows this standard phase sequence. Identify which phases apply:

| Phase | Typical Story | Agent Type |
|-------|--------------|------------|
| 1 — Extraction | Acquire raw inputs from source systems | `{extractor}` |
| 2A — Validation | Profile quality, flag anomalies, document findings | `{validator}` |
| 2B — Cleaning | Resolve quality issues, standardize, transform | `{cleaner}` |
| 3A — Analysis | Explore patterns, trends, relationships | `{analyst}` |
| 3B — Engineering | Build features or intermediate artifacts | `{engineer}` |
| 4 — Modeling / Core | Build the primary deliverable | `{specialist}` |
| 5 — Delivery | Package output for stakeholders | `{delivery}` |

Phases 2A+2B and 3A+3B can run in parallel. All other phases are sequential.

### Step 3: Write User Stories

For each problem statement, create a folder:
`docs/objectives/user_stories/problem-statement-{num}-{name}/`

Write one file per story: `{phase-num}-{story-slug}.md`

**Story file template:**

```markdown
# Story {phase-num}: {Short Story Title}

## User Story
As a {role}, I want to {action}, so that {outcome}.

## Context
- **Problem Statement**: PS-{num} `docs/objectives/problem_statements/ps-{num}-{name}.md`
- **Phase**: {phase name and number}
- **Depends on**: Story {prior-phase-num} (or "none" for Phase 1)
- **Enables**: Story {next-phase-num}

## Inputs
| Input | Path | Format |
|-------|------|--------|
| {input name} | `{path}` | {CSV / Parquet / JSON / etc.} |

## Acceptance Criteria
- [ ] {Criterion 1 — specific and verifiable}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

## Expected Outputs
| Output | Path | Format | Description |
|--------|------|--------|-------------|
| {output name} | `{output-dir}/{task-id}/{subfolder}/` | {format} | {what it contains} |
| Handoff JSON | `docs/agent-handoffs/{phase}/{task-id}/handoff_{timestamp}.json` | JSON | Agent completion signal |

## Non-Functional Requirements
- Performance: {any time/size constraints}
- Quality: {minimum quality bar}
- Logging: {what must be logged}

## Notes / Assumptions
- {any domain-specific notes the agent needs}
```

### Step 4: Create Story Index

Write `docs/objectives/user_stories/problem-statement-{num}-{name}/index.md`:

```markdown
# Story Index: PS-{num} {Problem Name}

## Execution Order

```
Story 01 (Extraction)
    ↓
Story 02A (Validation) ∥ Story 02B (Cleaning)
    ↓
Story 03A (Analysis) ∥ Story 03B (Engineering)
    ↓
Story 04 (Core Deliverable)
    ↓
Story 05 (Delivery / Packaging)
```

## Stories
| # | Title | Phase | Depends On | Agent |
|---|-------|-------|------------|-------|
```
