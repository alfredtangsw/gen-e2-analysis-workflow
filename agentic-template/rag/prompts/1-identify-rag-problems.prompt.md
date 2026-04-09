---
description: Identify RAG Problem Statements from Project Context
model: claude-sonnet-4.5
---

# Identify RAG Problem Statements

## Role

You are an expert information retrieval architect and business analyst. Your job is to surface concrete, solvable RAG use cases from project context — constrained by what documents are actually available and what retrieval quality is measurable.

## Objective

Analyze project context to identify **viable RAG problem statements** that:
1. Have a clearly defined corpus (documents that exist and are accessible)
2. Have natural language questions that users actually need to ask
3. Can be evaluated empirically (a ground-truth eval set can be constructed)
4. Produce measurable, demonstrable quality improvements over keyword search

---

## Instructions

### Step 1: Read All Context

Read all three static context documents before forming any opinions:

1. `docs/project-context/business-objectives.md` — what decisions or workflows this RAG system will support
2. `docs/project-context/document-corpus.md` — what documents are available, their formats, access methods, known quality issues
3. `docs/project-context/rag-stack.md` — approved embedding models, vector stores, LLMs, and performance constraints

---

### Step 2: RAG-Specific Feasibility Checks

For each candidate problem, confirm ALL of the following before including it:

#### Corpus Readiness
- [ ] Source documents are listed in `document-corpus.md` and are accessible right now (not "planned")
- [ ] Documents are in a parseable format (PDF, HTML, DOCX, plain text — not scanned images without OCR)
- [ ] Total corpus size is within compute constraints from `rag-stack.md`
- [ ] Licensing permits indexing and retrieval (no DRM or redistribution restrictions)
- [ ] At least 80% of documents have usable text content (not mostly tables, charts, or images)

#### Question Coverage
- [ ] At least 20 distinct natural language questions can be formulated that: (a) have definitive answers, (b) require reading the corpus to answer, and (c) cannot be answered by general LLM knowledge alone
- [ ] Questions are spread across multiple documents (not all answerable from one source)
- [ ] Questions span at least 2–3 distinct topics within the corpus

#### Eval Set Constructability
- [ ] A ground-truth QA eval set of ≥ 50 pairs can be built from the corpus before indexing begins
- [ ] Each QA pair can be traced to specific source document(s) with verifiable answers
- [ ] Eval set covers easy, medium, and hard questions (mix of factual, comparative, temporal)

#### Measurability
- [ ] Success can be defined as: "Precision@5 ≥ X and faithfulness ≥ Y" (not "users find it useful")
- [ ] A baseline exists or can be created (keyword search, existing tool, or human lookup)

**Reject** any problem that fails these checks. A RAG system over an unmeasurable use case cannot be validated.

---

### Step 3: Score and Prioritize

Rate each candidate on five dimensions (1–5 each):

| Dimension | What it measures |
|-----------|-----------------|
| **Business impact** | How directly does this support a stated objective? |
| **Corpus readiness** | How accessible, clean, and well-structured are the documents? |
| **Question specificity** | How well-defined and bounded are the questions users need to ask? |
| **Eval set feasibility** | How easy is it to build a high-quality ground-truth eval set? |
| **Differentiation** | How much better is RAG than keyword search or existing tools for this use case? |

Surface highest total-score problems first. Aim for 2–4 RAG problem statements.

---

### Step 4: Write Problem Statement Files

For each approved RAG problem, create `docs/objectives/problem_statements/ps-{num}-{name}.md`:

```markdown
# PS-{num}: {Problem Title}

## Business Objective
[What workflow, decision, or question-answering task does this RAG system enable? 1–2 sentences.]

## Problem Statement
[What is currently hard to find or answer, what the RAG system will do, and why retrieval-augmented generation is the right approach over keyword search or fine-tuning. 2–4 sentences.]

## RAG System Scope

### Corpus
| Source | Format | Volume | Access | Update Frequency |
|--------|--------|--------|--------|-----------------|
| {source name} | {format} | {N docs / N MB} | {path/API} | {static/weekly} |

### Target Questions (sample)
Provide 5–10 example questions that the system must be able to answer:
1. {example question}
2. {example question}
...

### Out of Scope
- {questions the system should NOT attempt to answer}
- {document types not included in the corpus}

## Success Criteria

### Retrieval Quality (must pass before generation evaluation)
- [ ] Precision@5 ≥ {0.75} on eval set
- [ ] Recall@5 ≥ {0.70} on eval set
- [ ] MRR ≥ {0.65} on eval set

### Generation Quality
- [ ] RAGAS Faithfulness ≥ {0.80}
- [ ] RAGAS Answer Relevancy ≥ {0.75}

### Performance
- [ ] p95 query latency ≤ {3s}

### Eval Set Requirement
- [ ] Ground-truth QA eval set of ≥ {50} pairs created before indexing

## Stakeholders
| Role | Need |
|------|------|
| {role} | {what they need to be able to ask or find} |

## Chunking & Retrieval Considerations
- Recommended chunk strategy: {recursive-character / semantic / sentence} because {reason}
- Special handling needed: {e.g., "tables in PDFs must be kept as single chunks"}
- Metadata fields critical for filtered retrieval: {e.g., date, document_type}

## Assumptions & Constraints
- {assumption 1}
- {assumption 2}

## Priority Score
| Dimension | Score (1–5) |
|-----------|-------------|
| Business impact | |
| Corpus readiness | |
| Question specificity | |
| Eval set feasibility | |
| Differentiation from keyword search | |
| **Total** | **/25** |
```

---

### Step 5: Flag Eval Set Creation as Blocked Work

For every approved problem statement, add a task to `TODO.md`:

```markdown
## {PS-num}: {Problem Name}
- [ ] Build ground-truth QA eval set (≥50 pairs) → save to {output-dir}/{task-id}/evaluation/qa_pairs.json
      Schema: agentic-template/rag/evaluation/qa-pairs-schema.json
      ⚠️ PIPELINE IS BLOCKED until this is complete
```

This task is human work — it cannot be automated. The pipeline executor will halt at startup if the eval set is missing.

---

### Step 6: Create Prioritization Summary

Write `docs/objectives/problem_statements/PRIORITIZATION.md` with:
- Ranked list of all approved RAG problems (highest score first)
- One-line justification for each
- Rejected candidates with reason (corpus not accessible, eval set unconstructable, etc.)
- Total estimated eval set creation effort (person-hours) across all approved problems
