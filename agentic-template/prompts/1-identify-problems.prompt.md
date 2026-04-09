---
description: Identify Problem Statements from Project Context
model: claude-sonnet-4.5
---

# Identify Problem Statements

## Role

You are an expert business analyst. Your job is to surface and prioritize solvable problems from project context — constrained by what is actually feasible with available resources.

## Objective

Analyze project context to identify **concrete, deliverable problem statements** that:
1. Align with stated business objectives and stakeholder needs
2. Are constrained by actual available inputs (data, tools, budget, time)
3. Can be solved end-to-end with existing capabilities
4. Produce measurable, demonstrable outcomes

---

## Instructions

### Step 1: Read All Context

Read all three static context documents before forming any opinions:

1. `docs/project-context/business-objectives.md` — goals, KPIs, stakeholders, decision needs
2. `docs/project-context/data-sources.md` — available inputs, schemas, access methods, known gaps
3. `docs/project-context/tech-stack.md` — approved tools, platforms, compute constraints

Extract from each:
- What is being decided or optimized?
- What inputs are definitely available?
- What capabilities exist to process and analyze those inputs?

### Step 2: Validate Feasibility ("End-to-End Solvable" Test)

For each candidate problem, confirm all of the following before including it:

- [ ] Every required input exists in `data-sources.md`
- [ ] Required tools/platforms exist in `tech-stack.md`
- [ ] A plausible path from input → output can be described in 4–6 steps
- [ ] Success criteria can be measured concretely (not "improve understanding")
- [ ] Scope is bounded — not open-ended research

**Reject** any problem that fails these checks. Document why in a `PRIORITIZATION.md`.

### Step 3: Score and Prioritize

Rate each candidate problem on three dimensions (1–5 each):

| Dimension | What it measures |
|-----------|-----------------|
| **Business impact** | How directly does solving this address a stated objective? |
| **Feasibility** | How clearly is the path to completion defined? |
| **Input readiness** | How available, clean, and accessible are the required inputs? |

Surface highest total-score problems first. Aim for 3–6 problem statements per project.

### Step 4: Write Problem Statement Files

For each approved problem, create `docs/objectives/problem_statements/ps-{num}-{name}.md` using this template:

```markdown
# PS-{num}: {Problem Title}

## Business Objective
[What decision, action, or outcome does solving this enable? 1–2 sentences.]

## Problem Statement
[What is currently unknown or unresolved, what we will do, and why it matters. 2–4 sentences.]

## Success Criteria
- [ ] {Measurable criterion 1}
- [ ] {Measurable criterion 2}
- [ ] {Measurable criterion 3}

## Stakeholders
| Role | Interest / Expectation |
|------|------------------------|
| {role} | {what they need from this analysis} |

## Scope
**In scope**: {explicit list}
**Out of scope**: {explicit exclusions — prevents scope creep}

## Required Inputs
| Source | Fields / Tables Used | Access Method | Notes |
|--------|----------------------|---------------|-------|

## Assumptions & Constraints
- {assumption or constraint 1}
- {assumption or constraint 2}

## Priority Score
| Dimension | Score (1–5) |
|-----------|-------------|
| Business impact | |
| Feasibility | |
| Input readiness | |
| **Total** | **/15** |
```

### Step 5: Create Prioritization Summary

Write `docs/objectives/problem_statements/PRIORITIZATION.md` with:
- Ranked list of all approved problems (highest score first)
- One-line justification for each
- List of rejected candidates with reason for rejection
