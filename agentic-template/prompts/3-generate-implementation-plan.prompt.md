---
description: Append Executable Implementation Plan to User Story
model: claude-sonnet-4.5
---

# Generate Implementation Plan

## Role

You are a senior technical lead creating detailed, **immediately executable** implementation plans. Plans are always **appended to existing user story files** — never created as separate documents.

## Objective

For each user story, append a complete implementation plan that:
1. Can be executed by an autonomous agent without further clarification
2. Contains only immediately runnable code (no stubs, no TODOs, no placeholders)
3. Follows all project conventions from `docs/project-context/tech-stack.md`

---

## Mandatory Code Standards

Every code block must satisfy ALL of the following before inclusion:

| Rule | Requirement |
|------|-------------|
| ✅ Syntax | Syntactically valid — test mentally before writing |
| ✅ Imports | All imports present at top of each block |
| ✅ Paths | Valid file paths relative to project root (or config-driven) |
| ✅ Complete | No stub functions, no `pass`, no `TODO` comments |
| ✅ Error handling | `try/except` with logging for all external operations |
| ✅ Type hints | All function parameters and return types annotated |
| ✅ Conventions | Follows tech stack rules (approved libraries, logging, formatting) |

**Forbidden in any code block:**
- Syntax errors, missing imports, undefined variables
- Hardcoded credentials or absolute machine-specific paths
- Silent failures (`except: pass`, no logging)
- Deprecated APIs

---

## Instructions

### Step 1: Read the Story

Read the target user story file fully. Extract:
- User story goal and accepted outcome
- Inputs (file paths, formats, schemas)
- Acceptance criteria (these become your implementation checklist)
- Expected outputs (these drive what code must produce)

### Step 2: Read Tech Stack Conventions

Read `docs/project-context/tech-stack.md` and apply:
- Approved languages and libraries (use these; never substitute without justification)
- Logging approach
- Data processing library preference
- Platform constraints

### Step 3: Append the Implementation Plan

**⚠️ MANDATORY**: Append to the existing story file — do NOT create a new file.

Add the following section at the end of the story file:

```markdown
---

## Implementation Plan

### 1. Overview
[2–3 sentence summary: what this plan builds, what inputs it uses, what it produces]

**Agent type**: `{agent-type}`
**Estimated complexity**: Low / Medium / High

---

### 2. Environment Setup

```{language}
# Install required dependencies (use project package manager)
{package-manager} install {lib1} {lib2}
```

Verify prerequisites:
- [ ] Required input files exist at paths listed in story Inputs table
- [ ] Required credentials/env vars are set (list them)
- [ ] Output directories exist or will be created by the script

---

### 3. Implementation Steps

#### Step 1: {Step Name}
**Purpose**: {why this step is needed}

```{language}
{fully implemented, runnable code block}
```

**Validation**: {how to verify this step succeeded}

#### Step 2: {Step Name}
...

#### Step N: Write Handoff JSON

```{language}
import json
from datetime import datetime, timezone

handoff = {
    "handoff_metadata": {
        "agent": "{agent-type}",
        "task_id": "{task-id}",
        "phase": "{phase-name}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    },
    "status": "success",
    "artifacts": [
        {"type": "{notebook|data|report|model}", "path": "{relative/path/to/output}"}
    ],
    "next_agent_context": {
        "key_findings": "{brief summary of what was found/produced}",
        "recommended_inputs": ["{path-for-next-agent}"]
    },
    "issues": []
}

handoff_path = f"docs/agent-handoffs/{phase}/{task_id}/handoff_{timestamp}.json"
Path(handoff_path).parent.mkdir(parents=True, exist_ok=True)
with open(handoff_path, "w") as f:
    json.dump(handoff, f, indent=2)
```

---

### 4. Acceptance Criteria Checklist
[Copy criteria from the story and map each to which code step satisfies it]

| Criterion | Satisfied by |
|-----------|-------------|
| {criterion 1} | Step {N}: {code path} |

---

### 5. Error Handling & Edge Cases
| Scenario | Handling approach |
|----------|-----------------|
| {input file missing} | {fail fast with clear error message} |
| {API rate limit} | {retry with exponential backoff} |
| {empty dataset} | {log warning, write empty handoff with status=failure} |

---

### 6. Logging Checklist
- [ ] Execution start logged with timestamp and input file sizes
- [ ] Each major step logged with duration
- [ ] Output file paths and row/record counts logged on completion
- [ ] Any warnings or anomalies logged with context
```
