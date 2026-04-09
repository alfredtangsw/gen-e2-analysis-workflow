# Agentic AI Project Template

A domain-agnostic, modular template for building multi-agent AI pipelines in GitHub Copilot Chat.
Extracted from the `gen-e2-analysis-workflow` design patterns.

---

## Core Architecture

```
Planning (Prompts 0–3)  →  Execution (executor.agent.md + subagents)
```

### Planning Phase (run once, in order)
```
/0-init-project               Sets up structure, env, tooling
       ↓
/1-identify-problems          Breaks domain into solvable problem statements
       ↓
/2-generate-tasks             Decomposes each problem into sprint-ready tasks
       ↓
/3-generate-implementation-plan   Appends executable plans to each task file
```

### Execution Phase (per problem)
```
executor.agent.md
    ├── Phase 1:  {first-agent}                      → code-quality ✓
    ├── Phase 2:  {phase-2a-agent} ∥ {phase-2b-agent} → code-quality ✓ (x2)
    ├── Phase N:  {final-agent}                       → code-quality ✓
    └── Phase QA: code-simplifier → code-reviewer
```

---

## File Index

### Prompts
| File | Purpose |
|------|---------|
| `prompts/0-init-project.prompt.md` | Project structure, env, context docs |
| `prompts/1-identify-problems.prompt.md` | Surface and prioritize problem statements |
| `prompts/2-generate-tasks.prompt.md` | Decompose problems into user stories |
| `prompts/3-generate-implementation-plan.prompt.md` | Append executable plans to stories |

### Agents
| File | Purpose |
|------|---------|
| `agents/executor.agent.md` | Orchestrator — spawns all subagents, never does domain work |
| `agents/specialist-agent.agent.md` | Template for any domain-specific phase agent |
| `agents/code-quality.agent.md` | Reusable gate — verifies every agent's outputs |
| `agents/code-reviewer.agent.md` | Final quality gate — executes and reviews all code |
| `agents/code-simplifier.agent.md` | Pre-review cleanup — improves clarity without changing behavior |

---

## How to Use

1. Copy this folder into your new project's `.github/` directory
2. Replace all `{PLACEHOLDER}` values with your domain-specific content
3. Populate `docs/project-context/` with your three context documents
4. Run prompts 0 → 3 in Copilot Chat with the context docs attached
5. Run the executor agent per problem: `#executor.agent.md {task-id}`

---

## Key Design Principles

| Principle | What it means |
|-----------|---------------|
| **Plans ≠ Execution** | Prompts produce artifacts; executor consumes them |
| **Blackboard communication** | Agents share state via files only — no inline data passing |
| **Verify before advancing** | `code-quality` runs after every phase, not just at the end |
| **Single responsibility** | Each agent owns exactly one phase |
| **Fork-join parallelism** | Independent phases run simultaneously; dependent ones run sequentially |
| **Immutable source data** | Inputs are never modified; all transforms write to new paths |
| **Context co-location** | Implementation plans live inside the task/story files they describe |
